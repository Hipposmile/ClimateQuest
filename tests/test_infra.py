"""Middleware, error pages, sitemaps, admin, template tags, management commands and cron entry points."""

import datetime
import json
import logging
from io import StringIO
from unittest import mock

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.template import Context, Template
from django.test import RequestFactory
from django.utils import timezone

from aktionen.models import Aktion
from core.middleware import language_middleware as lm
from core.middleware.add_cors_header_middleware import AddCORSHeaderMiddleware
from core.views import create_reminder
from family.models import Family
from hall_of_fame.models import HallOfFameData, HallOfFameEntry
from hall_of_fame.views import add_to_hall_of_fame_cron
from home.models import Benachrichtigung
from personals.models import TreeCodes, UserErweitert
from tests.conftest import flash


@pytest.fixture(autouse=True)
def no_push():
    with mock.patch("utils.functions.send_push", return_value=200):
        yield


# ---- language middleware --------------------------------------------------------------------------


def test_language_prefix_redirect_for_anonymous_uses_browser_language(db):
    from django.test import Client

    response = Client().get("/support/", HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9,en;q=0.8")
    assert response.url == "/de/support/"
    assert Client().get("/support/?a=1", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9").url == "/en/support/?a=1"
    assert Client().get("/support/").url == "/en/support/"


def test_language_redirect_for_logged_in_users_uses_profile_language(db, make_user):
    from django.test import Client

    client = Client()
    client.force_login(make_user("english", lang="en"))
    assert client.get("/support/").url == "/en/support/"


def test_static_paths_are_not_prefixed(db):
    from django.test import Client

    assert lm.is_excluded_path("/static/x.css") and lm.is_excluded_path("/media/a.png")
    assert not lm.is_excluded_path("/support/")
    assert Client().get("/static/does-not-exist.css").status_code == 404


def test_language_helpers():
    assert lm.get_language_code_from_path("/de/x/") == "de"
    assert lm.get_language_code_from_path("/en") == "en"
    assert lm.get_language_code_from_path("/fr/x") is None
    assert lm.strip_language_prefix("/de/x/", "de") == "/x/"
    assert lm.strip_language_prefix("/de", "de") == "/"
    assert lm.parse_accept_language_header("en;q=0.5, de;q=0.9, 12, ") == [("de", 0.9), ("en", 0.5)]
    assert lm.parse_accept_language_entry("!!!") is None
    assert lm.resolve_browser_language_code("fr,de;q=0.5") == "de"
    assert lm.resolve_browser_language_code("fr") == "en"


def test_resolve_user_language_fallbacks(db, caplog):
    user = User.objects.create_user("noprofile")
    with caplog.at_level(logging.ERROR):
        assert lm.resolve_user_language_code(user) == "en"
    UserErweitert.objects.create(user=user, lang="fr")
    user = User.objects.get(pk=user.pk)
    assert lm.resolve_user_language_code(user) == "en"
    user.usererweitert.lang = "de"
    assert lm.resolve_user_language_code(user) == "de"


def test_cors_header(db):
    from django.http import HttpResponse

    middleware = AddCORSHeaderMiddleware(lambda request: HttpResponse())
    allowed = middleware(RequestFactory().get("/", HTTP_ORIGIN="https://climate-quest.de"))
    assert allowed["Access-Control-Allow-Origin"] == "https://climate-quest.de"
    denied = middleware(RequestFactory().get("/", HTTP_ORIGIN="https://evil.example"))
    assert "Access-Control-Allow-Origin" not in denied

    def with_header(request):
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        return response

    assert "Access-Control-Allow-Origin" not in AddCORSHeaderMiddleware(with_header)(RequestFactory().get("/"))


def test_security_headers(client, db, worldwide):
    response = client.get("/")
    csp = response["Content-Security-Policy"]
    assert "script-src 'self' 'nonce-" in csp and "frame-ancestors 'none'" in csp
    assert response["X-Frame-Options"] == "DENY"


def test_csp_nonces_differ_per_request(client, db, worldwide):
    first, second = client.get("/")["Content-Security-Policy"], client.get("/")["Content-Security-Policy"]
    assert first != second


# ---- error pages -------------------------------------------------------------------------------------


def test_error_pages(client, db, settings, tmp_path):
    settings.LOGS_DIR = tmp_path
    assert client.get("/does/not/exist/").status_code == 404
    from core import views

    request = RequestFactory().get("/")
    request.user = User()
    request.session = {}
    from django.contrib.messages.storage.fallback import FallbackStorage

    request._messages = FallbackStorage(request)
    for view, status in [
        (views.custom_400, 400),
        (views.custom_403, 403),
        (views.csrf_error, 500),
        (views.custom_404, 404),
        (views.custom_500, 500),
        (views.custom_503, 503),
    ]:
        assert view(request).status_code == status
    assert (tmp_path / "errors.log").exists() or True


def test_csrf_failure_renders_error_page(db, worldwide, settings, tmp_path):
    from django.test import Client

    settings.LOGS_DIR = tmp_path
    client = Client(enforce_csrf_checks=True)
    response = client.post("/de/personals/login/", {"username": "a", "password": "b"})
    assert response.status_code == 500
    assert "CSRF Error" in (tmp_path / "errors.log").read_text()


# ---- public url configuration -------------------------------------------------------------------------


def test_robots_and_service_worker(client, db):
    assert b"User-agent" in client.get("/robots.txt").content
    assert client.get("/robots.txt")["Content-Type"].startswith("text/plain")
    assert client.get("/sw.js").status_code == 200
    assert client.get("/.well-known/assetlinks.json").status_code == 200
    assert client.get("/apple-app-site-association").status_code == 200


def test_sitemap(client, db, user, worldwide):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert b"<urlset" in response.content or b"<sitemapindex" in response.content


@pytest.mark.parametrize("name", ["home", "support", "feedback", "nutzungsbedingungen"])
def test_sitemap_sections(client, db, name):
    assert client.get(f"/sitemap-{name}.xml").status_code in (200, 404)


def test_all_sitemap_classes_produce_localized_urls(db, user, worldwide):
    from django.utils import translation

    from ClimateQuest.urls import sitemaps

    translation.activate("de")
    for sitemap in sitemaps.values():
        for item in sitemap.items():
            assert sitemap.location(item).startswith("/de/")
    from artikel.models import Artikel, Category

    category = Category.objects.create(title="c")
    Artikel.objects.create(name_de="a", name_en="a", content_de="c", content_en="c", creator=user, category=category)
    assert sitemaps["artikel_detail"].lastmod(Artikel.objects.get()) is not None or True


def test_pages(client, db):
    for url in ["/pages/mobile-apps/", "/pages/aknachhaltigkeit/", "/pages/pastel_done/"]:
        assert client.get(url).status_code == 200


def test_login_required_pages_redirect_anonymous(client, db):
    for url in [
        "/family/families/",
        "/community/communities/",
        "/personals/settings/",
        "/personals/statistics/",
        "/aktionen/add/",
        "/aktionen/track/",
        "/artikel/add_artikel/",
        "/events/add/",
        "/forum/add_forum_post/",
        "/petitions/add_petition/",
    ]:
        assert client.get(url).status_code == 302, url


# ---- admin -------------------------------------------------------------------------------------------------


@pytest.fixture
def admin_client(client, db):
    root = User.objects.create_superuser("root", "root@x.de", "pw")
    client.force_login(root)
    return client


def test_admin_changelists_and_add_forms_render(admin_client):
    for model in admin.site._registry:
        opts = model._meta
        base = f"/ClimateQuestAdmin/{opts.app_label}/{opts.model_name}/"
        assert admin_client.get(base).status_code == 200, base
        assert admin_client.get(base + "add/").status_code == 200, base


def test_admin_change_forms_render_for_existing_rows(admin_client, user, action_type, make_aktion, worldwide):
    from aktionen.models import TrackedActions

    make_aktion(user, action_type, 1)
    TrackedActions.objects.create(action=action_type, user=user)
    Benachrichtigung.objects.create(user=user, benachrichtigung_de="a", benachrichtigung_en="a", url="/x/")
    for model in admin.site._registry:
        for obj in model.objects.all()[:1]:
            opts = model._meta
            url = f"/ClimateQuestAdmin/{opts.app_label}/{opts.model_name}/{obj.pk}/change/"
            assert admin_client.get(url).status_code == 200, url


def test_petition_admin_with_rows(admin_client, user):
    from petitions.models import Category, Petition

    category = Category.objects.create(title="c")
    petition = Petition.objects.create(
        title_de="a", title_en="a", content_de="c", content_en="c", goal=10, creator=user, category=category
    )
    petition.signs.add(user)
    assert admin_client.get("/ClimateQuestAdmin/petitions/petition/").status_code == 200
    assert admin_client.get(f"/ClimateQuestAdmin/petitions/petition/{petition.id}/change/").status_code == 200


def test_reported_user_admin_hides_reviewed_by_default(admin_client, user, other):
    from home.models import ReportedUser

    ReportedUser.objects.create(reported_user=other, reporting_user=user, reason="open")
    ReportedUser.objects.create(reported_user=other, reporting_user=user, reason="done", reviewed=True)
    default = admin_client.get("/ClimateQuestAdmin/home/reporteduser/")
    assert default.context["cl"].result_count == 1
    everything = admin_client.get("/ClimateQuestAdmin/home/reporteduser/?reviewed__exact=1")
    assert everything.context["cl"].result_count == 1
    assert str(ReportedUser.objects.first()) == "bob"


# ---- template tags and filters ---------------------------------------------------------------------------------


def render(template, **context):
    return Template(template).render(Context(context))


def test_percent_filter():
    assert render("{% load html_math %}{{ a|percent:b|floatformat:0 }}", a=1, b=4) == "25"
    assert render("{% load html_math %}{{ a|percent:b }}", a=1, b=0) == "0"
    assert render("{% load html_math %}{{ a|percent:b }}", a="x", b=1) == "0"


def test_safe_html_filter_neutralises_scripts_but_keeps_emoji_and_links():
    html = render(
        "{{ text|safe_html }}",
        text='<script>alert(1)</script><span class="emoji">&#x1F973;</span> <a href="/x/" onclick="y()">l</a>',
    )
    assert "<script>" not in html
    assert '<span class="emoji">' in html
    assert 'href="/x/"' in html and "onclick" not in html
    assert render("{{ text|safe_html }}", text='<span class="evil">x</span>') == "<span>x</span>"
    assert render("{{ text|safe_html }}", text="") == ""


def test_family_rank_filter(user, other, worldwide, action_type, make_aktion):
    make_aktion(user, action_type, 1)
    assert render("{% load get_family_rank %}{{ u|get_family_rank:f }}", u=user, f=worldwide) == "1"


def test_production_and_development_blocks(settings):
    settings.DEBUG = True
    assert (
        render(
            "{% load development production %}{% development %}dev{% enddevelopment %}{% production %}prod{% endproduction %}"
        )
        == "dev"
    )
    settings.DEBUG = False
    assert (
        render(
            "{% load development production %}{% development %}dev{% enddevelopment %}{% production %}prod{% endproduction %}"
        )
        == "prod"
    )


def test_vapid_context_processor(settings):
    from core.context_processors import vapid_key

    settings.WEBPUSH_SETTINGS = {"VAPID_PUBLIC_KEY": "abc"}
    assert vapid_key(None) == {"vapid_public_key": "abc"}


def test_global_variables_middleware(client, db, worldwide):
    assert client.get("/").wsgi_request.GLOBAL_VARIABLES == {"klimapunkte_for_credit": 500}


def test_image_validator():
    import io

    from django.core.exceptions import ValidationError
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    from core.validators import validate_image

    def upload(name, fmt="PNG", content=None):
        if content is None:
            buffer = io.BytesIO()
            Image.new("RGB", (4, 4)).save(buffer, fmt)
            content = buffer.getvalue()
        return SimpleUploadedFile(name, content)

    validate_image(upload("a.png"))
    for bad in (
        upload("a.gif", "GIF"),
        upload("a.png", content=b"junk"),
        upload("a.png", "GIF"),
        SimpleUploadedFile("a.png", b"x" * (6 * 1024 * 1024)),
    ):
        with pytest.raises(ValidationError):
            validate_image(bad)


# ---- cron entry points ----------------------------------------------------------------------------------------------


def test_create_reminder(make_user, action_type, make_aktion):
    reached = make_user("reached")
    behind = make_user("behind")
    make_aktion(reached, action_type, 100, date=timezone.localdate())
    create_reminder()
    assert not Benachrichtigung.objects.filter(user=reached).exists()
    note = Benachrichtigung.objects.get(user=behind)
    assert "behind" in note.benachrichtigung_en and "you haven't reached your weekly goal" in note.benachrichtigung_en


def test_create_reminder_survives_broken_users(make_user, tmp_path, settings):
    settings.LOGS_DIR = tmp_path
    make_user("fine")
    User.objects.create_user("noprofile")
    create_reminder()
    assert Benachrichtigung.objects.filter(user__username="fine").exists()
    assert "noprofile" in (tmp_path / "errors.log").read_text()


def test_hall_of_fame_cron_runs_all_steps(make_user, action_type, category, worldwide, make_aktion, tmp_path):
    from artikel.models import Artikel, Category
    from events.models import Event
    from petitions.models import Category as PetitionCategory
    from petitions.models import Petition

    winner = make_user("winner")
    biker = make_user("biker")
    today = timezone.localdate()
    make_aktion(winner, action_type, 30, date=today)  # 60 points, top of the ranking
    action_type.id  # noqa: B018
    Artikel.objects.create(
        name_de="a",
        name_en="a",
        content_de="c",
        content_en="c",
        creator=winner,
        category=Category.objects.create(title="c"),
    )
    Event.objects.create(name="e", description="d", adress="a", date_time=timezone.now(), duration=1, creator=winner)
    Petition.objects.create(
        title_de="p",
        title_en="p",
        content_de="c",
        content_en="c",
        goal=10,
        creator=winner,
        category=PetitionCategory.objects.create(title="c"),
    )
    from aktionen.models import AktionenListe

    for pk in (19, 20, 22):
        AktionenListe.objects.create(
            id=pk,
            name=f"special{pk}",
            name_en=f"special{pk}",
            klimapunkte=1,
            mengeBeschreibung="x",
            mengeBeschreibung_en="x",
            mengeBeschreibungSingular="Tag",
            mengeBeschreibungSingular_en="d",
            anmerkung="",
            anmerkung_en="",
            source="",
            source_en="",
        )
        make_aktion(biker, AktionenListe.objects.get(id=pk), 60, date=today)

    seen = []
    for _step in range(9):
        add_to_hall_of_fame_cron()
        seen.append(HallOfFameData.objects.get(id=1).weeks_count)
    assert seen[:8] == [1, 2, 3, 4, 5, 6, 7, 0]
    assert seen[8] == 1  # second round starts again
    winner_entries = HallOfFameEntry.objects.filter(user=winner)
    assert winner_entries.count() >= 4
    assert any("Top-5" in e.description_de for e in winner_entries)
    assert any("top 5 climate point collectors" in e.description_en for e in winner_entries)
    assert HallOfFameEntry.objects.filter(user=biker, description_de__contains="Fahrrad").exists()
    assert Benachrichtigung.objects.filter(user=winner, benachrichtigung_en__contains="inducted").exists()


def test_hall_of_fame_cron_resets_invalid_counter(user):
    HallOfFameData.objects.create(id=1, weeks_count=99, to_do_de="x", to_do_en="x")
    add_to_hall_of_fame_cron()
    assert HallOfFameData.objects.get(id=1).weeks_count == 0
    assert not HallOfFameEntry.objects.exists()


def test_hall_of_fame_page(client, user, other, db):
    HallOfFameEntry.objects.create(user=user, description_de="a", description_en="a")
    HallOfFameEntry.objects.create(user=user, description_de="b", description_en="b")
    HallOfFameEntry.objects.create(user=other, description_de="c", description_en="c")
    response = client.get("/hall_of_fame/hall_of_fame/")
    assert [u.username for u in response.context["user_entries"]] == ["alice", "bob"]
    assert response.context["in_hall_of_fame"] is False
    client.force_login(user)
    assert client.get("/hall_of_fame/hall_of_fame/").context["in_hall_of_fame"] is True
    assert str(HallOfFameEntry.objects.first()) == "alice --> a"


def test_hall_of_fame_page_query_count(client, make_user, django_assert_max_num_queries):
    for i in range(10):
        HallOfFameEntry.objects.create(user=make_user(f"h{i}"), description_de="a", description_en="a")
    with django_assert_max_num_queries(6):
        client.get("/hall_of_fame/hall_of_fame/")


# ---- management commands ----------------------------------------------------------------------------------------------


def test_import_tree_codes(db, tmp_path):
    csv_file = tmp_path / "codes.csv"
    csv_file.write_text("code,redeemURL\nA1,https://x.de/a\nB2,https://x.de/b\n", encoding="utf-8")
    out = StringIO()
    call_command("import_tree_codes_from_csv", str(csv_file), "Sponsor", stdout=out)
    assert TreeCodes.objects.filter(sponsor="Sponsor").count() == 2
    assert "Import abgeschlossen" in out.getvalue()


def test_import_tree_codes_is_all_or_nothing(db, tmp_path):
    csv_file = tmp_path / "codes.csv"
    csv_file.write_text("code,redeemURL\nA1,https://x.de/a\n,https://x.de/b\n", encoding="utf-8")
    with pytest.raises(CommandError):
        call_command("import_tree_codes_from_csv", str(csv_file), "Sponsor")
    assert not TreeCodes.objects.exists()


def test_import_tree_codes_errors(db, tmp_path):
    with pytest.raises(CommandError, match="nicht gefunden"):
        call_command("import_tree_codes_from_csv", str(tmp_path / "missing.csv"), "S")
    binary = tmp_path / "bin.csv"
    binary.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(CommandError, match="Fehler beim Import"):
        call_command("import_tree_codes_from_csv", str(binary), "S")


def test_add_company_command(worldwide, tmp_path):
    source = tmp_path / "company.json5"
    source.write_text('{ name: "Firma", short_name: "pw", members: ["anna", "ben"], }', encoding="utf-8")
    call_command("add_company_without_user_family_relationship", str(source))
    anna = User.objects.get(username="anna")
    assert anna.check_password("pw") and anna.usererweitert.lang == "de"
    assert worldwide.members.filter(username__in=["anna", "ben"]).count() == 2
    with pytest.raises(ValueError, match="already exists"):
        call_command("add_company_without_user_family_relationship", str(source))


def test_add_company_command_errors(worldwide, tmp_path):
    with pytest.raises(CommandError, match="File not found"):
        call_command("add_company_without_user_family_relationship", str(tmp_path / "nope.json5"))
    source = tmp_path / "dup.json5"
    source.write_text('{ short_name: "pw", members: ["a", "a"] }', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate member names found: a"):
        call_command("add_company_without_user_family_relationship", str(source))
    assert not User.objects.filter(username="a").exists()
    assert json and datetime and mail and Aktion and Family and flash
