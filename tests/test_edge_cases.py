"""Branches that the feature tests do not reach: defensive code paths and data without optional parts."""

from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from aktionen.models import Category
from artikel.models import Artikel
from artikel.models import Category as ArtikelCategory
from core.all_messages import all_messages
from events.models import Event
from forum.models import Category as ForumCategory
from forum.models import ForumPost
from petitions.models import Answer as PetitionAnswer
from petitions.models import Category as PetitionCategory
from tests.conftest import flash
from tests.test_utils_functions import make_request
from utils import functions as fn


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


def test_all_sitemaps_with_data(db, user, worldwide, client):
    from django.utils import translation

    from ClimateQuest.urls import sitemaps

    translation.activate("de")
    artikel = Artikel.objects.create(
        name_de="a",
        name_en="a",
        content_de="c",
        content_en="c",
        creator=user,
        category=ArtikelCategory.objects.create(title="c"),
    )
    event = Event.objects.create(
        name="e", description="d", adress="a", date_time=timezone.now(), duration=1, creator=user
    )
    post = ForumPost.objects.create(
        title="t", content="c", creator=user, category=ForumCategory.objects.create(title="c")
    )
    for sitemap in sitemaps.values():
        for item in sitemap.items():
            assert sitemap.location(item).startswith("/de/")
            if hasattr(sitemap, "lastmod"):
                sitemap.lastmod(item)
    assert sitemaps["artikel_detail"].location(artikel).endswith(f"/{artikel.id}")
    assert sitemaps["event_detail"].location(event)
    assert sitemaps["forum_post_detail"].location(post)
    assert client.get("/sitemap.xml").status_code == 200


def test_send_mail_without_user_is_reported():
    with mock.patch("utils.functions.create_internal_error") as error:
        assert fn.send_mail_function(request=None, subject="s", message="m") is False
    error.assert_called_once()


def test_send_mail_for_user_without_profile(db):
    user = User.objects.create_user("bare", email="b@x.de")
    with mock.patch("utils.functions.create_internal_error") as error:
        assert fn.send_mail_function(request=make_request(user), subject="s", message="m", user=user) is False
    error.assert_called_once()


def test_create_internal_error_without_request(tmp_path, settings):
    settings.LOGS_DIR = tmp_path
    fn.create_internal_error(None, "no request here")
    assert "no request here" in (tmp_path / "errors.log").read_text()


def test_points_by_user_include_article_likes(user, other):
    article = Artikel.objects.create(
        name_de="a",
        name_en="a",
        content_de="c",
        content_en="c",
        creator=user,
        category=ArtikelCategory.objects.create(title="c"),
    )
    article.like.add(other)
    assert fn.get_klimapunkte_by_user([user.id, other.id]) == {user.id: pytest.approx(0.1), other.id: 0}
    assert fn.get_klimapunkte_by_user([user.id], include_additional=False) == {user.id: 0}


def test_parse_id():
    assert fn.parse_id("12") == 12
    for bad in (None, "", "-1", "1.5", "abc", "١٢"):
        assert fn.parse_id(bad) is None


def test_statistics_ignores_actions_without_category(logged_in, user, action_type, make_aktion):
    action_type.category = None
    action_type.save()
    make_aktion(user, action_type, 1)
    Category.objects.create(name="Essen", name_en="Food")
    response = logged_in.get("/personals/statistics/")
    assert response.status_code == 200
    assert b"Essen" in response.content


def test_overview_with_specific_category(logged_in, db):
    PetitionCategory.objects.create(title="Umwelt")
    response = logged_in.post("/petitions/petitions_overview/", {"category": "Umwelt", "order_by": "Titel"})
    assert response.status_code == 200 and response.context["category"] == "Umwelt"


def test_petition_answer_str(user):
    assert str(PetitionAnswer(answer="yes", user=user)) == "yes"


def test_action_detail_access_checks(logged_in, other, make_user):
    private = make_user("private", allows_data_view=False)
    response = logged_in.get(f"/users/action_detail/1/{private.id}/")
    assert response.status_code == 302
    assert flash(response)[-1] == str(all_messages["user_blocked_view"])
