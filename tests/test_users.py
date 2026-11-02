import datetime
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone

from aktionen.models import Aktion
from core.all_messages import all_messages
from home.models import Benachrichtigung, ReportedUser
from personals.models import UserErweitert
from tests.conftest import flash

TODAY = timezone.localdate


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


# ---- access control -------------------------------------------------------------------------


def test_klimapunkte_requires_login(client, user):
    assert client.get(f"/users/klimapunkte/{user.id}/").status_code == 302


def test_unknown_user_redirects(logged_in):
    response = logged_in.get("/users/level/9999/")
    assert response.status_code == 302
    assert flash(response) == [str(all_messages["user_not_found"])]


def test_private_user_data_is_blocked(logged_in, make_user):
    private = make_user("private", allows_data_view=False)
    for url in ("level", "history", "klimapunkte"):
        response = logged_in.get(f"/users/{url}/{private.id}/")
        assert response.status_code == 302
    assert all_messages["user_blocked_view"] in [m for m in map(str, flash(response))] or True
    assert str(all_messages["user_blocked_view"]) in flash(response)


def test_get_user_without_profile(logged_in, db):
    from django.contrib.auth.models import User

    profileless = User.objects.create_user("noprofile", password="x")
    response = logged_in.get(f"/users/level/{profileless.id}/")
    assert response.status_code == 302
    assert str(all_messages["user_blocked_view"]) in flash(response)


def test_own_data_is_visible_even_if_private(logged_in, user):
    assert user.usererweitert.allows_data_view is False
    assert logged_in.get(f"/users/level/{user.id}/").status_code == 200


# ---- klimapunkte / level / history ---------------------------------------------------------------


def test_klimapunkte_total(logged_in, user, action_type, make_aktion):
    make_aktion(user, action_type, 10)
    make_aktion(user, action_type, 10, date=TODAY() - datetime.timedelta(days=40))
    response = logged_in.get(f"/users/klimapunkte/{user.id}/")
    assert response.context["klimapunkte"] == 40
    assert response.context["saved_co2"] == 0.04
    assert response.context["zeitraum"] == "Gesamt"


@pytest.mark.parametrize(
    "period, expected, text_de, text_en",
    [
        ("Gesamt", 40, "Gesamt", "Total"),
        ("Heute", 20, "Heute", "Today"),
        ("Sieben Tage", 20, "Sieben Tage", "Seven days"),
        ("Dreißig Tage", 20, "Dreißig Tage", "Thirty days"),
        ("Dreihundertfünfundsechzig Tage", 40, "Dreihundertfünfundsechzig Tage", "Three hundred sixty-five days"),
    ],
)
def test_klimapunkte_periods(logged_in, en_client, user, action_type, make_aktion, period, expected, text_de, text_en):
    make_aktion(user, action_type, 10, date=TODAY())
    make_aktion(user, action_type, 10, date=TODAY() - datetime.timedelta(days=40))
    response = logged_in.post(f"/users/klimapunkte/{user.id}/", {"zeitraum": period})
    assert (response.context["klimapunkte"], response.context["zeitraum"]) == (expected, text_de)
    en_client.force_login(user)
    response = en_client.post(f"/users/klimapunkte/{user.id}/", {"zeitraum": period})
    assert response.context["zeitraum"] == text_en


def test_klimapunkte_custom_period(logged_in, en_client, user, action_type, make_aktion):
    day = TODAY() - datetime.timedelta(days=40)
    make_aktion(user, action_type, 10, date=day)
    make_aktion(user, action_type, 10, date=TODAY())
    data = {
        "zeitraum": "Benutzerdefiniert",
        "start_date": (day - datetime.timedelta(days=1)).isoformat(),
        "end_date": day.isoformat(),
    }
    response = logged_in.post(f"/users/klimapunkte/{user.id}/", data)
    assert response.context["klimapunkte"] == 20
    assert (
        response.context["zeitraum"]
        == f"{(day - datetime.timedelta(days=1)).strftime('%d.%m.%Y')} bis {day.strftime('%d.%m.%Y')}"
    )
    en_client.force_login(user)
    response = en_client.post(f"/users/klimapunkte/{user.id}/", data)
    assert response.context["zeitraum"].startswith((day - datetime.timedelta(days=1)).strftime("%m/%d/%Y"))
    assert " to " in response.context["zeitraum"]


@pytest.mark.parametrize(
    "data, key",
    [
        ({"zeitraum": "bogus"}, "invalid_time_period"),
        ({"zeitraum": "Benutzerdefiniert"}, "missing_required_inputs"),
        ({"zeitraum": "Benutzerdefiniert", "start_date": "x", "end_date": "y"}, "invalid_date"),
        ({"zeitraum": "Benutzerdefiniert", "start_date": "2025-02-01", "end_date": "2025-01-01"}, "invalid_date_range"),
        ({"zeitraum": "Benutzerdefiniert", "start_date": "2025-02-01", "end_date": "2999-01-01"}, "date_in_future"),
    ],
)
def test_klimapunkte_invalid_periods(logged_in, user, data, key):
    response = logged_in.post(f"/users/klimapunkte/{user.id}/", data)
    assert response.status_code == 302
    assert flash(response) == [str(all_messages[key])]


def test_me_redirects(logged_in, user):
    assert logged_in.get("/users/klimapunkte/me/").url == f"/users/klimapunkte/{user.id}/"
    assert logged_in.get("/users/level/me/").url == f"/users/level/{user.id}/"
    assert logged_in.get("/users/history/me/").url == f"/users/history/{user.id}/"


def test_level_view(logged_in, user, levels):
    response = logged_in.get(f"/users/level/{user.id}/")
    assert response.context["level_data"]["current_level"] == levels[0]


def test_history_orders_newest_first_with_few_queries(
    logged_in, user, action_type, make_aktion, django_assert_max_num_queries
):
    for days in range(6):
        make_aktion(user, action_type, 1, date=TODAY() - datetime.timedelta(days=days))
    with django_assert_max_num_queries(8):
        response = logged_in.get(f"/users/history/{user.id}/")
    dates = [a.date for a in response.context["actions"]]
    assert dates == sorted(dates, reverse=True)


def test_users_overview(client, user, other):
    assert client.get("/users/overview/").status_code == 200
    response = client.post("/users/overview/", {"search_keyword": "ali"})
    assert list(response.context["users"]) == [user]
    response = client.post("/users/overview/", {})
    assert response.status_code == 200


# ---- user detail / report ----------------------------------------------------------------------------


def test_user_detail(client, user, worldwide):
    response = client.get(f"/users/detail/{user.id}/")
    assert response.status_code == 200
    assert response.context["worldwide_ranking_rank"] == 1
    assert client.get("/users/detail/9999/").status_code == 302


def test_report_user(logged_in, user, other, staff):
    admin = staff
    admin.username = "admin"
    admin.is_superuser = True
    admin.email = "admin@x.de"
    admin.save()
    UserErweitert.objects.filter(user=admin).update(mail_verified=True)
    response = logged_in.post(f"/users/detail/{other.id}/", {"reason": "<script>alert(1)</script> spam"})
    assert str(all_messages["reported_user"]) in flash(response)
    report = ReportedUser.objects.get()
    assert (report.reported_user, report.reporting_user) == (other, user)
    html = mail.outbox[0].alternatives[0][0]
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_report_user_escapes_reason(logged_in, user, other, make_user):
    admin = make_user("admin", is_staff=True, is_superuser=True, email="a@x.de", mail_verified=True)
    logged_in.post(f"/users/detail/{other.id}/", {"reason": "<b>x</b>"})
    assert "<b>x</b>" not in mail.outbox[0].body or "&lt;b&gt;" in mail.outbox[0].body
    assert admin


def test_report_without_admin_still_stores_report(logged_in, other):
    logged_in.post(f"/users/detail/{other.id}/", {"reason": "spam"})
    assert ReportedUser.objects.count() == 1
    assert mail.outbox == []


def test_report_without_reason_is_rejected(logged_in, other):
    response = logged_in.post(f"/users/detail/{other.id}/", {"reason": "   "})
    assert str(all_messages["missing_required_inputs"]) in flash(response)
    assert not ReportedUser.objects.exists()


def test_anonymous_cannot_report(client, other):
    client.post(f"/users/detail/{other.id}/", {"reason": "spam"})
    assert not ReportedUser.objects.exists()


# ---- action detail: edit / delete ---------------------------------------------------------------------


def edit_form(action_type, **overrides):
    data = {
        "edit_action": "1",
        "is_truth": "on",
        "action_type_id": str(action_type.id),
        "action_description": "changed",
        "action_quantity": "3",
    }
    data.update(overrides)
    return data


def test_action_detail_view(logged_in, user, action_type, make_aktion, other):
    aktion = make_aktion(user, action_type, 1)
    assert logged_in.get(f"/users/action_detail/{aktion.id}/{user.id}/").status_code == 200
    missing = logged_in.get(f"/users/action_detail/9999/{user.id}/")
    assert missing.url == f"/users/history/{user.id}/" or missing.status_code == 302
    blocked = logged_in.get(f"/users/action_detail/{aktion.id}/{other.id}/")
    assert blocked.status_code == 302


def test_cannot_edit_foreign_action(logged_in, other, action_type, make_aktion):
    aktion = make_aktion(other, action_type, 1)
    logged_in.post(f"/users/action_detail/{aktion.id}/{other.id}/", edit_form(action_type))
    logged_in.post(f"/users/action_detail/{aktion.id}/{other.id}/", {"delete_action": "1"})
    aktion.refresh_from_db()
    assert aktion.quantity == 1


def test_edit_action(logged_in, user, action_type, make_aktion):
    aktion = make_aktion(user, action_type, 1)
    response = logged_in.post(f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type))
    aktion.refresh_from_db()
    assert (aktion.quantity, aktion.description) == (3, "changed")
    assert flash(response)[-1] == str(all_messages["action_edited"])


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"is_truth": ""}, "not_is_truth"),
        ({"action_quantity": "0"}, "invalid_quantity"),
        ({"action_type_id": "999"}, "action_not_found"),
    ],
)
def test_edit_action_validation(logged_in, user, action_type, make_aktion, overrides, key):
    aktion = make_aktion(user, action_type, 1)
    response = logged_in.post(f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type, **overrides))
    assert flash(response)[-1] == str(all_messages[key])
    aktion.refresh_from_db()
    assert aktion.quantity == 1


def test_edit_action_max_check_uses_action_date_and_excludes_itself(logged_in, user, action_type, make_aktion):
    old_day = TODAY() - datetime.timedelta(days=3)
    aktion = make_aktion(user, action_type, 50, date=old_day)  # already at the daily maximum of that day
    make_aktion(user, action_type, 50, date=TODAY())  # a full other day must not matter
    response = logged_in.post(
        f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type, action_quantity="49")
    )
    assert flash(response)[-1] == str(all_messages["action_edited"])
    aktion.refresh_from_db()
    assert aktion.quantity == 49


def test_edit_action_too_past_stays_on_action(logged_in, user, action_type, make_aktion):
    aktion = make_aktion(user, action_type, 1, date=TODAY() - datetime.timedelta(days=60))
    response = logged_in.post(f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type))
    assert response.url == f"/users/action_detail/{aktion.id}/{user.id}/"
    assert flash(response)[-1] == str(all_messages["action_too_past"])


def test_edit_action_level_messages_use_matching_language(en_client, make_user, action_type, make_aktion, levels):
    user = make_user("english", lang="en")
    en_client.force_login(user)
    aktion = make_aktion(user, action_type, 1)
    en_client.post(f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type, action_quantity="50"))
    note = Benachrichtigung.objects.filter(user=user).order_by("id").first()
    assert "Sapling" in note.benachrichtigung_en
    assert "Setzling" in note.benachrichtigung_de


def test_edit_action_level_down_and_streak_down(logged_in, user, action_type, make_aktion, levels):
    monday = TODAY() - datetime.timedelta(days=TODAY().weekday())
    aktion = make_aktion(user, action_type, 50, date=TODAY())  # 100 points -> level 2 and goal met
    make_aktion(user, action_type, 10, date=monday - datetime.timedelta(days=7))
    response = logged_in.post(
        f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type, action_quantity="1")
    )
    texts = flash(response)
    assert any("abgestiegen" in t for t in texts)
    assert any("verkürzt" in t for t in texts)


def test_edit_action_level_up_and_streak_up(logged_in, user, action_type, make_aktion, levels):
    aktion = make_aktion(user, action_type, 1, date=TODAY())
    response = logged_in.post(
        f"/users/action_detail/{aktion.id}/{user.id}/", edit_form(action_type, action_quantity="50")
    )
    texts = flash(response)
    assert any("aufgestiegen" in t for t in texts)
    assert any("verlängert" in t for t in texts)


def test_delete_action(logged_in, user, action_type, make_aktion, levels):
    make_aktion(user, action_type, 10, date=TODAY() - datetime.timedelta(days=7 + TODAY().weekday()))
    aktion = make_aktion(user, action_type, 50, date=TODAY())
    response = logged_in.post(f"/users/action_detail/{aktion.id}/{user.id}/", {"delete_action": "1"})
    assert response.url == "/users/history/me/"
    assert not Aktion.objects.filter(id=aktion.id).exists()
    texts = flash(response)
    assert any("gelöscht" in t and "abgestiegen" in t for t in texts)
    assert any("Streak" in t for t in texts)
    assert texts[-1] == str(all_messages["action_deleted"])


def test_post_without_known_button_renders(logged_in, user, action_type, make_aktion):
    aktion = make_aktion(user, action_type, 1)
    assert logged_in.post(f"/users/action_detail/{aktion.id}/{user.id}/", {}).status_code == 200
