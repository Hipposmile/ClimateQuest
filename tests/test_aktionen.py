import datetime
from unittest import mock

import pytest
from django.utils import timezone

from aktionen import services
from aktionen.models import Aktion, AktionenListe, Category, TrackedActions
from aktionen.views import add_weekly_tracking_action
from core.all_messages import all_messages
from home.models import Benachrichtigung
from tests.conftest import flash

TODAY = timezone.localdate


def form(action_type, **overrides):
    data = {
        "is_truth": "on",
        "action_type_id": str(action_type.id),
        "action_description": "desc",
        "action_date": TODAY().isoformat(),
        "action_quantity": "2",
    }
    data.update(overrides)
    return data


def last_flash(response):
    return flash(response)[-1]


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


@pytest.fixture
def day_type(category):
    """An action blocking a whole day per quantity unit (timely)."""
    return AktionenListe.objects.create(
        name="Vegan",
        name_en="Vegan",
        klimapunkte=1,
        mengeBeschreibung="Tage",
        mengeBeschreibung_en="days",
        mengeBeschreibungSingular="Tag",
        mengeBeschreibungSingular_en="day",
        anmerkung="",
        anmerkung_en="",
        source="",
        source_en="",
        category=category,
    )


@pytest.fixture
def week_type(category):
    return AktionenListe.objects.create(
        name="Veggie",
        name_en="Veggie",
        klimapunkte=5,
        mengeBeschreibung="Wochen",
        mengeBeschreibung_en="weeks",
        mengeBeschreibungSingular="Woche",
        mengeBeschreibungSingular_en="week",
        anmerkung="",
        anmerkung_en="",
        source="",
        source_en="",
        category=category,
        track_weekly=True,
    )


# ---- services ------------------------------------------------------------------------------


def test_period_start_units():
    end = datetime.date(2025, 3, 31)
    assert services.get_period_start(end, 2, "Tag") == datetime.date(2025, 3, 29)
    assert services.get_period_start(end, 1, "Woche") == datetime.date(2025, 3, 24)
    assert services.get_period_start(end, 1, "Monat") == datetime.date(2025, 3, 1)
    assert services.get_period_start(end, 1, "Kilometer") is None
    assert services.get_period_start(end, 1e18, "Tag") == datetime.date.min


def test_is_timely_unit():
    assert services.is_timely_unit("Woche") and services.is_timely_unit("tag")
    assert not services.is_timely_unit("Kilometer")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2", 2.0),
        ("2,5", 2.5),
        ("1.23456", 1.2346),
        ("abc", None),
        ("", None),
        ("nan", None),
        ("inf", None),
        (None, None),
    ],
)
def test_validate_number(raw, expected):
    assert services.validate_number(raw) == expected


def test_forbidden_actions_conflict_both_directions(user, day_type, week_type, make_aktion):
    week_type.forbidden_in_same_period.add(day_type)
    day_type.forbidden_in_same_period.add(week_type)
    today = TODAY()
    make_aktion(user, week_type, 1, date=today)  # covers the last 7 days
    assert services.action_date_invalid(day_type, today - datetime.timedelta(days=2), 1, user)
    assert services.action_date_invalid(day_type, today, 1, user)
    assert not services.action_date_invalid(day_type, today - datetime.timedelta(days=10), 1, user)
    assert not services.action_date_invalid(day_type, today, 1, user, exclude_id=Aktion.objects.get().id)


def test_non_timely_actions_never_conflict(user, action_type, make_aktion):
    make_aktion(user, action_type, 1)
    assert not services.action_date_invalid(action_type, TODAY(), 1, user)


def test_later_non_timely_conflicting_action_is_skipped(user, day_type, action_type, make_aktion):
    day_type.forbidden_in_same_period.add(action_type)
    make_aktion(user, action_type, 1, date=TODAY())
    make_aktion(user, day_type, 1, date=TODAY())
    assert not services.action_is_in_different_action_period(day_type, TODAY() - datetime.timedelta(days=5), user)


# ---- add view ------------------------------------------------------------------------------


def test_add_get(logged_in, action_type):
    response = logged_in.get("/aktionen/add/")
    assert response.status_code == 200
    assert list(response.context["categories"]) == [action_type.category]


def test_add_requires_login(client, db):
    assert client.get("/aktionen/add/").status_code == 302


def test_add_action_success(logged_in, user, action_type, levels):
    response = logged_in.post("/aktionen/add/", form(action_type))
    aktion = Aktion.objects.get()
    assert response.url == f"/users/action_detail/{aktion.id}/{user.id}/"
    assert (aktion.quantity, aktion.description, aktion.date) == (2.0, "desc", TODAY())
    assert last_flash(response) == str(all_messages["action_added"])


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"is_truth": ""}, "not_is_truth"),
        ({"action_type_id": ""}, "action_name_missing"),
        ({"action_type_id": "999"}, "action_not_found"),
        ({"action_type_id": "abc"}, "action_not_found"),
        ({"action_description": "x" * 201}, "too_long_input"),
        ({"action_date": ""}, "missing_required_inputs"),
        ({"action_date": "2025-13-45"}, "invalid_date"),
        ({"action_quantity": ""}, "missing_required_inputs"),
        ({"action_quantity": "abc"}, "invalid_quantity"),
        ({"action_quantity": "0"}, "invalid_quantity"),
        ({"action_quantity": "-3"}, "invalid_quantity"),
        ({"action_quantity": "nan"}, "invalid_quantity"),
        ({"action_quantity": "51"}, "max_action_quantity"),
        ({"action_date": (TODAY() + datetime.timedelta(days=1)).isoformat()}, "date_in_future"),
        ({"action_date": (TODAY() - datetime.timedelta(days=60)).isoformat()}, "action_too_past"),
    ],
)
def test_add_action_validation_errors(logged_in, action_type, overrides, key):
    response = logged_in.post("/aktionen/add/", form(action_type, **overrides))
    assert response.url == "/aktionen/add/"
    assert last_flash(response) == str(all_messages[key])
    assert not Aktion.objects.exists()


def test_add_action_missing_description_is_allowed(logged_in, action_type):
    data = form(action_type)
    del data["action_description"]
    logged_in.post("/aktionen/add/", data)
    assert Aktion.objects.get().description == ""


def test_add_action_max_counts_existing_same_day(logged_in, user, action_type, make_aktion):
    make_aktion(user, action_type, 49, date=TODAY())
    response = logged_in.post("/aktionen/add/", form(action_type, action_quantity="2"))
    assert last_flash(response) == str(all_messages["max_action_quantity"])
    # a different day has its own limit
    day = TODAY() - datetime.timedelta(days=1)
    logged_in.post("/aktionen/add/", form(action_type, action_quantity="2", action_date=day.isoformat()))
    assert Aktion.objects.count() == 2


def test_add_huge_timely_quantity_is_rejected_not_crashing(logged_in, day_type):
    response = logged_in.post("/aktionen/add/", form(day_type, action_quantity="1e300"))
    assert last_flash(response) == str(all_messages["action_too_past"])


def test_add_timely_action_checks_start_of_period(logged_in, week_type):
    response = logged_in.post("/aktionen/add/", form(week_type, action_quantity="6"))  # ~42 days back
    assert last_flash(response) == str(all_messages["action_too_past"])
    assert not Aktion.objects.exists()


def test_add_timely_action_conflict(logged_in, user, day_type, make_aktion):
    make_aktion(user, day_type, 1, date=TODAY())
    response = logged_in.post("/aktionen/add/", form(day_type, action_quantity="1"))
    assert last_flash(response) == str(all_messages["action_already_set_in_period"])


def test_add_action_level_up_and_streak_notifications(logged_in, user, action_type, levels):
    response = logged_in.post("/aktionen/add/", form(action_type, action_quantity="50"))  # 100 points -> level 2
    texts = flash(response)
    assert any("Setzling" in t for t in texts)
    assert "request-review" in texts
    assert any("Streak" in t for t in texts)
    kinds = {n.benachrichtigung_de for n in Benachrichtigung.objects.filter(user=user)}
    assert len(kinds) == 2


def test_add_action_english_feedback(en_client, user, action_type, levels):
    en_client.force_login(user)
    response = en_client.post("/aktionen/add/", form(action_type, action_quantity="50"))
    assert any("reached the level Sapling" in t for t in flash(response))


# ---- tracking ------------------------------------------------------------------------------


def test_track_page_lists_actions(logged_in, user, week_type, action_type):
    action_type.track_kilometerly = True
    action_type.save()
    TrackedActions.objects.create(action=week_type, user=user)
    response = logged_in.get("/aktionen/track/")
    weekly = response.context["trackable_actions_weekly"]
    assert weekly["Veggie"]["done"] is True
    assert weekly["Veggie"]["since"] is not None
    assert list(response.context["trackable_actions_kilometerly"]) == [action_type]


def test_track_page_query_count(logged_in, user, category, django_assert_max_num_queries):
    for i in range(8):
        AktionenListe.objects.create(
            name=f"w{i}",
            name_en=f"w{i}",
            klimapunkte=1,
            mengeBeschreibung="x",
            mengeBeschreibung_en="x",
            mengeBeschreibungSingular="Woche",
            mengeBeschreibungSingular_en="x",
            anmerkung="",
            anmerkung_en="",
            source="",
            source_en="",
            category=category,
            track_weekly=True,
        )
    with django_assert_max_num_queries(8):
        logged_in.get("/aktionen/track/")


def test_weekly_track_toggle(logged_in, user, week_type):
    response = logged_in.post("/aktionen/track/", {"weekly_track": week_type.id})
    assert last_flash(response) == str(all_messages["tracking_action"])
    assert TrackedActions.objects.filter(user=user, action=week_type).exists()
    response = logged_in.post("/aktionen/track/", {"weekly_track": week_type.id})
    assert last_flash(response) == str(all_messages["stopped_tracking"])
    assert not TrackedActions.objects.exists()


def test_weekly_track_forbidden_and_unknown(logged_in, user, week_type, day_type):
    day_type.track_weekly = True
    day_type.save()
    week_type.forbidden_in_same_period.add(day_type)
    TrackedActions.objects.create(action=day_type, user=user)
    response = logged_in.post("/aktionen/track/", {"weekly_track": week_type.id})
    assert last_flash(response) == str(all_messages["forbidden_tracking_action"])
    for bad in ("999", "abc", ""):
        response = logged_in.post("/aktionen/track/", {"weekly_track": bad})
        assert last_flash(response) == str(all_messages["internal_error"])


def test_kilometer_tracking(logged_in, user, action_type):
    action_type.track_kilometerly = True
    action_type.save()
    response = logged_in.post(
        "/aktionen/track/", {"kilometerly_track": "1", "distance": "2500", "action_id": action_type.id}
    )
    aktion = Aktion.objects.get()
    assert response.json() == {"success": True, "action_id": aktion.id, "user_id": user.id}
    assert aktion.quantity == 2.5
    assert "automatisch getrackt" in aktion.description


def test_kilometer_tracking_english_description(en_client, make_user, action_type):
    action_type.track_kilometerly = True
    action_type.save()
    en_user = make_user("english", lang="en")
    en_client.force_login(en_user)
    en_client.post("/aktionen/track/", {"kilometerly_track": "1", "distance": "10", "action_id": action_type.id})
    assert "automatically tracked" in Aktion.objects.get().description


@pytest.mark.parametrize("distance", ["abc", "", "0", "-500"])
def test_kilometer_tracking_rejects_invalid_distance(logged_in, action_type, distance):
    action_type.track_kilometerly = True
    action_type.save()
    response = logged_in.post(
        "/aktionen/track/", {"kilometerly_track": "1", "distance": distance, "action_id": action_type.id}
    )
    assert response.status_code == 302
    assert not Aktion.objects.exists()


def test_kilometer_tracking_only_for_trackable_actions(logged_in, action_type):
    response = logged_in.post(
        "/aktionen/track/", {"kilometerly_track": "1", "distance": "100", "action_id": action_type.id}
    )
    assert response.json()["success"] is False
    response = logged_in.post("/aktionen/track/", {"kilometerly_track": "1", "distance": "100", "action_id": "x"})
    assert response.json()["success"] is False
    assert not Aktion.objects.exists()


def test_track_post_without_known_field_renders_page(logged_in):
    assert logged_in.post("/aktionen/track/", {}).status_code == 200


def test_weekly_cron_adds_actions(user, make_user, week_type):
    english = make_user("eng", lang="en")
    old = TODAY() - datetime.timedelta(days=7)
    TrackedActions.objects.create(action=week_type, user=user, since=old)
    TrackedActions.objects.create(action=week_type, user=english, since=old)
    recent = make_user("recent")
    TrackedActions.objects.create(action=week_type, user=recent, since=TODAY())
    with mock.patch("utils.functions.send_push", return_value=200):
        add_weekly_tracking_action()
        add_weekly_tracking_action()  # second run: already tracked this week, nothing changes
    assert Aktion.objects.filter(user=user).count() == 1
    assert Aktion.objects.filter(user=recent).count() == 0
    assert "Eingetragen" in Aktion.objects.get(user=user).description
    assert "added by" in Aktion.objects.get(user=english).description


def test_weekly_cron_query_count(make_user, week_type, django_assert_max_num_queries):
    old = TODAY() - datetime.timedelta(days=7)
    for i in range(6):
        TrackedActions.objects.create(action=week_type, user=make_user(f"c{i}"), since=old)
    with django_assert_max_num_queries(6 * 6 + 3):
        add_weekly_tracking_action()


def test_model_str_and_impact(user, action_type, make_aktion):
    aktion = make_aktion(user, action_type, 3)
    assert aktion.impact == 6
    assert str(aktion) == "Fahrrad (alice)"
    assert str(action_type) == "Fahrrad"
    assert str(action_type.category) == "Mobilität"
    tracked = TrackedActions.objects.create(action=action_type, user=user)
    assert str(tracked) == "Fahrrad --> (alice)"
    assert Category.objects.count() == 1
