from unittest import mock

import pytest
from django.utils import timezone

from artikel.models import Artikel
from artikel.models import Category as ArtikelCategory
from community.models import Community
from core.all_messages import all_messages
from events.models import Event
from family.models import Family
from home.models import Benachrichtigung
from personals.models import TreeCodes
from tests.conftest import flash


@pytest.mark.parametrize(
    "url", ["/support/", "/feedback/", "/impressum/", "/datenschutz/", "/nutzungsbedingungen/", "/companies-schools"]
)
def test_static_pages(client, url, db, worldwide):
    assert client.get(url).status_code == 200


def test_home_statistics(client, user, other, action_type, make_aktion, django_assert_max_num_queries):
    make_aktion(user, action_type, 10)  # 20
    user.usererweitert.additional_klimapunkte = 5
    user.usererweitert.save()
    cat = ArtikelCategory.objects.create(title="c")
    article = Artikel.objects.create(
        name_de="a", name_en="a", content_de="c", content_en="c", creator=user, category=cat
    )
    article.like.add(other)
    TreeCodes.objects.create(code="c", redeemURL="https://x.de", sponsor="s", planted=True)
    TreeCodes.objects.create(code="d", redeemURL="https://x.de", sponsor="s")
    with django_assert_max_num_queries(6):
        response = client.get("/")
    assert response.context["klimapunkte"] == 25
    assert response.context["user_count"] == 2
    assert response.context["co2"] == 0
    assert response.context["tree_count"] == 1


def test_home_query_count_is_independent_of_user_count(
    client, make_user, action_type, make_aktion, django_assert_max_num_queries
):
    for i in range(15):
        make_aktion(make_user(f"u{i}"), action_type, 1)
    with django_assert_max_num_queries(6):
        client.get("/")


def test_dashboard_redirects_anonymous(client, db):
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert response.url == "/"


def test_dashboard_renders(logged_in, user, levels, category, action_type, make_aktion):
    make_aktion(user, action_type, 30, date=timezone.localdate())
    response = logged_in.get("/dashboard/")
    assert response.status_code == 200
    assert response.context["klimapunkte"] == 60
    assert response.context["level"] == levels[0]
    assert response.context["weekly_goal_progress_percent"] == 300
    assert response.context["perfect_week"] is True
    assert response.context["worldwide_ranking_rank"] == 1


def test_dashboard_without_worldwide_family(logged_in, worldwide, levels):
    worldwide.delete()
    assert logged_in.get("/dashboard/").status_code == 200


def test_dashboard_query_count_is_bounded(
    logged_in, make_user, levels, action_type, make_aktion, django_assert_max_num_queries
):
    for i in range(10):
        make_aktion(make_user(f"p{i}"), action_type, i)
    with django_assert_max_num_queries(25):
        logged_in.get("/dashboard/")


# ---- notifications ------------------------------------------------------------------------


def test_notification_views_require_login(client, db):
    for url in ["/count-benachrichtigungen/", "/benachrichtigungen/", "/delete-benachrichtigung/1/", "/admin/"]:
        assert client.get(url).status_code == 302


def test_notifications_list_and_count(logged_in, user, other):
    Benachrichtigung.objects.create(user=user, benachrichtigung_de="a", benachrichtigung_en="a", url="/x/")
    Benachrichtigung.objects.create(user=other, benachrichtigung_de="b", benachrichtigung_en="b", url="/x/")
    assert logged_in.get("/count-benachrichtigungen/").json() == {"benachrichtigungen_count": 1}
    response = logged_in.get("/benachrichtigungen/")
    assert [n.benachrichtigung_de for n in response.context["benachrichtigungen"]] == ["a"]
    focused = logged_in.get("/benachrichtigungen/7/")
    assert focused.context["benachrichtigungen_id"] == 7


def test_delete_notification(logged_in, user):
    note = Benachrichtigung.objects.create(user=user, benachrichtigung_de="a", benachrichtigung_en="a", url="/x/")
    response = logged_in.get(f"/delete-benachrichtigung/{note.id}/")
    assert response.status_code == 302
    assert flash(response) == [str(all_messages["notification_deleted"])]
    assert not Benachrichtigung.objects.exists()
    again = logged_in.get(f"/delete-benachrichtigung/{note.id}/")
    assert flash(again)[-1] == str(all_messages["delete_notification_error"])


def test_cannot_delete_notification_of_other_user(logged_in, other):
    note = Benachrichtigung.objects.create(user=other, benachrichtigung_de="a", benachrichtigung_en="a", url="/x/")
    response = logged_in.get(f"/delete-benachrichtigung/{note.id}/")
    assert flash(response) == [str(all_messages["delete_notification_error"])]
    assert Benachrichtigung.objects.filter(id=note.id).exists()


# ---- admin notification form ----------------------------------------------------------------


@pytest.fixture
def staff_client(client, staff):
    client.force_login(staff)
    return client


def test_admin_requires_staff(logged_in):
    response = logged_in.get("/admin/")
    assert response.status_code == 302
    assert flash(response) == [str(all_messages["not_authorized_to_visit"])]


def test_admin_form_renders(staff_client):
    assert staff_client.get("/admin/").status_code == 200


def post_admin(client, **overrides):
    data = {"receiver": "user", "name": "alice", "msg_de": "de", "msg_en": "en", "url": ""}
    data.update(overrides)
    with mock.patch("utils.functions.send_push", return_value=200):
        return client.post("/admin/", data)


def test_admin_notifies_single_user(staff_client, user):
    response = post_admin(staff_client)
    assert flash(response) == [str(all_messages["admin__successfully_sent_notification"])]
    assert Benachrichtigung.objects.get(user=user).benachrichtigung_de == "de"


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"msg_de": ""}, "missing_required_inputs"),
        ({"name": ""}, "missing_required_inputs"),
        ({"msg_en": "x" * 501}, "too_long_input"),
        ({"name": "nobody"}, "admin__user_not_found"),
        ({"receiver": "family-members", "name": "nope"}, "admin__family_not_found"),
        ({"receiver": "community-members", "name": "nope"}, "admin__community_not_found"),
        ({"receiver": "event-participants", "name": "999"}, "admin__event_not_found"),
        ({"receiver": "event-participants", "name": "abc"}, "admin__event_not_found"),
        ({"receiver": "bogus"}, "admin__invalid_receiver_type"),
    ],
)
def test_admin_errors(staff_client, user, overrides, key):
    response = post_admin(staff_client, **overrides)
    assert flash(response) == [str(all_messages[key])]
    assert not Benachrichtigung.objects.exists()


def test_admin_missing_fields_does_not_crash(staff_client):
    response = staff_client.post("/admin/", {"receiver": "user"})
    assert flash(response) == [str(all_messages["missing_required_inputs"])]


def test_admin_family_community_and_event_receivers(staff_client, user, other, make_user, staff):
    family = Family.objects.create(name="fam", password="p", admin_password="a")
    family.members.add(user, other)
    second_family = Family.objects.create(name="fam2", password="p", admin_password="a")
    second_family.members.add(user)
    community = Community.objects.create(name="comm", password="p", admin_password="a")
    community.members.add(family, second_family)
    event = Event.objects.create(
        name="e", description="d", adress="a", date_time=timezone.now(), duration=1, creator=staff
    )
    event.participants.add(other)

    post_admin(staff_client, receiver="family-members", name="fam")
    assert Benachrichtigung.objects.count() == 2
    Benachrichtigung.objects.all().delete()

    post_admin(staff_client, receiver="community-members", name="comm")
    # every member user is notified exactly once, even if they are in several families of the community
    assert sorted(Benachrichtigung.objects.values_list("user__username", flat=True)) == ["alice", "bob"]
    Benachrichtigung.objects.all().delete()

    post_admin(staff_client, receiver="event-participants", name=str(event.id), url="/events/")
    note = Benachrichtigung.objects.get()
    assert (note.user, note.url) == (other, "/events/")


def test_base_template_renders_notification_count_without_extra_request(logged_in, user, other):
    """The count is rendered into the page (no separate /count-benachrichtigungen/ request per page view)."""
    response = logged_in.get("/dashboard/")
    assert 'id="benachrichtigungen-count"' not in response.content.decode()  # nothing to show for 0

    Benachrichtigung.objects.create(user=user, benachrichtigung_de="a", benachrichtigung_en="a", url="/x/")
    Benachrichtigung.objects.create(user=user, benachrichtigung_de="b", benachrichtigung_en="b", url="/x/")
    Benachrichtigung.objects.create(user=other, benachrichtigung_de="c", benachrichtigung_en="c", url="/x/")
    html = logged_in.get("/dashboard/").content.decode()
    assert 'id="benachrichtigungen-count" class="count">2</span>' in html
    assert "/count-benachrichtigungen/" not in html


@pytest.mark.django_db
def test_dynamic_pages_are_gzip_compressed(client):
    response = client.get("/", headers={"accept-encoding": "gzip"})
    assert response.headers["Content-Encoding"] == "gzip"
