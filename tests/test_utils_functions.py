import datetime
import string
from unittest import mock

import pytest
from django.core import mail
from django.test import RequestFactory
from django.utils import timezone

from aktionen.models import Aktion
from artikel.models import Artikel
from artikel.models import Category as ArtikelCategory
from community.models import Community
from family.models import Family
from home.models import Benachrichtigung
from personals.models import IOSDevice, UserErweitert
from utils import functions as fn


def make_request(user=None, lang="de"):
    request = RequestFactory().get("/")
    request.user = user
    request.LANGUAGE_CODE = lang
    request.session = {}
    from django.contrib.messages.storage.fallback import FallbackStorage

    request._messages = FallbackStorage(request)
    return request


def test_generate_random_password_uses_safe_alphabet_and_length():
    passwords = {fn.generate_random_password() for _ in range(20)}
    assert len(passwords) == 20
    allowed = set(string.ascii_letters + string.digits + string.punctuation) - {'"', "'"}
    for password in passwords:
        assert len(password) == 12
        assert set(password) <= allowed


def test_generate_random_password_uses_cryptographic_source():
    with mock.patch("utils.functions.secrets.choice", side_effect=lambda seq: seq[0]) as choice:
        assert fn.generate_random_password() == "a" * 12
    assert choice.call_count == 12


# ---- klimapunkte / levels -------------------------------------------------------------


def test_get_klimapunkte_for_queryset_and_list(user, action_type, make_aktion):
    make_aktion(user, action_type, 3)
    make_aktion(user, action_type, 2)
    queryset = Aktion.objects.filter(user=user)
    assert fn.get_klimapunkte(queryset) == 10
    assert fn.get_klimapunkte(list(queryset)) == 10
    assert fn.get_klimapunkte(Aktion.objects.none()) == 0


def test_get_klimapunkte_runs_constant_queries(user, action_type, make_aktion, django_assert_num_queries):
    for _ in range(5):
        make_aktion(user, action_type, 1)
    with django_assert_num_queries(1):
        fn.get_klimapunkte(Aktion.objects.filter(user=user))


def test_additional_klimapunkte_include_likes(user, other, category):
    user.usererweitert.additional_klimapunkte = 5
    user.usererweitert.save()
    cat = ArtikelCategory.objects.create(title="c")
    artikel = Artikel.objects.create(
        name_de="a", name_en="a", content_de="c", content_en="c", creator=user, category=cat
    )
    artikel.like.add(other)
    assert fn.get_klimapunkte_from_likes(user) == pytest.approx(0.1)
    assert fn.get_additional_klimapunkte(user) == pytest.approx(5.1)


def test_all_klimapunkte_from_user(user, action_type, make_aktion):
    make_aktion(user, action_type, 4)
    assert fn.get_all_klimapunkte_from_user(user) == 8


def test_get_level_progress(user, levels, action_type, make_aktion):
    make_aktion(user, action_type, 25)  # 50 points
    data = fn.get_level(user)
    assert data["current_level"] == levels[0]
    assert data["next_level"] == levels[1]
    assert data["progress_percent"] == 50
    assert data["klimapunkte_missing"] == 50
    assert data["level_number"] == 1
    assert fn.get_level(user, 50)["progress_percent"] == 50


def test_get_level_highest(user, levels, action_type, make_aktion):
    make_aktion(user, action_type, 400)  # 800 points
    for data in (fn.get_level(user), fn.get_level(user, 800)):
        assert data["current_level"] == levels[2]
        assert data["level_number"] == 3
        assert "Baum" in data["info"]


def test_get_level_without_level_zero_does_not_crash(user, levels):
    levels[0].delete()
    data = fn.get_level(user)
    assert data["current_level"] is None
    assert data["next_level"] == levels[1]
    assert data["level_number"] == 0
    assert data["klimapunkte_missing"] == 100


def test_get_level_without_any_level(user, db):
    data = fn.get_level(user)
    assert data["current_level"] is None
    assert data["next_level"] is None


def test_get_level_equal_thresholds(user, db):
    from personals.models import Level

    Level.objects.create(klimapunkte=0, description="a", description_en="a")
    Level.objects.create(klimapunkte=0, description="b", description_en="b")
    assert fn.get_level(user, 0)["level_number"] == 2


def test_weekly_goal(user, action_type, make_aktion):
    today = timezone.localdate()
    make_aktion(user, action_type, 5, date=today)
    make_aktion(user, action_type, 100, date=today - datetime.timedelta(days=30))
    goal, points, percent = fn.get_weekly_goal_from_user(user)
    assert (goal, points, percent) == (20, 10, 50)


def test_streak(user, action_type, make_aktion):
    today = timezone.localdate()
    monday = today - datetime.timedelta(days=today.weekday())
    assert fn.get_streak_from_user(user) == 0
    make_aktion(user, action_type, 10, date=monday - datetime.timedelta(days=7))  # 20 points, goal met
    make_aktion(user, action_type, 10, date=monday - datetime.timedelta(days=14))
    assert fn.get_streak_from_user(user) == 2
    make_aktion(user, action_type, 1, date=monday)  # current week below goal does not break the streak
    assert fn.get_streak_from_user(user) == 2
    make_aktion(user, action_type, 10, date=monday)  # current week met
    assert fn.get_streak_from_user(user) == 3


def test_streak_gap_breaks(user, action_type, make_aktion):
    today = timezone.localdate()
    monday = today - datetime.timedelta(days=today.weekday())
    make_aktion(user, action_type, 10, date=monday - datetime.timedelta(days=7))
    make_aktion(user, action_type, 10, date=monday - datetime.timedelta(days=21))
    assert fn.get_streak_from_user(user) == 1


def test_streak_week_below_goal_stops(user, action_type, make_aktion):
    today = timezone.localdate()
    monday = today - datetime.timedelta(days=today.weekday())
    make_aktion(user, action_type, 1, date=monday - datetime.timedelta(days=7))
    assert fn.get_streak_from_user(user) == 0


def test_perfect_week_progress(user, category, action_type, make_aktion):
    from aktionen.models import Category

    Category.objects.create(name="Essen", name_en="Food")
    make_aktion(user, action_type, 1, date=timezone.localdate())
    de, en = fn.get_perfect_week_progress(user, timezone.localdate())
    assert de == {"Mobilität": True, "Essen": False}
    assert en == {"Mobility": True, "Food": False}


def test_date_range_and_member_points(user, action_type, make_aktion):
    today = datetime.date(2025, 6, 15)
    assert fn.get_date_range("Heute", today) == (today, today)
    assert fn.get_date_range("Sieben Tage", today) == (today - datetime.timedelta(days=7), today)
    assert fn.get_date_range("Gesamt", today) == (None, None)
    make_aktion(user, action_type, 1, date=today)
    make_aktion(user, action_type, 1, date=today - datetime.timedelta(days=10))
    assert fn.get_klimapunkte_for_member(user, None, None) == 4
    assert fn.get_klimapunkte_for_member(user, today - datetime.timedelta(days=7), None) == 2
    assert fn.get_klimapunkte_for_member(user, today - datetime.timedelta(days=7), today) == 2


def test_family_rank(user, other, worldwide, action_type, make_aktion):
    make_aktion(other, action_type, 10)
    make_aktion(user, action_type, 5)
    assert fn.get_family_rank_from_user(user, worldwide) == 2
    assert fn.get_family_rank_from_user(other, worldwide) == 1
    assert fn.get_worldwide_rank(user, 10) == 2
    assert fn.get_worldwide_rank(other, 20) == 1


def test_family_rank_for_non_member_is_none(user, make_user, worldwide):
    outsider = make_user("outsider")
    family = Family.objects.create(name="small", password="p", admin_password="a")
    family.members.add(user)
    assert fn.get_family_rank_from_user(outsider, family) is None


def test_family_rank_optimized_query_count_is_constant(
    user, make_user, action_type, make_aktion, django_assert_max_num_queries
):
    for i in range(10):
        make_aktion(make_user(f"m{i}"), action_type, i)
    with django_assert_max_num_queries(5):
        fn.get_worldwide_rank(user)


def test_family_rank_optimized_missing_family(user, worldwide):
    worldwide.delete()
    assert fn.get_worldwide_rank(user) is None


def test_hall_of_fame_entry_count(user, db):
    from hall_of_fame.models import HallOfFameEntry

    HallOfFameEntry.objects.create(user=user, description_de="a", description_en="a")
    assert fn.get_hall_of_fame_entries(user) == 1


# ---- families / communities ------------------------------------------------------------


def test_families_and_communities_of_user(user, other, worldwide):
    family = Family.objects.create(name="A", password="p", admin_password="a")
    family.members.add(user)
    community = Community.objects.create(name="C", password="p", admin_password="a")
    community.members.add(family)
    assert list(fn.get_families_of_user(user)) == [family, worldwide]
    assert list(fn.get_communities_of_user(user)) == [community]
    assert list(fn.get_communities_of_family(family)) == [community]
    assert list(fn.get_communities_of_user(other)) == []


# ---- html / images ---------------------------------------------------------------------


def test_clean_html_strips_scripts_and_adds_nofollow():
    cleaned = fn.clean_html('<p>Hi</p><script>alert(1)</script><a href="https://x.de">x</a><img src=x onerror=1>')
    assert "<script" not in cleaned
    assert "onerror" not in cleaned
    assert 'rel="nofollow"' in cleaned
    assert "<p>Hi</p>" in cleaned


def test_check_is_truth(db):
    request = make_request()
    request.method = "POST"
    request.POST = {"is_truth": "on"}
    assert fn.check_is_truth(request) is True
    request.POST = {}
    assert fn.check_is_truth(request) is False


def test_email_validation():
    assert fn.ist_email_gueltig("a@b.de")
    assert not fn.ist_email_gueltig("nope")


# ---- mail / push / notifications -----------------------------------------------------------


def test_send_mail_to_verified_user(user):
    user.email = "a@b.de"
    user.save()
    UserErweitert.objects.filter(user=user).update(mail_verified=True)
    request = make_request(user)
    assert fn.send_mail_function(request=request, subject="Hi", message="Body <b>x</b>", user=user) is True
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["a@b.de"]
    assert message.subject == "Hi"
    html = message.alternatives[0][0]
    assert "Body <b>x</b>" in html
    assert "Hier abmelden" in html


def test_send_mail_skips_unverified_and_unsubscribed_and_empty(user):
    user.email = "a@b.de"
    user.save()
    request = make_request(user)
    assert fn.send_mail_function(request=request, subject="s", message="m", user=user) is True  # unverified
    UserErweitert.objects.filter(user=user).update(mail_verified=True, mailinglist=False)
    assert fn.send_mail_function(request=request, subject="s", message="m", user=user) is False  # unsubscribed
    user.email = ""
    assert fn.send_mail_function(request=request, subject="s", message="m", user=user) is True
    assert mail.outbox == []


def test_send_mail_without_mailinglist_check(user):
    request = make_request(user)
    assert (
        fn.send_mail_function(
            request=request, subject="s", message="m", user=user, recipient_list="x@y.de", mailinglist_needless=True
        )
        is True
    )
    assert mail.outbox[0].to == ["x@y.de"]
    assert "Hier abmelden" not in mail.outbox[0].alternatives[0][0]


def test_send_mail_escapes_subject_in_html(user):
    request = make_request(user)
    fn.send_mail_function(
        request=request,
        subject="<script>x</script>",
        message="m",
        user=user,
        recipient_list="x@y.de",
        mailinglist_needless=True,
    )
    assert "<script>" not in mail.outbox[0].alternatives[0][0]


def test_send_mail_failure_reports_error(user):
    request = make_request(user)
    with (
        mock.patch("utils.functions.EmailMultiAlternatives.send", side_effect=OSError("smtp down")),
        mock.patch("utils.functions.create_internal_error") as error,
    ):
        result = fn.send_mail_function(
            request=request, subject="s", message="m", user=user, recipient_list="x@y.de", mailinglist_needless=True
        )
    assert result is False
    error.assert_called_once()


def test_send_mail_failure_for_subscribed_user(user):
    user.email = "a@b.de"
    user.save()
    UserErweitert.objects.filter(user=user).update(mail_verified=True)
    with (
        mock.patch("utils.functions.EmailMultiAlternatives.send", side_effect=OSError("smtp down")),
        mock.patch("utils.functions.create_internal_error") as error,
    ):
        assert fn.send_mail_function(request=make_request(user), subject="s", message="m", user=user) is False
    error.assert_called_once()


def test_send_mail_uses_request_user_by_default(user):
    request = make_request(user)
    assert fn.send_mail_function(request=request, subject="s", message="m") is True


def test_send_mail_missing_arguments_is_reported(user):
    with mock.patch("utils.functions.create_internal_error") as error:
        assert fn.send_mail_function(request=make_request(user), user=user) is False
    error.assert_called_once()


def test_send_mail_without_request_does_not_crash(user):
    assert fn.send_mail_function(
        subject="s", message="m", user=user, recipient_list="x@y.de", mailinglist_needless=True
    )
    assert len(mail.outbox) == 1


def test_create_internal_error_logs_and_redacts(user, settings, tmp_path):
    settings.LOGS_DIR = tmp_path / "logs"
    request = RequestFactory().post("/x/?a=1", {"password": "secret", "name": "n"}, HTTP_USER_AGENT="ua")
    request.user = user
    request.COOKIES = {"sessionid": "abc"}
    request.session = {}
    from django.contrib.messages.storage.fallback import FallbackStorage

    request._messages = FallbackStorage(request)
    with mock.patch("utils.functions.logger.error") as log:
        fn.create_internal_error(request, "desc", "visible message", exception=ValueError("boom"))
    entry = log.call_args.args[0]
    assert entry["POST"]["password"] == "***"
    assert entry["POST"]["name"] == "n"
    assert entry["COOKIES"] == {"sessionid": "***"}
    assert entry["exception"] == "boom"
    assert "HTTP_USER_AGENT" in entry["META"]
    assert (tmp_path / "logs" / "errors.log").read_text().count("desc") == 1
    assert [str(m) for m in request._messages] == ["visible message"]


def test_create_internal_error_anonymous_without_message(tmp_path, settings):
    from django.contrib.auth.models import AnonymousUser

    settings.LOGS_DIR = tmp_path / "does" / "not" / "exist"
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    fn.create_internal_error(request, "x", throw_exception=False)
    assert (settings.LOGS_DIR / "errors.log").exists()


def test_create_notification_german_and_english(make_user):
    de_user = make_user("de_user", lang="de", email="d@x.de", mail_verified=True)
    en_user = make_user("en_user", lang="en", email="e@x.de", mail_verified=True)
    request = make_request(de_user)
    with mock.patch("utils.functions.send_push", return_value=200) as push:
        fn.create_notification(request, "deutsch <span>x</span>", "english <span>x</span>", user=de_user)
        fn.create_notification(request, "deutsch", "english", user=en_user, url="/somewhere/")
    assert Benachrichtigung.objects.get(user=de_user).url == "/de/dashboard/" or Benachrichtigung.objects.get(
        user=de_user
    ).url.endswith("/dashboard/")
    assert Benachrichtigung.objects.get(user=en_user).url == "/somewhere/"
    assert push.call_args_list[0].kwargs["benachrichtigung"] == "deutsch "
    assert push.call_args_list[0].kwargs["head"] == "Neue Benachrichtigung"
    assert push.call_args_list[1].kwargs["benachrichtigung"] == "english"
    assert push.call_args_list[1].kwargs["head"] == "New notification"
    assert [m.subject for m in mail.outbox] == ["ClimateQuest - neue Benachrichtigung"] * 2


def test_create_notification_defaults_to_request_user(user):
    with mock.patch("utils.functions.send_push", return_value=200):
        fn.create_notification(make_request(user), "de", "en")
    assert Benachrichtigung.objects.filter(user=user).count() == 1


def test_create_notification_push_errors(user):
    IOSDevice.objects.create(user=user, apns_token="tok")
    with (
        mock.patch("utils.functions.send_push", return_value=500),
        mock.patch("utils.functions.send_ios_push", side_effect=RuntimeError("apns")) as ios,
        mock.patch("utils.functions.create_internal_error") as error,
    ):
        fn.create_notification(make_request(user), "de", "en", user=user)
    ios.assert_called_once()
    error.assert_called_once()


def test_send_push(user):
    with mock.patch("utils.functions.send_user_notification") as send:
        assert fn.send_push("hi", user) == 200
        send.assert_called_once()
    with mock.patch("utils.functions.send_user_notification", side_effect=TypeError):
        assert fn.send_push("hi", user) == 500


def test_send_ios_push(settings, tmp_path):
    settings.APNS_HOST = "https://apns.example"
    settings.APPLE_BUNDLE_ID = "bundle"
    ok = mock.Mock(status_code=200)
    with (
        mock.patch("utils.functions._make_jwt", return_value="jwt"),
        mock.patch("utils.functions.httpx.Client") as client_cls,
    ):
        client_cls.return_value.__enter__.return_value.post.return_value = ok
        fn.send_ios_push("tok", "t", "b", {"url": "/x"})
        post = client_cls.return_value.__enter__.return_value.post
        assert post.call_args.args[0] == "https://apns.example/3/device/tok"
        assert post.call_args.kwargs["json"]["url"] == "/x"
        fn.send_ios_push("tok", "t", "b")
        bad = mock.Mock(status_code=400, text="bad")
        post.return_value = bad
        with pytest.raises(RuntimeError, match="APNs Fehler 400"):
            fn.send_ios_push("tok", "t", "b")


def test_make_jwt(settings, tmp_path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    key_file = tmp_path / "key.p8"
    key_file.write_bytes(pem)
    settings.APN_KEY_PATH = key_file
    settings.APPLE_TEAM_ID = "TEAM"
    settings.APN_KEY_ID = "KID"
    import jwt

    token = fn._make_jwt()
    assert jwt.get_unverified_header(token)["kid"] == "KID"
    assert jwt.decode(token, options={"verify_signature": False})["iss"] == "TEAM"
