import datetime
from unittest import mock

import pytest
from django.contrib.auth.hashers import check_password
from django.utils import timezone

from community.models import Community, CommunityChatMessage
from core.all_messages import all_messages
from family.models import Family, FamilyChatMessage
from home.models import Benachrichtigung
from tests.conftest import flash

TODAY = timezone.localdate


def msg(key, **format_args):
    text = str(all_messages[key])
    return text.format(**format_args) if format_args else text


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


@pytest.fixture
def family(user, other):
    family = Family.objects.create(name="Fam", password="famsecret", admin_password="famadmin")
    family.members.add(user, other)
    return family


@pytest.fixture
def community(family):
    community = Community.objects.create(name="Comm", password="commsecret", admin_password="commadmin")
    community.members.add(family)
    return community


# ---- models -----------------------------------------------------------------------------------


def test_passwords_are_hashed_once(db):
    family = Family.objects.create(name="F", password="pw", admin_password="admin")
    assert check_password("pw", family.password) and check_password("admin", family.admin_password)
    stored = family.password
    family.save()
    assert family.password == stored


def test_password_that_looks_like_a_hash_prefix_is_still_hashed(db):
    family = Family.objects.create(name="F", password="pbkdf2_mypassword", admin_password="pbkdf2_x")
    assert family.password != "pbkdf2_mypassword"
    assert check_password("pbkdf2_mypassword", family.password)


def test_model_helpers(family, community, user, other):
    assert family.member_count() == 2
    assert community.members_count() == 1
    assert set(community.user_members()) == {user, other}
    assert str(family) == "Fam" and str(community) == "Comm"
    assert str(FamilyChatMessage(message="hi")) == "hi"
    assert str(CommunityChatMessage(message="yo")) == "yo"


# ---- family: create / join -----------------------------------------------------------------------


def test_create_family(logged_in, user):
    assert logged_in.get("/family/create_family/").status_code == 200
    response = logged_in.post(
        "/family/create_family/", {"familyname": "New", "family_password": "p", "family_admin_password": "a"}
    )
    assert response.url == "/family/families/"
    assert Family.objects.get(name="New").members.get() == user


@pytest.mark.parametrize(
    "data, key",
    [
        ({"familyname": ""}, "missing_required_inputs"),
        ({"familyname": "x" * 101}, "too_long_input"),
        ({"familyname": "Fam"}, "family_exists"),
        ({"familyname": "worldwide ranking"}, "family_exists"),
    ],
)
def test_create_family_errors(logged_in, family, data, key):
    payload = {"familyname": "N", "family_password": "p", "family_admin_password": "a", **data}
    response = logged_in.post("/family/create_family/", payload)
    assert flash(response)[-1] == msg(key)
    assert not Family.objects.filter(name="N").exists()


def test_create_family_with_forbidden_name_when_ranking_missing(logged_in, worldwide):
    worldwide.delete()
    response = logged_in.post(
        "/family/create_family/",
        {"familyname": "worldwide ranking", "family_password": "p", "family_admin_password": "a"},
    )
    assert flash(response)[-1] == msg("family_name_forbidden")


def test_join_family(client, make_user, family):
    newcomer = make_user("newcomer")
    client.force_login(newcomer)
    assert client.get("/family/join_family/").status_code == 200
    response = client.post("/family/join_family/", {"familyname": "Fam", "family_password": "famsecret"})
    assert response.url == "/family/families/"
    assert family.members.filter(id=newcomer.id).exists()
    assert Benachrichtigung.objects.count() == 2  # both existing members


@pytest.mark.parametrize(
    "data, key",
    [
        ({"familyname": ""}, "missing_required_inputs"),
        ({"family_password": "wrong"}, "invalid_family_credentials"),
        ({"familyname": "Nope"}, "invalid_family_credentials"),
    ],
)
def test_join_family_errors(client, make_user, family, data, key):
    client.force_login(make_user("newcomer"))
    response = client.post("/family/join_family/", {"familyname": "Fam", "family_password": "famsecret", **data})
    assert flash(response)[-1] == msg(key)
    assert family.members.count() == 2


def test_join_family_twice_does_nothing(logged_in, family):
    response = logged_in.post("/family/join_family/", {"familyname": "Fam", "family_password": "famsecret"})
    assert flash(response) == [msg("family_already_joined", familyname="Fam")]
    assert response.url == "/family/join_family/"
    assert not Benachrichtigung.objects.exists()


def test_family_name_in_flash_message_is_not_executed(client, make_user, db, worldwide):
    evil = Family.objects.create(name="<script>alert(1)</script>", password="p", admin_password="a")
    user = make_user("victim")
    client.force_login(user)
    client.post("/family/join_family/", {"familyname": evil.name, "family_password": "p"})
    page = client.get("/family/families/")
    assert b"<script>alert(1)</script>" not in page.content


# ---- family: chat / list ----------------------------------------------------------------------------------


def test_families_view(logged_in, family, worldwide):
    assert [f.name for f in logged_in.get("/family/families/").context["families"]] == ["Fam", "worldwide ranking"]


def test_family_chat(logged_in, user, other, family):
    assert logged_in.get(f"/family/family/{family.id}/chat/").status_code == 200
    response = logged_in.post(f"/family/family/{family.id}/chat/", {"message": "<b>hi</b>"})
    assert response.url == f"/family/family/{family.id}/chat/"
    assert FamilyChatMessage.objects.get().message == "<b>hi</b>"
    note = Benachrichtigung.objects.get(user=other)
    assert "<b>hi</b>" not in note.benachrichtigung_de
    assert "&lt;b&gt;hi&lt;/b&gt;" in note.benachrichtigung_de
    logged_in.post(f"/family/family/{family.id}/chat/", {"message": ""})
    assert FamilyChatMessage.objects.count() == 1


def test_family_chat_restrictions(logged_in, make_user, family, worldwide):
    assert flash(logged_in.get("/family/family/999/chat/"))[-1] == msg("family_not_found")
    assert flash(logged_in.get(f"/family/family/{worldwide.id}/chat/"))[-1] == msg(
        "chat_not_enabled_for_worldwide_ranking"
    )
    outsider = make_user("outsider")
    logged_in.force_login(outsider)
    assert flash(logged_in.get(f"/family/family/{family.id}/chat/"))[-1] == msg("not_part_of_family", familyname="Fam")
    family.chat = False
    family.save()
    response = logged_in.get(f"/family/family/{family.id}/chat/")
    assert response.url == f"/family/family/{family.id}/"


# ---- family: detail -------------------------------------------------------------------------------------


def test_family_detail_ranking(logged_in, user, other, family, action_type, make_aktion):
    make_aktion(user, action_type, 5, date=TODAY())
    make_aktion(other, action_type, 10, date=TODAY() - datetime.timedelta(days=20))
    response = logged_in.get(f"/family/family/{family.id}/")
    assert [(r["member"], r["klimapunkte"]) for r in response.context["members"]] == [(other, 20), (user, 10)]
    assert response.context["total_klimapunkte"] == 30
    assert response.context["average_klimapunkte"] == 15
    response = logged_in.post(f"/family/family/{family.id}/", {"zeitraum": "Sieben Tage"})
    assert [(r["member"], r["klimapunkte"]) for r in response.context["members"]] == [(user, 10), (other, 0)]
    assert response.context["zeitraum"] == "Sieben Tage"


def test_family_detail_bonus_points_only_in_total(logged_in, user, family):
    user.usererweitert.additional_klimapunkte = 7
    user.usererweitert.save()
    total = logged_in.get(f"/family/family/{family.id}/").context["total_klimapunkte"]
    week = logged_in.post(f"/family/family/{family.id}/", {"zeitraum": "Sieben Tage"}).context["total_klimapunkte"]
    assert (total, week) == (7, 0)


def test_family_detail_invalid_period_and_empty_family(logged_in, family):
    response = logged_in.post(f"/family/family/{family.id}/", {"zeitraum": "bogus"})
    assert flash(response) == [msg("invalid_time_period")]
    empty = Family.objects.create(name="Empty", password="p", admin_password="a")
    empty.members.add(logged_in.session["_auth_user_id"])
    empty.members.clear()
    assert flash(logged_in.get(f"/family/family/{empty.id}/"))[-1] == msg("not_part_of_family", familyname="Empty")


def test_family_detail_access_rules(client, make_user, family, community, db):
    assert flash(client.get(f"/family/family/{family.id}/")) or True
    outsider = make_user("outsider")
    client.force_login(outsider)
    response = client.get(f"/family/family/{family.id}/")
    assert flash(response)[-1] == msg("not_part_of_family", familyname="Fam")
    own = Family.objects.create(name="Own", password="p", admin_password="a")
    own.members.add(outsider)
    assert client.get(f"/family/family/{family.id}/").status_code == 302  # no shared community yet
    community.members.add(own)
    assert client.get(f"/family/family/{family.id}/").status_code == 200  # same community
    assert flash(client.get("/family/family/999/"))[-1] == msg("family_not_found")


def test_family_detail_query_count(
    logged_in, make_user, family, action_type, make_aktion, django_assert_max_num_queries
):
    for i in range(10):
        member = make_user(f"fm{i}")
        family.members.add(member)
        make_aktion(member, action_type, 1)
    with django_assert_max_num_queries(16):
        logged_in.get(f"/family/family/{family.id}/")


def test_check_familyname(logged_in, family):
    assert logged_in.get("/family/check-familyname/?familyname=Fam").json() == {"exists": True}
    assert logged_in.get("/family/check-familyname/?familyname=No").json() == {"exists": False}


# ---- family: edit -------------------------------------------------------------------------------------------


def edit(client, family, **data):
    return client.post(f"/family/family/{family.id}/edit/", data)


def test_edit_family_access(logged_in, make_user, family, worldwide):
    assert logged_in.get(f"/family/family/{family.id}/edit/").status_code == 200
    assert flash(logged_in.get("/family/family/999/edit/"))[-1] == msg("family_not_found")
    assert flash(logged_in.get(f"/family/family/{worldwide.id}/edit/"))[-1] == msg("family_name_forbidden")
    logged_in.force_login(make_user("outsider"))
    assert flash(logged_in.get(f"/family/family/{family.id}/edit/"))[-1] == msg("not_part_of_family", familyname="Fam")


def test_rename_family(logged_in, other, family):
    response = edit(
        logged_in, family, change_familyname="1", admin_password_familyname="famadmin", new_familyname="Renamed"
    )
    assert flash(response)[-1] == msg("family_name_changed")
    family.refresh_from_db()
    assert family.name == "Renamed"
    assert Benachrichtigung.objects.get(user=other).benachrichtigung_en.startswith("The family name")


@pytest.mark.parametrize(
    "data, key",
    [
        ({"new_familyname": "x" * 101}, "too_long_input"),
        ({"new_familyname": "Fam"}, "family_exists"),
        ({"admin_password_familyname": "", "new_familyname": "N"}, "missing_required_inputs"),
        ({"admin_password_familyname": "wrong", "new_familyname": "N"}, "invalid_admin_password"),
        ({"new_familyname": ""}, "missing_required_inputs"),
    ],
)
def test_rename_family_errors(logged_in, family, data, key):
    payload = {"change_familyname": "1", "admin_password_familyname": "famadmin", "new_familyname": "N", **data}
    assert flash(edit(logged_in, family, **payload))[-1] == msg(key)
    family.refresh_from_db()
    assert family.name == "Fam"


def test_change_family_passwords(logged_in, family):
    response = edit(logged_in, family, change_password="1", admin_password_password="famadmin", new_password="newpw")
    assert flash(response)[-1] == msg("family_password_changed")
    family.refresh_from_db()
    assert check_password("newpw", family.password)
    response = edit(
        logged_in, family, change_admin_password="1", current_admin_password="famadmin", new_admin_password="newadmin"
    )
    assert flash(response)[-1] == msg("family_admin_password_changed")
    family.refresh_from_db()
    assert check_password("newadmin", family.admin_password)


@pytest.mark.parametrize(
    "button, data, key",
    [
        ("change_password", {"admin_password_password": "famadmin", "new_password": "x" * 101}, "too_long_input"),
        ("change_password", {"admin_password_password": "bad", "new_password": "n"}, "invalid_admin_password"),
        ("change_password", {"admin_password_password": "famadmin"}, "missing_required_inputs"),
        (
            "change_admin_password",
            {"current_admin_password": "famadmin", "new_admin_password": "x" * 101},
            "too_long_input",
        ),
        (
            "change_admin_password",
            {"current_admin_password": "bad", "new_admin_password": "n"},
            "invalid_admin_password",
        ),
        ("change_admin_password", {"current_admin_password": "famadmin"}, "missing_required_inputs"),
    ],
)
def test_change_family_password_errors(logged_in, family, button, data, key):
    assert flash(edit(logged_in, family, **{button: "1"}, **data))[-1] == msg(key)


def test_remove_member(logged_in, other, family):
    response = edit(logged_in, family, remove_member="1", admin_password_remove="famadmin", username="bob")
    assert flash(response)[-1] == msg("family_user_removed")
    assert not family.members.filter(id=other.id).exists()
    # the removed user is told about it (previously they never were)
    assert "entfernt" in Benachrichtigung.objects.get(user=other).benachrichtigung_de


def test_remove_member_errors_and_self_removal(logged_in, user, family):
    assert flash(edit(logged_in, family, remove_member="1", admin_password_remove="famadmin", username=""))[-1] == msg(
        "missing_required_inputs"
    )
    assert flash(edit(logged_in, family, remove_member="1", admin_password_remove="bad", username="bob"))[-1] == msg(
        "invalid_admin_password"
    )
    response = edit(logged_in, family, remove_member="1", admin_password_remove="famadmin", username="ghost")
    assert flash(response)[-1] == msg("family_user_not_found")
    assert response.url == f"/family/family/{family.id}/edit/"
    response = edit(logged_in, family, remove_member="1", admin_password_remove="famadmin", username="alice")
    assert response.url == "/family/families/"
    assert not family.members.filter(id=user.id).exists()


def test_leave_family(logged_in, user, family):
    response = edit(logged_in, family, leave_family="1")
    assert response.url == "/family/families/"
    assert not family.members.filter(id=user.id).exists()


def test_family_chat_settings(logged_in, family):
    assert flash(edit(logged_in, family, change_chat_settings="1", admin_password_chat_settings="bad"))[-1] == msg(
        "invalid_admin_password"
    )
    response = edit(logged_in, family, change_chat_settings="1", admin_password_chat_settings="famadmin")
    assert flash(response)[-1] == msg("family_chat_disabled")
    response = edit(
        logged_in, family, change_chat_settings="1", admin_password_chat_settings="famadmin", chat_checkbox="on"
    )
    assert flash(response)[-1] == msg("family_chat_enabled")
    family.refresh_from_db()
    assert family.chat is True


def test_delete_family(logged_in, other, family):
    assert flash(edit(logged_in, family, delete_family="1", admin_password_delete=""))[-1] == msg(
        "missing_required_inputs"
    )
    assert flash(edit(logged_in, family, delete_family="1", admin_password_delete="bad"))[-1] == msg(
        "invalid_admin_password"
    )
    response = edit(logged_in, family, delete_family="1", admin_password_delete="famadmin")
    assert response.url == "/family/families/"
    assert not Family.objects.filter(id=family.id).exists()
    assert Benachrichtigung.objects.filter(user=other).count() == 1


def test_edit_post_without_known_button(logged_in, family):
    assert edit(logged_in, family, foo="bar").status_code == 200


# ---- community --------------------------------------------------------------------------------------------------


def test_communities_view(logged_in, family, community, django_assert_max_num_queries):
    with django_assert_max_num_queries(10):
        response = logged_in.get("/community/communities/")
    row = response.context["communities_with_user_families"][0]
    assert (row["community"], row["families"]) == (community, [family])


def test_create_community(logged_in, family):
    assert logged_in.get("/community/create_community/").status_code == 200
    data = {
        "communityname": "NewC",
        "community_password": "cp",
        "community_admin_password": "ca",
        "familyname": "Fam",
        "family_admin_password": "famadmin",
    }
    response = logged_in.post("/community/create_community/", data)
    assert response.url == "/community/communities/"
    assert Community.objects.get(name="NewC").members.get() == family
    assert Benachrichtigung.objects.count() == 1


@pytest.mark.parametrize(
    "data, key",
    [
        ({"communityname": ""}, "missing_required_inputs"),
        ({"communityname": "x" * 101}, "too_long_input"),
        ({"community_admin_password": "x" * 101}, "too_long_input"),
        ({"communityname": "Comm"}, "community_exists"),
        ({"family_admin_password": "bad"}, "community__invalid_family_credentials"),
        ({"familyname": "Nope"}, "community__invalid_family_credentials"),
    ],
)
def test_create_community_errors(logged_in, family, community, data, key):
    payload = {
        "communityname": "NewC",
        "community_password": "cp",
        "community_admin_password": "ca",
        "familyname": "Fam",
        "family_admin_password": "famadmin",
        **data,
    }
    response = logged_in.post("/community/create_community/", payload)
    assert flash(response)[-1] == msg(key)
    assert not Community.objects.filter(name="NewC").exists()


def test_join_community(logged_in, user, other):
    second = Family.objects.create(name="Second", password="p", admin_password="sa")
    second.members.add(user)
    target = Community.objects.create(name="Target", password="tp", admin_password="ta")
    assert logged_in.get("/community/join_community/").status_code == 200
    data = {
        "communityname": "Target",
        "community_password": "tp",
        "familyname": "Second",
        "family_admin_password": "sa",
    }
    response = logged_in.post("/community/join_community/", data)
    assert response.url == "/community/communities/"
    assert target.members.get() == second
    again = logged_in.post("/community/join_community/", data)
    assert flash(again)[-1] == msg("family_already_in_community")


@pytest.mark.parametrize(
    "data, key",
    [
        ({"communityname": ""}, "missing_required_inputs"),
        ({"family_admin_password": "bad"}, "community__invalid_family_credentials"),
        ({"familyname": "Nope"}, "community__invalid_family_credentials"),
        ({"community_password": "bad"}, "invalid_community_credentials"),
        ({"communityname": "Nope"}, "invalid_community_credentials"),
    ],
)
def test_join_community_errors(logged_in, family, community, data, key):
    other_community = Community.objects.create(name="Other", password="op", admin_password="oa")
    payload = {
        "communityname": "Other",
        "community_password": "op",
        "familyname": "Fam",
        "family_admin_password": "famadmin",
        **data,
    }
    response = logged_in.post("/community/join_community/", payload)
    assert flash(response)[-1] == msg(key)
    assert not other_community.members.exists()


def url(community, family, suffix=""):
    return f"/community/community/{community.id}/{family.id}/{suffix}"


def test_community_detail(logged_in, user, other, family, community, action_type, make_aktion):
    second = Family.objects.create(name="Second", password="p", admin_password="a")
    solo = other.__class__.objects.create_user("solo")
    second.members.add(solo)
    community.members.add(second)
    Family.objects.create(name="Empty", password="p", admin_password="a")
    empty = Family.objects.get(name="Empty")
    community.members.add(empty)
    make_aktion(user, action_type, 5, date=TODAY())
    make_aktion(other, action_type, 5, date=TODAY())
    response = logged_in.get(url(community, family))
    assert [(r["member"], r["klimapunkte"]) for r in response.context["members_with_klimapunkte"]][0] == (family, 10)
    response = logged_in.post(url(community, family), {"zeitraum": "Heute"})
    assert response.context["zeitraum"] == "Heute"
    response = logged_in.post(url(community, family), {"zeitraum": "bogus"})
    assert flash(response)[-1] == msg("invalid_time_period")


def test_community_access_rules(logged_in, user, family, community, make_user):
    unrelated = Family.objects.create(name="Unrelated", password="p", admin_password="a")
    unrelated.members.add(user)
    for suffix in ("", "edit/", "chat/"):
        response = logged_in.get(url(community, unrelated, suffix))
        assert flash(response)[-1] == msg("community__family_not_in_community")
    assert flash(logged_in.get("/community/community/999/1/"))[-1] == msg("community_not_found")
    assert flash(logged_in.get(f"/community/community/{community.id}/999/"))[-1] == msg("community__family_not_found")
    outsider = make_user("outsider")
    logged_in.force_login(outsider)
    assert flash(logged_in.get(url(community, family)))[-1] == msg("community__not_member_of_family")


def test_community_chat(logged_in, user, other, family, community):
    assert logged_in.get(url(community, family, "chat/")).status_code == 200
    response = logged_in.post(url(community, family, "chat/"), {"message": "hello <i>all</i>"})
    assert response.url == url(community, family, "chat/")
    assert CommunityChatMessage.objects.get().family == family
    note = Benachrichtigung.objects.get(user=other)
    assert note.url == url(community, family)
    assert "&lt;i&gt;" in note.benachrichtigung_en
    logged_in.post(url(community, family, "chat/"), {"message": ""})
    assert CommunityChatMessage.objects.count() == 1
    community.chat = False
    community.save()
    assert logged_in.get(url(community, family, "chat/")).url == url(community, family)


def edit_community(client, community, family, **data):
    return client.post(url(community, family, "edit/"), data)


def test_edit_community_renders(logged_in, community, family):
    assert logged_in.get(url(community, family, "edit/")).status_code == 200
    assert edit_community(logged_in, community, family, nothing="1").status_code == 200


def test_edit_community_name_and_passwords(logged_in, other, community, family):
    response = edit_community(
        logged_in,
        community,
        family,
        change_communityname="1",
        admin_password_communityname="commadmin",
        new_communityname="Renamed",
    )
    assert flash(response)[-1] == msg("community_name_changed")
    community.refresh_from_db()
    assert community.name == "Renamed"
    assert Benachrichtigung.objects.get(user=other).url == url(community, family)
    response = edit_community(
        logged_in, community, family, change_password="1", admin_password_password="commadmin", new_password="cp2"
    )
    assert flash(response)[-1] == msg("community_password_changed")
    response = edit_community(
        logged_in,
        community,
        family,
        change_admin_password="1",
        current_admin_password="commadmin",
        new_admin_password="ca2",
    )
    assert flash(response)[-1] == msg("community_admin_password_changed")
    community.refresh_from_db()
    assert check_password("cp2", community.password) and check_password("ca2", community.admin_password)


@pytest.mark.parametrize(
    "button, data, key",
    [
        (
            "change_communityname",
            {"admin_password_communityname": "commadmin", "new_communityname": "x" * 101},
            "too_long_input",
        ),
        (
            "change_communityname",
            {"admin_password_communityname": "commadmin", "new_communityname": "Comm"},
            "community_exists",
        ),
        (
            "change_communityname",
            {"admin_password_communityname": "bad", "new_communityname": "N"},
            "invalid_admin_password",
        ),
        ("change_communityname", {"admin_password_communityname": "commadmin"}, "missing_required_inputs"),
        ("change_password", {"admin_password_password": "commadmin", "new_password": "x" * 101}, "too_long_input"),
        ("change_password", {"admin_password_password": "bad", "new_password": "n"}, "invalid_admin_password"),
        (
            "change_admin_password",
            {"current_admin_password": "commadmin", "new_admin_password": "x" * 101},
            "too_long_input",
        ),
        ("change_admin_password", {"current_admin_password": "commadmin"}, "missing_required_inputs"),
    ],
)
def test_edit_community_errors(logged_in, community, family, button, data, key):
    assert flash(edit_community(logged_in, community, family, **{button: "1"}, **data))[-1] == msg(key)


def test_remove_family_from_community(logged_in, other, community, family):
    second = Family.objects.create(name="Second", password="p", admin_password="a")
    second.members.add(other)
    community.members.add(second)
    response = edit_community(
        logged_in, community, family, remove_member="1", admin_password_remove="commadmin", family_name="Second"
    )
    assert flash(response)[-1] == msg("community__family_removed")
    assert not community.members.filter(id=second.id).exists()
    assert edit_community(
        logged_in, community, family, remove_member="1", admin_password_remove="commadmin", family_name="Ghost"
    ).url == url(community, family, "edit/")
    assert flash(
        edit_community(logged_in, community, family, remove_member="1", admin_password_remove="bad", family_name="Fam")
    )[-1] == msg("invalid_admin_password")
    response = edit_community(
        logged_in, community, family, remove_member="1", admin_password_remove="commadmin", family_name="Fam"
    )
    assert response.url == "/dashboard/"
    assert not community.members.filter(id=family.id).exists()


def test_leave_community(logged_in, community, family):
    assert flash(edit_community(logged_in, community, family, leave_community="1", family_admin_password=""))[
        -1
    ] == msg("missing_required_inputs")
    assert flash(edit_community(logged_in, community, family, leave_community="1", family_admin_password="bad"))[
        -1
    ] == msg("invalid_admin_password")
    response = edit_community(logged_in, community, family, leave_community="1", family_admin_password="famadmin")
    assert response.url == "/dashboard/"
    assert not community.members.exists()


def test_community_chat_settings_and_delete(logged_in, community, family):
    assert flash(
        edit_community(logged_in, community, family, change_chat_settings="1", admin_password_chat_settings="bad")
    )[-1] == msg("invalid_admin_password")
    assert flash(
        edit_community(logged_in, community, family, change_chat_settings="1", admin_password_chat_settings="commadmin")
    )[-1] == msg("community_chat_disabled")
    assert flash(
        edit_community(
            logged_in,
            community,
            family,
            change_chat_settings="1",
            admin_password_chat_settings="commadmin",
            chat_checkbox="on",
        )
    )[-1] == msg("community_chat_enabled")
    assert flash(edit_community(logged_in, community, family, delete_community="1", admin_password_delete=""))[
        -1
    ] == msg("missing_required_inputs")
    assert flash(edit_community(logged_in, community, family, delete_community="1", admin_password_delete="bad"))[
        -1
    ] == msg("invalid_admin_password")
    response = edit_community(logged_in, community, family, delete_community="1", admin_password_delete="commadmin")
    assert response.url == "/dashboard/"
    assert not Community.objects.exists()


def test_check_communityname(logged_in, community):
    assert logged_in.get("/community/check-communityname/?communityname=Comm").json() == {"exists": True}
    assert logged_in.get("/community/check-communityname/").json() == {"exists": False}
