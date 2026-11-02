import datetime
import json
from unittest import mock

import pytest
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from aktionen.models import Aktion
from community.models import Community
from core.all_messages import all_messages
from family.models import Family
from home.models import Benachrichtigung
from personals import views
from personals.models import IOSDevice, TreeCodes, UserErweitert
from personals.tokens import email_verification_token
from tests.conftest import flash


@pytest.fixture(autouse=True)
def social_apps(db):
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site

    app = SocialApp.objects.create(provider="google", name="google", client_id="id", secret="s")
    app.sites.add(Site.objects.get_current())


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


def msg(key):
    return str(all_messages[key])


# ---- login / logout ------------------------------------------------------------------------------


def test_login_page(client, db):
    response = client.get("/personals/login/?next=/foo/")
    assert response.status_code == 200
    assert response.context["next"] == "/foo/"


def test_login_success_and_failure(client, user):
    response = client.post("/personals/login/", {"username": "alice", "password": "pw12345!"})
    assert response.url == "/dashboard/"
    assert "logged-in" in flash(response)
    client.logout()
    response = client.post("/personals/login/", {"username": "alice", "password": "wrong"})
    assert response.url == "/personals/login/"
    assert flash(response) == [msg("invalid_login_data")]


@pytest.mark.parametrize(
    "next_url, expected",
    [
        ("/users/overview/", "/users/overview/"),
        ("https://evil.example/phish", "/dashboard/"),
        ("//evil.example/phish", "/dashboard/"),
        ("javascript:alert(1)", "/dashboard/"),
        ("", "/dashboard/"),
    ],
)
def test_login_next_is_validated(client, user, next_url, expected):
    response = client.post("/personals/login/", {"username": "alice", "password": "pw12345!", "next": next_url})
    assert response.url == expected


def test_login_next_from_query_string(client, user):
    response = client.post("/personals/login/?next=/users/overview/", {"username": "alice", "password": "pw12345!"})
    assert response.url == "/users/overview/"


def test_logout(logged_in):
    response = logged_in.get("/personals/logout/")
    assert response.url == "/"
    assert "_auth_user_id" not in logged_in.session


# ---- registration ----------------------------------------------------------------------------------


def register_data(**overrides):
    data = {
        "recaptchaToken": "tok",
        "username": "newbie",
        "password": "secret123",
        "email": "",
        "nutzungsbedingungen_accepted": "on",
        "datenschutz_accepted": "on",
    }
    data.update(overrides)
    return data


@pytest.fixture
def recaptcha_ok():
    with mock.patch("personals.views.recaptcha_passed", return_value=True) as patched:
        yield patched


def test_register_page(client, db):
    assert client.get("/personals/register/").status_code == 200


def test_register_without_email(client, worldwide, recaptcha_ok):
    response = client.post("/personals/register/", register_data())
    assert response.url == "/dashboard/"
    user = User.objects.get(username="newbie")
    assert user.usererweitert.mail_verified is True
    assert user.usererweitert.lang == "de"
    assert worldwide.members.filter(id=user.id).exists()
    assert "_auth_user_id" in client.session
    assert msg("successfully_signed_up") in flash(response)


def test_register_with_email_sends_activation_mail(en_client, worldwide, recaptcha_ok):
    response = en_client.post("/personals/register/", register_data(email="n@x.de"))
    assert response.url == "/dashboard/"
    user = User.objects.get(username="newbie")
    assert (user.usererweitert.mail_verified, user.usererweitert.lang) == (False, "en")
    assert len(mail.outbox) == 1
    assert "/personals/activate/" in mail.outbox[0].body
    assert "Please click" in mail.outbox[0].body or "Bitte klick" in mail.outbox[0].body


def test_register_activation_mail_text_is_interpolated_after_translation(client, worldwide, recaptcha_ok):
    client.post("/personals/register/", register_data(email="n@x.de"))
    assert "%(activation_link)s" not in mail.outbox[0].body


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"nutzungsbedingungen_accepted": ""}, "nutzungsbedingungen_not_accepted"),
        ({"datenschutz_accepted": ""}, "datenschutz_not_accepted"),
        ({"username": ""}, "missing_required_inputs"),
        ({"password": ""}, "missing_required_inputs"),
        ({"username": "u" * 151}, "too_long_input"),
        ({"username": "alice"}, "username_not_available"),
        ({"email": "not-an-email"}, "invalid_email"),
        ({"email": "taken@x.de"}, "email_not_available"),
    ],
)
def test_register_validation(client, user, recaptcha_ok, overrides, key):
    User.objects.filter(username="alice").update(email="taken@x.de")
    response = client.post("/personals/register/", register_data(**overrides))
    assert response.url == "/personals/register/"
    assert flash(response) == [msg(key)]
    assert not User.objects.filter(username="newbie").exists()


def test_register_requires_recaptcha(client, worldwide):
    response = client.post("/personals/register/", register_data(recaptchaToken=""))
    assert flash(response) == [msg("recaptcha_token_missing")]
    with mock.patch("personals.views.recaptcha_passed", return_value=False):
        response = client.post("/personals/register/", register_data())
    assert flash(response)[-1] == msg("robot")


def test_recaptcha_passed(settings):
    settings.RECAPTCHA_PRIVATE_KEY = "secret"
    reply = mock.Mock()
    with mock.patch("personals.views.requests.post", return_value=reply) as post:
        reply.json.return_value = {"success": True, "score": 0.9}
        assert views.recaptcha_passed("t") is True
        assert post.call_args.kwargs["timeout"] == views.RECAPTCHA_TIMEOUT_SECONDS
        assert post.call_args.kwargs["data"] == {"secret": "secret", "response": "t"}
        reply.json.return_value = {"success": True, "score": 0.1}
        assert views.recaptcha_passed("t") is False
        reply.json.return_value = {"success": False}
        assert views.recaptcha_passed("t") is False
        reply.json.side_effect = ValueError
        assert views.recaptcha_passed("t") is False
    with mock.patch("personals.views.requests.post", side_effect=requests.ConnectionError):
        assert views.recaptcha_passed("t") is False


def test_register_without_worldwide_family_still_creates_profile(client, db, recaptcha_ok):
    client.post("/personals/register/", register_data())
    assert UserErweitert.objects.filter(user__username="newbie").exists()


# ---- email verification ---------------------------------------------------------------------------


def activation_url(user, token=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"/personals/activate/{uid}/{token or email_verification_token.make_token(user)}/"


def test_activate(client, user):
    response = client.get(activation_url(user))
    assert response.url == "/dashboard/"
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.mail_verified is True
    assert flash(response) == [msg("email_verified")]


@pytest.mark.parametrize("uid, token", [("!!!", "x"), ("MTAwMDA", "x"), ("YWJj", "x"), ("", "")])
def test_activate_invalid_links(client, user, uid, token):
    response = client.get(f"/personals/activate/{uid or 'x'}/{token or 'x'}/")
    assert flash(response) == [msg("invalid_verification_link")]
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.mail_verified is False


def test_activate_wrong_token(client, user):
    response = client.get(activation_url(user, "bad-token"))
    assert flash(response) == [msg("invalid_verification_link")]


def test_resend_verification_email(logged_in, user):
    response = logged_in.get("/personals/resend_verification_email/")
    assert flash(response) == [msg("no_email_to_verify")]
    user.email = "a@x.de"
    user.save()
    response = logged_in.get("/personals/resend_verification_email/")
    assert flash(response)[-1] == msg("verification_email_resent")
    assert len(mail.outbox) == 1


def test_resend_requires_login(client, db):
    assert client.get("/personals/resend_verification_email/").status_code == 302


# ---- settings -------------------------------------------------------------------------------------


def post_settings(client, **data):
    return client.post("/personals/settings/", data)


def test_settings_page(logged_in, user):
    assert logged_in.get("/personals/settings/").context["is_social_account"] is False
    SocialAccount.objects.create(user=user, provider="google", uid="1")
    assert logged_in.get("/personals/settings/").context["is_social_account"] is True


def test_settings_unknown_post_renders_page(logged_in):
    assert post_settings(logged_in, foo="bar").status_code == 200


def test_settings_requires_recent_login(logged_in, user):
    User.objects.filter(id=user.id).update(last_login=timezone.now() - datetime.timedelta(days=5))
    response = logged_in.get("/personals/settings/")
    assert response.url == "/personals/login/"
    assert flash(response) == [msg("relogin_to_edit")]


def test_settings_without_last_login(logged_in, user):
    User.objects.filter(id=user.id).update(last_login=None)
    assert logged_in.get("/personals/settings/").status_code == 200


def test_change_username(logged_in, user, other):
    assert flash(post_settings(logged_in, change_username="", new_username=""))[-1] == msg("missing_required_inputs")
    assert flash(post_settings(logged_in, change_username="1", new_username="x" * 151))[-1] == msg("too_long_input")
    assert flash(post_settings(logged_in, change_username="1", new_username="alice"))[-1] == msg(
        "username_belongs_to_you"
    )
    assert flash(post_settings(logged_in, change_username="1", new_username="bob"))[-1] == msg("username_not_available")
    response = post_settings(logged_in, change_username="1", new_username="alicia")
    assert flash(response)[-1] == msg("username_changed")
    user.refresh_from_db()
    assert user.username == "alicia"


def test_change_password(logged_in, user):
    assert flash(post_settings(logged_in, change_password="1", new_password=""))[-1] == msg("missing_required_inputs")
    response = post_settings(logged_in, change_password="1", new_password="brandnew1")
    assert flash(response)[-1] == msg("password_changed")
    user.refresh_from_db()
    assert user.check_password("brandnew1")
    assert logged_in.get("/personals/settings/").status_code == 200  # session survived the change


def test_change_email(logged_in, user, other):
    other.email = "taken@x.de"
    other.save()
    assert flash(post_settings(logged_in, change_email="1", email="bad"))[-1] == msg("invalid_email")
    assert flash(post_settings(logged_in, change_email="1", email="taken@x.de"))[-1] == msg("email_not_available")
    response = post_settings(logged_in, change_email="1", email="new@x.de")
    assert flash(response)[-1] == msg("email_changed")
    user.refresh_from_db()
    assert user.email == "new@x.de"
    assert user.usererweitert.mail_verified is False
    assert mail.outbox[0].to == ["new@x.de"]
    response = post_settings(logged_in, change_email="1", email="")
    assert flash(response)[-1] == msg("successfully_changed_email_no_email")
    user.refresh_from_db()
    assert user.email == ""


def test_change_email_rolls_back_if_mail_fails(logged_in, user):
    user.email = "old@x.de"
    user.save()
    with mock.patch("personals.views.send_mail_function", return_value=False):
        post_settings(logged_in, change_email="1", email="new@x.de")
    user.refresh_from_db()
    assert user.email == "old@x.de"
    assert user.usererweitert.mail_verified is True


def test_boolean_settings(logged_in, user):
    assert flash(post_settings(logged_in, change_email_settings="1"))[-1] == msg("mailinglist_disabled")
    assert flash(post_settings(logged_in, change_email_settings="1", mailinglist="on"))[-1] == msg(
        "mailinglist_enabled"
    )
    response = post_settings(logged_in, change_block_data_settings="1", block_data_settings="on")
    assert response.status_code == 302
    assert flash(response)[-1] == msg("allows_data_view_enabled")
    assert flash(post_settings(logged_in, change_block_data_settings="1"))[-1] == msg("allows_data_view_disabled")
    assert flash(post_settings(logged_in, change_tour_banner="1"))[-1] == msg("deactivated_tour_banner")
    assert flash(post_settings(logged_in, change_tour_banner="1", show_tour_banner="on"))[-1] == msg(
        "activated_tour_banner"
    )
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.show_tour_banner is True
    assert user.usererweitert.allows_data_view is False


def test_change_statement_is_sanitized(logged_in, user):
    post_settings(
        logged_in, change_statement="1", content="<p>hi</p><script>alert(1)</script><img src=x onerror=alert(1)>"
    )
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.statement == "<p>hi</p>alert(1)"


def test_change_weekly_goal(logged_in, user):
    for value, key in [
        ("abc", "not_a_number"),
        ("", "not_a_number"),
        ("0", "weekly_goal_too_small"),
        ("100001", "weekly_goal_too_large"),
        ("99999999999999999", "weekly_goal_too_large"),
    ]:
        response = post_settings(logged_in, change_weekly_goal="1", weekly_goal=value)
        assert response.url == "/personals/settings/"
        assert flash(response)[-1] == msg(key)
    response = post_settings(logged_in, change_weekly_goal="1", weekly_goal="42")
    assert response.url == "/dashboard/"
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.weekly_goal == 42


def test_change_language(logged_in, user):
    assert flash(post_settings(logged_in, change_lang="1", lang="fr"))[-1] == msg("internal_error")
    assert flash(post_settings(logged_in, change_lang="1", lang="en"))[-1] == "Language successfully changed"
    user.usererweitert.refresh_from_db()
    assert user.usererweitert.lang == "en"
    assert flash(post_settings(logged_in, change_lang="1", lang="de"))[-1] == "Sprache erfolgreich geändert"


def test_delete_account_notifies_family_and_community_members_once(logged_in, user, other, make_user):
    third = make_user("third")
    fourth = make_user("fourth")
    stranger = make_user("stranger")
    family_a = Family.objects.create(name="A", password="p", admin_password="a")
    family_a.members.add(user, other)
    family_b = Family.objects.create(name="B", password="p", admin_password="a")
    family_b.members.add(user, other)
    family_c = Family.objects.create(name="C", password="p", admin_password="a")
    family_c.members.add(third, fourth)
    community = Community.objects.create(name="comm", password="p", admin_password="a")
    community.members.add(family_a, family_c)
    response = post_settings(logged_in, delete_account="1")
    assert response.url == "/personals/login/"
    assert not User.objects.filter(username="alice").exists()
    notified = list(Benachrichtigung.objects.values_list("user__username", flat=True))
    assert sorted(notified) == ["bob", "fourth", "third"]
    assert not Benachrichtigung.objects.filter(user=stranger).exists()
    family_text = Benachrichtigung.objects.get(user=other).benachrichtigung_en
    assert "Family" not in family_text and "family" in family_text
    assert "who you were in a family with" in family_text
    assert "community" in Benachrichtigung.objects.get(user=third).benachrichtigung_en


# ---- password reset ----------------------------------------------------------------------------------


def test_reset_password_page(client, db):
    assert client.get("/personals/reset_password/").status_code == 200


@pytest.mark.parametrize("email", ["", "nobody@x.de"])
def test_reset_password_unknown_email(client, user, email):
    response = client.post("/personals/reset_password/", {"email": email})
    assert flash(response) == [msg("email_not_found")]


def test_reset_password_social_account(client, user):
    user.email = "a@x.de"
    user.save()
    SocialAccount.objects.create(user=user, provider="google", uid="1")
    response = client.post("/personals/reset_password/", {"email": "a@x.de"})
    assert flash(response) == [msg("socialaccount_no_password_reset")]


@pytest.mark.parametrize("verified, mailinglist", [(True, True), (False, True), (True, False), (False, False)])
def test_reset_password_always_mails_the_new_password(client, make_user, verified, mailinglist):
    target = make_user("target", email="t@x.de", mail_verified=verified, mailinglist=mailinglist)
    response = client.post("/personals/reset_password/", {"email": "t@x.de"})
    assert flash(response) == [msg("password_reset_mail_sent")]
    assert len(mail.outbox) == 1
    target.refresh_from_db()
    new_password = mail.outbox[0].alternatives[0][0].split("<b>")[1].split("</b>")[0]
    assert target.check_password(new_password)


def test_reset_password_keeps_old_password_if_mail_fails(client, make_user):
    target = make_user("target", email="t@x.de", mail_verified=True)
    with mock.patch("personals.views.send_mail_function", return_value=False):
        response = client.post("/personals/reset_password/", {"email": "t@x.de"})
    assert response.url == "/personals/reset_password/"
    target.refresh_from_db()
    assert target.check_password("pw12345!")


# ---- small json endpoints ----------------------------------------------------------------------------


def test_check_endpoints(client, user):
    user.email = "a@x.de"
    user.save()
    assert client.get("/personals/check-username/?username=alice").json() == {"exists": True}
    assert client.get("/personals/check-username/?username=zed").json() == {"exists": False}
    assert client.get("/personals/check-username/").json() == {"exists": False}
    assert client.get("/personals/check-email/?email=a@x.de").json() == {"exists": True}
    assert client.get("/personals/check-email/").json() == {"exists": False}


def test_settings_json_endpoints(logged_in, user):
    assert logged_in.get("/personals/get_email_settings/").json() == {"mailinglist": True}
    assert logged_in.get("/personals/get_block_data_settings/").json() == {"block_data_settings": False}


def test_get_email_settings_without_profile(client, db):
    user = User.objects.create_user("bare", password="x")
    client.force_login(user)
    with pytest.raises(UserErweitert.DoesNotExist):
        client.get("/personals/get_email_settings/")


# ---- credits ---------------------------------------------------------------------------------------


@pytest.fixture
def tree_codes(db):
    return [TreeCodes.objects.create(code=f"c{i}", redeemURL="https://x.de", sponsor="s") for i in range(3)]


def test_credit_view_numbers(logged_in, user, action_type, make_aktion):
    make_aktion(user, action_type, 300)  # 600 points, 500 per credit
    response = logged_in.get("/personals/credits/")
    assert response.context["available_credits"] == 1
    assert response.context["percent_done"] == 20
    assert response.context["klimapunkte_missing"] == 400


def test_credit_planting(logged_in, user, action_type, make_aktion, tree_codes):
    make_aktion(user, action_type, 300)
    response = logged_in.post("/personals/credits/")
    assert response.url == "/personals/credits/"
    assert user.usererweitert.given_credits == 1
    assert TreeCodes.objects.filter(planted=True).count() == 1
    logged_in.post("/personals/credits/")  # no second credit available
    assert TreeCodes.objects.filter(planted=True).count() == 1


def test_credit_planting_without_codes_reports_error(logged_in, user, action_type, make_aktion):
    make_aktion(user, action_type, 300)
    response = logged_in.post("/personals/credits/")
    assert flash(response) == [msg("error_planting_tree")]


def test_credit_planting_without_credit_does_nothing(logged_in, user, tree_codes):
    logged_in.post("/personals/credits/")
    assert not TreeCodes.objects.filter(planted=True).exists()


# ---- iOS devices -------------------------------------------------------------------------------------


def post_device(client, payload, raw=False):
    body = payload if raw else json.dumps(payload)
    return client.post("/personals/api/devices/ios/register/", body, content_type="application/json")


def test_register_ios_device(client, user):
    response = post_device(client, {"user_id": user.id, "apns_token": "tok", "bundle_id": "b", "app_version": "1"})
    assert response.json()["status"] == "ok"
    device = IOSDevice.objects.get()
    assert (device.user, device.bundle_id) == (user, "b")
    post_device(client, {"user_id": user.id, "apns_token": "tok", "bundle_id": "c"})
    assert IOSDevice.objects.count() == 1
    assert IOSDevice.objects.get().bundle_id == "c"
    assert str(device).startswith("alice - tok")


@pytest.mark.parametrize(
    "payload, status",
    [
        ("not json", 400),
        ("[1, 2]", 400),
        ({"apns_token": "t"}, 400),
        ({"user_id": 1}, 400),
        ({"user_id": 1, "apns_token": "t" * 201}, 400),
        ({"user_id": 1, "apns_token": 5}, 400),
        ({"user_id": 99999, "apns_token": "t"}, 404),
        ({"user_id": "abc", "apns_token": "t"}, 404),
    ],
)
def test_register_ios_device_errors(client, user, payload, status):
    response = post_device(client, payload, raw=isinstance(payload, str))
    assert response.status_code == status


def test_register_ios_device_requires_post(client, db):
    assert client.get("/personals/api/devices/ios/register/").status_code == 405


# ---- statistics -----------------------------------------------------------------------------------------


def test_statistics_requires_login(client, db):
    assert client.get("/personals/statistics/").status_code == 302


def test_statistics_chart_data(logged_in, en_client, user, action_type, make_aktion):
    today = timezone.localdate()
    make_aktion(user, action_type, 2, date=today)
    make_aktion(user, action_type, 1, date=today - datetime.timedelta(days=3))
    make_aktion(user, action_type, 1, date=today - datetime.timedelta(days=100))
    response = logged_in.get("/personals/statistics/")
    data = json.loads(response.context["chart_data"])
    assert data["categories"] == ["Mobilität"]
    assert data["series"] == [[2.0, 4.0]]
    assert len(data["labels"]) == 2
    en_client.force_login(user)
    assert json.loads(en_client.get("/personals/statistics/").context["chart_data"])["categories"] == ["Mobility"]


@pytest.mark.parametrize(
    "days, expected", [("7", 7), ("abc", 30), ("0", 30), ("-5", 30), ("99999999", 30), ("365", 365)]
)
def test_statistics_days_parameter(logged_in, days, expected):
    assert logged_in.get(f"/personals/statistics/?days={days}").context["days"] == expected


# ---- models, signals, adapter ----------------------------------------------------------------------------


def test_model_strings(user):
    tree = TreeCodes.objects.create(code="abc", redeemURL="https://x.de", sponsor="Sp")
    assert str(tree) == "Sp --> abc"
    assert str(user.usererweitert) == "alice"
    from personals.models import Level

    assert str(Level(description="Baum")) == "Baum"


def test_signal_creates_profile_for_social_signup(rf, worldwide, db):
    from allauth.account.signals import user_signed_up

    new_user = User.objects.create_user("social")
    request = rf.get("/")
    request.LANGUAGE_CODE = "en"
    user_signed_up.send(sender=User, request=request, user=new_user)
    assert new_user.usererweitert.lang == "en"
    assert worldwide.members.filter(id=new_user.id).exists()


def FakeSocialLogin(extra_data):  # noqa: N802 - behaves like a class in the tests below
    from allauth.socialaccount.models import SocialAccount
    from allauth.socialaccount.models import SocialLogin

    return SocialLogin(user=User(), account=SocialAccount(provider="google", uid="1", extra_data=extra_data))


@pytest.mark.parametrize(
    "extra, expected",
    [
        ({"name": {"firstName": "Ada", "lastName": "Lovelace"}, "email": "a@x.de"}, "Ada Lovelace"),
        ({"given_name": "Ada", "email": "a@x.de"}, "Ada"),
        ({"family_name": "Lovelace"}, "Lovelace"),
        ({"name": "Plain Name"}, "Plain Name"),
        ({"name": {"firstName": "", "lastName": ""}, "email": "only@x.de"}, "only@x.de"),
        ({}, None),
    ],
)
def test_adapter_username(db, extra, expected):
    from personals.adapters import MySocialAccountAdapter

    username = MySocialAccountAdapter()._build_username(FakeSocialLogin(extra))
    if expected is None:
        assert username.startswith("user-")
    else:
        assert username == expected


def test_adapter_falls_back_when_name_or_email_taken(db):
    from personals.adapters import MySocialAccountAdapter

    User.objects.create_user("Ada", email="a@x.de")
    username = MySocialAccountAdapter()._build_username(FakeSocialLogin({"given_name": "Ada", "email": "a@x.de"}))
    assert username.startswith("user-")


def test_adapter_populate_and_pre_login(rf, db):
    from allauth.core.exceptions import ImmediateHttpResponse

    from personals.adapters import MySocialAccountAdapter

    adapter = MySocialAccountAdapter()
    login = FakeSocialLogin({"given_name": "Zoe", "email": "z@x.de"})
    user = adapter.populate_user(rf.get("/"), login, {})
    assert (user.username, user.email) == ("Zoe", "z@x.de")
    User.objects.create_user("taken", email="z@x.de")
    user = adapter.populate_user(rf.get("/"), login, {})
    assert user.email == ""
    adapter.pre_social_login(rf.get("/"), login)  # name still free: no error
    with mock.patch.object(adapter, "_build_username", return_value="taken"):
        request = rf.get("/")
        request.session = {}
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)
        with pytest.raises(ImmediateHttpResponse):
            adapter.pre_social_login(request, login)


def test_reverse_names_exist():
    assert reverse("statistics_view") == "/personals/statistics/"
    assert Aktion and Benachrichtigung
