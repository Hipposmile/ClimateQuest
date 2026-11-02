"""Articles, events, forum and petitions share the same patterns (overview, detail, comments, edit)."""

import datetime
from unittest import mock

import pytest
from django.utils import timezone

from artikel.models import Answer as ArtikelAnswer
from artikel.models import Artikel
from artikel.models import Category as ArtikelCategory
from artikel.models import Comment as ArtikelComment
from core.all_messages import all_messages
from events.models import Answer as EventAnswer
from events.models import Event, Question
from forum.models import Answer as ForumAnswer
from forum.models import Category as ForumCategory
from forum.models import ForumPost
from home.models import Benachrichtigung
from petitions.models import Category as PetitionCategory
from petitions.models import Comment as PetitionComment
from petitions.models import Petition, Update
from tests.conftest import flash


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


def msg(key):
    return str(all_messages[key])


# ======================================= articles =======================================


@pytest.fixture
def artikel_category(db):
    return ArtikelCategory.objects.create(title="Klima")


@pytest.fixture
def artikel(user, artikel_category):
    return Artikel.objects.create(
        name_de="Alpha",
        name_en="Alpha en",
        content_de="<p>de</p>",
        content_en="<p>en</p>",
        creator=user,
        category=artikel_category,
    )


def artikel_form(**overrides):
    data = {
        "is_truth": "on",
        "name_de": "N",
        "name_en": "N en",
        "content_de": "<p>d</p>",
        "content_en": "<p>e</p>",
        "category": "Klima",
    }
    data.update(overrides)
    return data


def test_artikel_overview_get(client, artikel, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        response = client.get("/artikel/artikel_overview/")
    assert list(response.context["artikel"]) == [artikel]


def test_artikel_overview_queries_do_not_grow(client, user, other, artikel_category, django_assert_max_num_queries):
    for i in range(12):
        a = Artikel.objects.create(
            name_de=f"A{i}", name_en=f"A{i}", content_de="c", content_en="c", creator=user, category=artikel_category
        )
        a.like.add(other)
    with django_assert_max_num_queries(6):
        client.get("/artikel/artikel_overview/")


@pytest.mark.parametrize(
    "order, keyword, expected",
    [
        ("Name", "", ["Alpha", "Beta"]),
        ("Name", "bet", ["Beta"]),
        ("Ersteller", "bob", ["Beta"]),
        ("Zuletzt bearbeitet", "", ["Alpha", "Beta"]),
        ("Zuletzt bearbeitet", "1999", []),
        ("Likes", "", ["Beta", "Alpha"]),
        ("Likes", "1", ["Beta"]),
        ("unknown", "", ["Alpha", "Beta"]),
    ],
)
def test_artikel_overview_post(client, user, other, artikel, artikel_category, order, keyword, expected):
    beta = Artikel.objects.create(
        name_de="Beta", name_en="Beta", content_de="c", content_en="c", creator=other, category=artikel_category
    )
    beta.like.add(user)
    response = client.post(
        "/artikel/artikel_overview/", {"category": "Alle", "order_by": order, "search_keyword": keyword}
    )
    assert [a.name_de for a in response.context["artikel"]] == expected


def test_artikel_overview_mine_and_liked(logged_in, user, other, artikel, artikel_category):
    other_artikel = Artikel.objects.create(
        name_de="Zed", name_en="Zed", content_de="c", content_en="c", creator=other, category=artikel_category
    )
    other_artikel.like.add(user)
    mine = logged_in.post("/artikel/artikel_overview/", {"category": "Alle", "order_by": "von mir erstellte Artikel"})
    assert [a.name_de for a in mine.context["artikel"]] == ["Alpha"]
    liked = logged_in.post("/artikel/artikel_overview/", {"category": "Alle", "order_by": "von mir gelikte Artikel"})
    assert [a.name_de for a in liked.context["artikel"]] == ["Zed"]
    wrong_category = logged_in.post(
        "/artikel/artikel_overview/", {"category": "Other", "order_by": "von mir gelikte Artikel"}
    )
    assert list(wrong_category.context["artikel"]) == []


@pytest.mark.parametrize("order", ["von mir erstellte Artikel", "von mir gelikte Artikel"])
def test_artikel_overview_personal_filters_for_anonymous_users(client, artikel, order):
    response = client.post("/artikel/artikel_overview/", {"category": "Alle", "order_by": order})
    assert response.status_code == 200
    assert list(response.context["artikel"]) == []


def test_artikel_overview_english_and_invalid_like_search(en_client, artikel):
    response = en_client.post(
        "/artikel/artikel_overview/", {"category": "Klima", "order_by": "Name", "search_keyword": "en"}
    )
    assert [a.name_en for a in response.context["artikel"]] == ["Alpha en"]
    response = en_client.post(
        "/artikel/artikel_overview/", {"category": "Alle", "order_by": "Likes", "search_keyword": "abc"}
    )
    assert flash(response) == [msg("likes_search_keyword_not_a_number")]


def test_add_artikel(logged_in, user, artikel_category):
    assert logged_in.get("/artikel/add_artikel/").status_code == 200
    response = logged_in.post("/artikel/add_artikel/", artikel_form(content_de="<p>hi</p><script>x</script>"))
    created = Artikel.objects.get()
    assert response.url == f"/artikel/artikel_detail/{created.id}"
    assert created.creator == user and "<script" not in created.content_de


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"is_truth": ""}, "not_is_truth"),
        ({"name_de": ""}, "missing_required_inputs"),
        ({"name_de": "x" * 101}, "too_long_input"),
        ({"category": "Nope"}, "internal_error"),
    ],
)
def test_add_artikel_errors(logged_in, artikel_category, overrides, key):
    response = logged_in.post("/artikel/add_artikel/", artikel_form(**overrides))
    assert flash(response) == [msg(key)]
    assert not Artikel.objects.exists()


def test_add_artikel_missing_fields_does_not_crash(logged_in, artikel_category):
    response = logged_in.post("/artikel/add_artikel/", {"is_truth": "on", "category": "Klima"})
    assert flash(response) == [msg("missing_required_inputs")]


def test_edit_artikel(logged_in, artikel, other):
    assert logged_in.get(f"/artikel/edit_artikel/{artikel.id}").status_code == 200
    response = logged_in.post(
        f"/artikel/edit_artikel/{artikel.id}", {"edit_artikel": "1", **artikel_form(name_de="Changed")}
    )
    artikel.refresh_from_db()
    assert artikel.name_de == "Changed"
    assert flash(response)[-1] == msg("successfully_edited_artikel")
    bad = logged_in.post(f"/artikel/edit_artikel/{artikel.id}", {"edit_artikel": "1", **artikel_form(name_de="")})
    assert flash(bad)[-1] == msg("missing_required_inputs")
    assert logged_in.post(f"/artikel/edit_artikel/{artikel.id}", {"unknown": "1"}).status_code == 200
    deleted = logged_in.post(f"/artikel/edit_artikel/{artikel.id}", {"delete_artikel": "1"})
    assert deleted.url == "/artikel/artikel_overview/"
    assert not Artikel.objects.exists()


def test_edit_artikel_permissions(logged_in, other, artikel_category):
    foreign = Artikel.objects.create(
        name_de="F", name_en="F", content_de="c", content_en="c", creator=other, category=artikel_category
    )
    response = logged_in.post(f"/artikel/edit_artikel/{foreign.id}", {"delete_artikel": "1"})
    assert flash(response) == [msg("not_authorized_to_visit")]
    assert Artikel.objects.filter(id=foreign.id).exists()
    assert flash(logged_in.get("/artikel/edit_artikel/999"))[-1] == msg("artikel_not_existing")


def test_artikel_detail_and_comments(logged_in, user, other, artikel, django_assert_max_num_queries):
    comment = ArtikelComment.objects.create(comment="c", user=other)
    comment.answers.add(ArtikelAnswer.objects.create(answer="a", user=user))
    artikel.comments.add(comment)
    with django_assert_max_num_queries(12):
        response = logged_in.get(f"/artikel/artikel_detail/{artikel.id}")
    assert response.context["has_liked"] is False
    response = logged_in.post(f"/artikel/artikel_detail/{artikel.id}", {"add_comment": "1", "comment": "  hello  "})
    assert flash(response)[-1] == msg("successfully_asked_comment")
    assert artikel.comments.filter(comment="hello").exists()
    response = logged_in.post(
        f"/artikel/artikel_detail/{artikel.id}", {"answer_comment": "1", "comment_id": comment.id, "answer": "reply"}
    )
    assert flash(response)[-1] == msg("successfully_answered_comment")
    assert comment.answers.count() == 2


def test_artikel_detail_validation(logged_in, artikel, other):
    assert flash(logged_in.post(f"/artikel/artikel_detail/{artikel.id}", {"add_comment": "1", "comment": "  "}))[
        -1
    ] == msg("missing_required_inputs")
    assert flash(logged_in.post(f"/artikel/artikel_detail/{artikel.id}", {"add_comment": "1"}))[-1] == msg(
        "missing_required_inputs"
    )
    foreign_comment = ArtikelComment.objects.create(comment="elsewhere", user=other)
    response = logged_in.post(
        f"/artikel/artikel_detail/{artikel.id}",
        {"answer_comment": "1", "comment_id": foreign_comment.id, "answer": "x"},
    )
    assert response.url == f"/artikel/artikel_detail/{artikel.id}"
    assert flash(response)[-1] == msg("internal_error")
    assert not foreign_comment.answers.exists()
    for comment_id in ("999", "abc", ""):
        response = logged_in.post(
            f"/artikel/artikel_detail/{artikel.id}", {"answer_comment": "1", "comment_id": comment_id, "answer": "x"}
        )
        assert flash(response)[-1] == msg("internal_error")
    own = ArtikelComment.objects.create(comment="own", user=other)
    artikel.comments.add(own)
    response = logged_in.post(
        f"/artikel/artikel_detail/{artikel.id}", {"answer_comment": "1", "comment_id": own.id, "answer": ""}
    )
    assert flash(response)[-1] == msg("missing_required_inputs")


def test_artikel_detail_anonymous_and_missing(client, artikel):
    assert (
        client.post(f"/artikel/artikel_detail/{artikel.id}", {"add_comment": "1", "comment": "hi"}).status_code == 200
    )
    assert not artikel.comments.exists()
    response = client.get("/artikel/artikel_detail/999")
    assert flash(response) == [msg("artikel_not_existing")]


def test_artikel_detail_unknown_post(logged_in, artikel):
    assert logged_in.post(f"/artikel/artikel_detail/{artikel.id}", {"foo": "1"}).status_code == 200


def test_artikel_moderation(client, staff, artikel):
    client.force_login(staff)
    url = f"/artikel/artikel_detail/{artikel.id}"
    assert flash(client.post(url, {"verify": "1"}))[-1] == msg("successfully_verified_article")
    artikel.refresh_from_db()
    assert artikel.verified
    assert flash(client.post(url, {"verify": "1"}))[-1] == msg("successfully_unverified_article")
    assert flash(client.post(url, {"block": "1"}))[-1] == msg("successfully_blocked_article")
    artikel.refresh_from_db()
    assert artikel.blocked and artikel.msg_if_wrong == "Dieser Artikel enthält Fake News"
    assert flash(client.post(url, {"block": "1"}))[-1] == msg("successfully_unblocked_article")
    client.post(url, {"block": "1", "block_msg": "wrong!"})
    artikel.refresh_from_db()
    assert artikel.msg_if_wrong == "wrong!"
    client.post(url, {"verify": "1"})
    artikel.refresh_from_db()
    assert artikel.verified and not artikel.blocked


def test_non_staff_cannot_moderate(logged_in, artikel):
    logged_in.post(f"/artikel/artikel_detail/{artikel.id}", {"verify": "1"})
    artikel.refresh_from_db()
    assert not artikel.verified


def test_like_artikel(client, user, other, artikel):
    client.force_login(other)
    assert flash(client.get(f"/artikel/add_like/{artikel.id}"))[-1] == msg("successfully_added_like")
    assert client.get(f"/artikel/artikel_detail/{artikel.id}").context["has_liked"] is True
    assert flash(client.get(f"/artikel/add_like/{artikel.id}"))[-1] == msg("successfully_removed_like")
    client.force_login(user)
    assert flash(client.get(f"/artikel/add_like/{artikel.id}"))[-1] == msg("not_allowed_to_like_own_article")
    assert flash(client.get("/artikel/add_like/999"))[-1] == msg("artikel_not_existing")


def test_artikel_model(artikel, other):
    artikel.like.add(other)
    assert artikel.like_count() == 1
    assert str(artikel) == "Alpha" and str(artikel.category) == "Klima"
    artikel.verified, artikel.msg_if_wrong = True, "wrong"
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        artikel.clean()
    artikel.msg_if_wrong = None
    artikel.clean()
    assert str(ArtikelComment(comment="c")) == "c" and str(ArtikelAnswer(answer="a")) == "a"


# ======================================= events =======================================


def future(days=3):
    return (timezone.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")


def event_form(**overrides):
    data = {
        "is_truth": "on",
        "name": "Cleanup",
        "content": "<p>d</p>",
        "date_time": future(),
        "duration": "2,5",
        "adress": "Park",
    }
    data.update(overrides)
    return data


@pytest.fixture
def event(user):
    return Event.objects.create(
        name="Cleanup",
        description="<p>d</p>",
        adress="Park",
        date_time=timezone.now() + datetime.timedelta(days=5),
        duration=2,
        creator=user,
    )


def test_events_overview(client, user, other, event, django_assert_max_num_queries):
    past = Event.objects.create(
        name="Old",
        description="d",
        adress="a",
        date_time=timezone.now() - datetime.timedelta(days=5),
        duration=1,
        creator=other,
    )
    event.participants.add(other)
    with django_assert_max_num_queries(6):
        response = client.get("/events/overview/")
    assert list(response.context["events"]) == [event]
    response = client.post("/events/overview/", {"order_by": "Name", "past_events_visible": "on"})
    assert [e.name for e in response.context["events"]] == ["Cleanup", "Old"]
    assert past


@pytest.mark.parametrize(
    "order, keyword, expected",
    [
        ("Name", "", ["Alpha", "Beta"]),
        ("Datum", "", ["Alpha", "Beta"]),
        ("Dauer", "", ["Alpha", "Beta"]),
        ("Adresse", "Hafen", ["Beta"]),
        ("Ersteller", "bob", ["Beta"]),
        ("Teilnehmeranzahl", "", ["Beta", "Alpha"]),
        ("Teilnehmeranzahl", "1", ["Beta"]),
        ("whatever", "", ["Alpha", "Beta"]),
    ],
)
def test_events_overview_post(client, user, other, order, keyword, expected):
    start = timezone.now() + datetime.timedelta(days=5)
    Event.objects.create(name="Alpha", description="d", adress="Park", date_time=start, duration=1, creator=user)
    beta = Event.objects.create(
        name="Beta",
        description="d",
        adress="Hafen",
        date_time=start + datetime.timedelta(days=1),
        duration=2,
        creator=other,
    )
    beta.participants.add(user)
    response = client.post("/events/overview/", {"order_by": order, "search_keyword": keyword})
    assert [e.name for e in response.context["events"]] == expected


def test_events_overview_personal_filters(logged_in, user, other, event):
    foreign = Event.objects.create(
        name="Foreign",
        description="d",
        adress="a",
        date_time=timezone.now() + datetime.timedelta(days=5),
        duration=1,
        creator=other,
    )
    foreign.participants.add(user)
    mine = logged_in.post("/events/overview/", {"order_by": "von mir erstellte Events"})
    assert [e.name for e in mine.context["events"]] == ["Cleanup"]
    joined = logged_in.post("/events/overview/", {"order_by": "Events, bei denen ich Teilnehmer bin"})
    assert [e.name for e in joined.context["events"]] == ["Foreign"]


@pytest.mark.parametrize("order", ["von mir erstellte Events", "Events, bei denen ich Teilnehmer bin"])
def test_events_overview_personal_filters_anonymous(client, event, order):
    response = client.post("/events/overview/", {"order_by": order})
    assert response.status_code == 200 and list(response.context["events"]) == []


def test_events_overview_invalid_participant_search(client, event):
    response = client.post("/events/overview/", {"order_by": "Teilnehmeranzahl", "search_keyword": "x"})
    assert flash(response) == [msg("teilnehmeranzahl_search_keyword_not_a_number")]


def test_event_detail_participation_and_questions(client, user, other, event):
    client.force_login(other)
    url = f"/events/detail/{event.id}/"
    assert client.get(url).status_code == 200
    assert flash(client.post(url, {"become_member": "1"}))[-1] == msg("joined_event")
    assert event.participants.filter(id=other.id).exists()
    assert flash(client.post(url, {"become_member": "1"}))[-1] == msg("left_event")
    assert flash(client.post(url, {"ask_question": "1", "question": " why? "}))[-1] == msg(
        "successfully_asked_question"
    )
    question = Question.objects.get()
    assert question.question == "why?"
    assert flash(client.post(url, {"ask_question": "1", "question": ""}))[-1] == msg("missing_required_inputs")
    assert flash(client.post(url, {"answer_question": "1", "question_id": question.id, "answer": "because"}))[
        -1
    ] == msg("successfully_answered_question")
    assert flash(client.post(url, {"answer_question": "1", "question_id": question.id, "answer": ""}))[-1] == msg(
        "missing_required_inputs"
    )
    assert flash(client.post(url, {"answer_question": "1", "question_id": "999", "answer": "x"}))[-1] == msg(
        "internal_error"
    )
    client.force_login(user)
    assert flash(client.post(url, {"become_member": "1"}))[-1] == msg("event__user_is_creator")
    assert client.post(url, {"foo": "1"}).status_code == 200


def test_event_detail_anonymous_cannot_participate(client, event):
    response = client.post(f"/events/detail/{event.id}/", {"become_member": "1"})
    assert response.status_code == 200
    assert not event.participants.exists()
    assert client.post(f"/events/detail/{event.id}/", {"ask_question": "1", "question": "x"}).status_code == 200
    assert not Question.objects.exists()
    assert flash(client.get("/events/detail/999/"))[-1] == msg("event_not_existing")


def test_event_answer_must_belong_to_event(logged_in, event, other):
    foreign = Question.objects.create(question="q", user=other)
    response = logged_in.post(
        f"/events/detail/{event.id}/", {"answer_question": "1", "question_id": foreign.id, "answer": "x"}
    )
    assert flash(response)[-1] == msg("internal_error")
    assert not foreign.answers.exists()


def test_add_event(logged_in, user):
    assert logged_in.get("/events/add/").status_code == 200
    response = logged_in.post("/events/add/", event_form(content="<p>x</p><script>y</script>"))
    event = Event.objects.get()
    assert response.url == f"/events/detail/{event.id}/"
    assert (event.creator, event.duration) == (user, 2.5)
    assert "<script" not in event.description


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"is_truth": ""}, "not_is_truth"),
        ({"name": ""}, "missing_required_inputs"),
        ({"name": "x" * 101}, "too_long_input"),
        ({"date_time": "garbage"}, "invalid_date"),
        ({"date_time": "2000-01-01T10:00"}, "date_must_be_tomorrow"),
        ({"duration": "abc"}, "invalid_duration"),
        ({"duration": "-1"}, "invalid_duration"),
        ({"duration": "nan"}, "invalid_duration"),
    ],
)
def test_add_event_errors(logged_in, overrides, key):
    response = logged_in.post("/events/add/", event_form(**overrides))
    assert flash(response) == [msg(key)]
    assert not Event.objects.exists()


def test_edit_event(logged_in, other, event):
    event.participants.add(other)
    assert logged_in.get(f"/events/edit/{event.id}/").status_code == 200
    response = logged_in.post(f"/events/edit/{event.id}/", {"edit": "1", **event_form(name="Renamed")})
    assert flash(response)[-1] == msg("successfully_edited_event")
    event.refresh_from_db()
    assert event.name == "Renamed"
    assert "Renamed" in Benachrichtigung.objects.get(user=other).benachrichtigung_de
    bad = logged_in.post(f"/events/edit/{event.id}/", {"edit": "1", **event_form(name="")})
    assert response.url == f"/events/detail/{event.id}/" and flash(bad)[-1] == msg("missing_required_inputs")
    assert flash(logged_in.post(f"/events/edit/{event.id}/", {"foo": "1"}))[-1] == msg("internal_error")
    deleted = logged_in.post(f"/events/edit/{event.id}/", {"delete": "1"})
    assert deleted.url == "/events/overview/"
    assert not Event.objects.exists()
    assert Benachrichtigung.objects.filter(user=other).count() == 2


def test_edit_event_permissions(logged_in, other, event):
    event.creator = other
    event.save()
    assert flash(logged_in.get(f"/events/edit/{event.id}/"))[-1] == msg("not_authorized_to_visit")
    response = logged_in.get("/events/edit/999/")
    assert response.status_code == 302 and flash(response)[-1] == msg("event_not_existing")


def test_event_model(event, other):
    event.participants.add(other)
    assert event.participants_count == 1
    assert str(event) == "Cleanup"
    assert str(Question(question="q")) == "q" and str(EventAnswer(answer="a")) == "a"


# ======================================= forum =======================================


@pytest.fixture
def forum_category(db):
    return ForumCategory.objects.create(title="Allgemein")


@pytest.fixture
def post(user, forum_category):
    return ForumPost.objects.create(title="Frage", content="<p>q</p>", creator=user, category=forum_category)


def test_forum_overview(client, post, django_assert_max_num_queries):
    with django_assert_max_num_queries(6):
        response = client.get("/forum/forum_overview/")
    assert list(response.context["forum_posts"]) == [post]


def test_forum_overview_query_count_with_answers(client, user, other, forum_category, django_assert_max_num_queries):
    for i in range(10):
        p = ForumPost.objects.create(title=f"P{i}", content="c", creator=other, category=forum_category)
        ForumAnswer.objects.create(content="a", creator=user, forum_post=p)
    client.force_login(user)
    with django_assert_max_num_queries(8):
        client.get("/forum/forum_overview/")


@pytest.mark.parametrize(
    "order, keyword, expected",
    [
        ("Titel", "", ["Frage", "Zweite"]),
        ("Titel", "zwei", ["Zweite"]),
        ("Ersteller", "bob", ["Zweite"]),
        ("Erstellt am", "", ["Zweite", "Frage"]),
        ("Erstellt am", "1999", []),
        (None, "", ["Frage", "Zweite"]),
    ],
)
def test_forum_overview_post(client, user, other, post, forum_category, order, keyword, expected):
    ForumPost.objects.create(
        title="Zweite",
        content="c",
        creator=other,
        category=forum_category,
        date_time=timezone.now() + datetime.timedelta(days=1),
    )
    data = {"category": "Alle", "search_keyword": keyword}
    if order:
        data["order_by"] = order
    response = client.post("/forum/forum_overview/", data)
    assert [p.title for p in response.context["forum_posts"]] == expected


def test_forum_overview_personal_filters(logged_in, user, other, post, forum_category):
    foreign = ForumPost.objects.create(title="Fremd", content="c", creator=other, category=forum_category)
    ForumAnswer.objects.create(content="a", creator=user, forum_post=foreign)
    mine = logged_in.post("/forum/forum_overview/", {"category": "Allgemein", "order_by": "von mir erstellte Posts"})
    assert [p.title for p in mine.context["forum_posts"]] == ["Frage"]
    answered = logged_in.post("/forum/forum_overview/", {"category": "Alle", "order_by": "von mir beantwortete Posts"})
    assert [p.title for p in answered.context["forum_posts"]] == ["Fremd"]


@pytest.mark.parametrize("order", ["von mir erstellte Posts", "von mir beantwortete Posts"])
def test_forum_overview_personal_filters_anonymous(client, post, order):
    response = client.post("/forum/forum_overview/", {"category": "Alle", "order_by": order})
    assert response.status_code == 200 and list(response.context["forum_posts"]) == []


def test_add_forum_post_sanitizes_content(logged_in, user, forum_category):
    assert logged_in.get("/forum/add_forum_post/").status_code == 200
    data = {
        "is_truth": "on",
        "title": "T",
        "content": "<p>ok</p><script>alert(1)</script><img src=x onerror=alert(1)>",
        "category": "Allgemein",
    }
    response = logged_in.post("/forum/add_forum_post/", data)
    created = ForumPost.objects.get()
    assert response.url == f"/forum/post_detail/{created.id}/"
    assert "<script" not in created.content and "onerror" not in created.content
    assert "<p>ok</p>" in created.content


@pytest.mark.parametrize(
    "overrides, expected_url, key",
    [
        ({"is_truth": ""}, "/forum/add_forum_post/", "not_is_truth"),
        ({"category": "Nope"}, "/forum/add_forum_post/", "internal_error"),
        ({"title": ""}, "/forum/add_forum_post/", "missing_required_inputs"),
        ({"content": ""}, "/forum/add_forum_post/", "missing_required_inputs"),
        ({"title": "x" * 101}, "/forum/add_forum_post/", "too_long_input"),
    ],
)
def test_add_forum_post_errors(logged_in, forum_category, overrides, expected_url, key):
    data = {"is_truth": "on", "title": "T", "content": "<p>c</p>", "category": "Allgemein", **overrides}
    response = logged_in.post("/forum/add_forum_post/", data)
    assert response.url == expected_url
    assert flash(response) == [msg(key)]
    assert not ForumPost.objects.exists()


def test_post_detail_and_answer(logged_in, user, other, post):
    client = logged_in
    client.force_login(other)
    assert client.get(f"/forum/post_detail/{post.id}/").status_code == 200
    response = client.post(
        f"/forum/post_detail/{post.id}/", {"is_truth": "on", "content": "<p>a</p><script>x</script>"}
    )
    assert response.url == f"/forum/post_detail/{post.id}/"
    answer = ForumAnswer.objects.get()
    assert "<script" not in answer.content
    assert "Your forum question" in Benachrichtigung.objects.get(user=user).benachrichtigung_en
    assert flash(client.post(f"/forum/post_detail/{post.id}/", {"content": "x"}))[-1] == msg("not_is_truth")
    assert flash(client.post(f"/forum/post_detail/{post.id}/", {"is_truth": "on", "content": ""}))[-1] == msg(
        "missing_required_inputs"
    )
    assert str(answer) == "Antwort von bob auf Frage"


def test_post_detail_anonymous_and_missing(client, post):
    assert client.post(f"/forum/post_detail/{post.id}/", {"is_truth": "on", "content": "x"}).status_code == 200
    assert not ForumAnswer.objects.exists()
    assert flash(client.get("/forum/post_detail/999/"))[-1] == msg("post_not_found")


def test_forum_models(post, forum_category):
    assert str(post) == "Frage" and str(forum_category) == "Allgemein"


# ======================================= petitions =======================================


@pytest.fixture
def petition_category(db):
    return PetitionCategory.objects.create(title="Umwelt")


@pytest.fixture
def petition(user, petition_category):
    return Petition.objects.create(
        title_de="Rettet",
        title_en="Save",
        content_de="<p>c</p>",
        content_en="<p>c</p>",
        goal=10,
        creator=user,
        category=petition_category,
    )


def petition_form(**overrides):
    data = {
        "is_truth": "on",
        "title_de": "T",
        "title_en": "T",
        "content_de": "<p>c</p>",
        "content_en": "<p>c</p>",
        "goal": "25",
        "category": "Umwelt",
    }
    data.update(overrides)
    return data


def test_add_petition(logged_in, user, petition_category):
    assert logged_in.get("/petitions/add_petition/").status_code == 200
    response = logged_in.post("/petitions/add_petition/", petition_form(content_de="<p>x</p><script>y</script>"))
    created = Petition.objects.get()
    assert response.url == f"/petitions/petition_detail/{created.id}/"
    assert created.goal == 25 and "<script" not in created.content_de


@pytest.mark.parametrize(
    "overrides, key",
    [
        ({"is_truth": ""}, "not_is_truth"),
        ({"title_de": ""}, "missing_required_inputs"),
        ({"goal": "abc"}, "goal_not_a_number"),
        ({"goal": "9"}, "goal_too_small"),
        ({"goal": "99999999999"}, "goal_too_big"),
        ({"category": "Nope"}, "internal_error"),
    ],
)
def test_add_petition_errors(logged_in, petition_category, overrides, key):
    response = logged_in.post("/petitions/add_petition/", petition_form(**overrides))
    assert flash(response) == [msg(key)]
    assert not Petition.objects.exists()


def test_petition_detail_sign_and_comment(client, user, other, petition, django_assert_max_num_queries):
    client.force_login(other)
    url = f"/petitions/petition_detail/{petition.id}/"
    with django_assert_max_num_queries(14):
        assert client.get(url).status_code == 200
    assert flash(client.post(url, {"sign": "1"}))[-1] == msg("petition_signed")
    assert petition.signs.filter(id=other.id).exists()
    assert flash(client.post(url, {"sign": "1"}))[-1] == msg("petition_unsigned")
    assert flash(client.post(url, {"add_comment": "1", "comment": "great"}))[-1] == msg("successfully_asked_comment")
    comment = petition.comments.get()
    assert flash(client.post(url, {"add_comment": "1", "comment": ""}))[-1] == msg("missing_required_inputs")
    assert flash(client.post(url, {"answer_comment": "1", "comment_id": comment.id, "answer": "thx"}))[-1] == msg(
        "successfully_answered_comment"
    )
    assert flash(client.post(url, {"answer_comment": "1", "comment_id": comment.id, "answer": ""}))[-1] == msg(
        "missing_required_inputs"
    )
    response = client.post(url, {"answer_comment": "1", "comment_id": "999", "answer": "x"})
    assert response.url == url and flash(response)[-1] == msg("internal_error")
    assert client.post(url, {"foo": "1"}).status_code == 200


def test_petition_detail_anonymous_and_missing(client, petition):
    assert client.post(f"/petitions/petition_detail/{petition.id}/", {"sign": "1"}).status_code == 200
    assert not petition.signs.exists()
    assert flash(client.get("/petitions/petition_detail/999/"))[-1] == msg("petition_not_found")


def test_edit_petition_update_and_goal(logged_in, other, petition):
    petition.signs.add(other)
    url = f"/petitions/edit_petition/{petition.id}/"
    assert logged_in.get(url).status_code == 200
    data = {
        "update": "1",
        "is_truth": "on",
        "title_de": "U",
        "title_en": "U",
        "content_de": "<p>x</p>",
        "content_en": "<p>x</p>",
    }
    response = logged_in.post(url, data)
    assert response.url == f"/petitions/petition_detail/{petition.id}/"
    assert petition.updates.count() == 1 and Update.objects.count() == 1
    assert "update" in Benachrichtigung.objects.get(user=other).benachrichtigung_en
    assert logged_in.post(url, {**data, "is_truth": ""}).url == url
    assert flash(logged_in.post(url, {**data, "title_de": ""}))[-1] == msg("missing_required_inputs")
    assert flash(logged_in.post(url, {"change_goal": "1", "goal": "50"}))[-1] == msg("successfully_updated_goal")
    petition.refresh_from_db()
    assert petition.goal == 50
    assert flash(logged_in.post(url, {"change_goal": "1", "goal": ""}))[-1] == msg("missing_required_inputs")
    response = logged_in.post(url, {"change_goal": "1", "goal": "3"})
    assert response.url == "/petitions/add_petition/" and flash(response)[-1] == msg("goal_too_small")
    assert logged_in.post(url, {"foo": "1"}).status_code == 200


def test_edit_petition_success_toggle(logged_in, other, petition):
    petition.signs.add(other)
    url = f"/petitions/edit_petition/{petition.id}/"
    assert flash(logged_in.post(url, {"success": "1"}))[-1] == msg("added_success")
    petition.refresh_from_db()
    assert petition.success
    assert flash(logged_in.post(url, {"success": "1"}))[-1] == msg("removed_success")
    assert Benachrichtigung.objects.filter(user=other).count() == 2


def test_edit_petition_permissions(logged_in, other, petition):
    petition.creator = other
    petition.save()
    response = logged_in.get(f"/petitions/edit_petition/{petition.id}/")
    assert response.url == "/petitions/add_petition/"
    assert flash(logged_in.get("/petitions/edit_petition/999/"))[-1] == msg("petition_not_found")


@pytest.mark.parametrize(
    "order, keyword, expected",
    [
        ("Titel", "", ["Alpha", "Beta"]),
        ("Titel", "bet", ["Beta"]),
        ("Ersteller", "bob", ["Beta"]),
        ("Erstellt am", "", ["Alpha", "Beta"]),
        ("Erstellt am", "1999", []),
        ("Unterschriften", "", ["Beta", "Alpha"]),
        ("Unterschriften", "1", ["Beta"]),
        (None, "", ["Alpha", "Beta"]),
    ],
)
def test_petitions_overview_post(client, user, other, petition_category, order, keyword, expected):
    Petition.objects.create(
        title_de="Alpha",
        title_en="Alpha",
        content_de="c",
        content_en="c",
        goal=10,
        creator=user,
        category=petition_category,
    )
    beta = Petition.objects.create(
        title_de="Beta",
        title_en="Beta",
        content_de="c",
        content_en="c",
        goal=10,
        creator=other,
        category=petition_category,
    )
    beta.signs.add(user)
    data = {"category": "Alle", "search_keyword": keyword}
    if order:
        data["order_by"] = order
    response = client.post("/petitions/petitions_overview/", data)
    assert [p.title_de for p in response.context["petitions"]] == expected


def test_petitions_overview_filters(logged_in, user, other, petition, petition_category, django_assert_max_num_queries):
    done = Petition.objects.create(
        title_de="Done",
        title_en="Done",
        content_de="c",
        content_en="c",
        goal=10,
        creator=other,
        category=petition_category,
        success=True,
    )
    done.signs.add(user)
    with django_assert_max_num_queries(8):
        default = logged_in.get("/petitions/petitions_overview/")
    assert [p.title_de for p in default.context["petitions"]] == ["Rettet"]
    shown = logged_in.post(
        "/petitions/petitions_overview/", {"category": "Alle", "success_visible": "on", "order_by": "Titel"}
    )
    assert [p.title_de for p in shown.context["petitions"]] == ["Done", "Rettet"]
    mine = logged_in.post(
        "/petitions/petitions_overview/", {"category": "Alle", "order_by": "von mir erstellte Petitionen"}
    )
    assert [p.title_de for p in mine.context["petitions"]] == ["Rettet"]
    signed = logged_in.post(
        "/petitions/petitions_overview/",
        {"category": "Alle", "success_visible": "on", "order_by": "von mir unterschriebene Petitionen"},
    )
    assert [p.title_de for p in signed.context["petitions"]] == ["Done"]


@pytest.mark.parametrize("order", ["von mir erstellte Petitionen", "von mir unterschriebene Petitionen"])
def test_petitions_overview_personal_filters_anonymous(client, petition, order):
    response = client.post("/petitions/petitions_overview/", {"category": "Alle", "order_by": order})
    assert response.status_code == 200 and list(response.context["petitions"]) == []


def test_petitions_overview_invalid_search(client, petition):
    response = client.post(
        "/petitions/petitions_overview/", {"category": "Alle", "order_by": "Unterschriften", "search_keyword": "x"}
    )
    assert flash(response) == [msg("signs_search_keyword_not_a_number")]


def test_petition_models(petition, other):
    petition.signs.add(other)
    assert petition.signs_count() == 1
    assert str(petition) == "Rettet"
    assert (
        str(PetitionCategory(title="c")) == "c"
        and str(Update(title="u")) == "u"
        and str(PetitionComment(comment="c")) == "c"
    )
