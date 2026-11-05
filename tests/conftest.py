import itertools

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.test import Client
from django.utils import translation

from aktionen.models import Aktion, AktionenListe, Category
from family.models import Family
from personals.models import Level, UserErweitert

_counter = itertools.count(1)


@pytest.fixture(autouse=True)
def default_language():
    """Requests activate their language for the whole thread: start every test in the default language."""
    translation.activate(settings.LANGUAGE_CODE)
    yield
    translation.deactivate_all()


@pytest.fixture(autouse=True)
def clear_cache():
    """The home page statistics are cached: every test starts with an empty cache."""
    cache.clear()
    yield
    cache.clear()


class LangClient(Client):
    """Test client that adds the mandatory language prefix (see LanguageFallbackMiddleware)."""

    language = "de"

    def generic(self, method, path, *args, **kwargs):
        if (
            path.startswith("/")
            and not path.startswith(("/de/", "/en/", "/static/", "/media/"))
            and path
            not in (
                "/de",
                "/en",
            )
        ):
            path = f"/{self.language}{path}"
        return super().generic(method, path, *args, **kwargs)


@pytest.fixture
def client():
    return LangClient()


@pytest.fixture
def en_client():
    c = LangClient()
    c.language = "en"
    return c


def flash(response):
    """Messages queued for the next page, as plain strings."""
    return [str(m) for m in get_messages(response.wsgi_request)]


@pytest.fixture
def worldwide(db):
    return Family.objects.create(name="worldwide ranking", password="pw", admin_password="admin")


@pytest.fixture
def levels(db):
    return [
        Level.objects.create(klimapunkte=0, description="Keimling", description_en="Seedling"),
        Level.objects.create(klimapunkte=100, description="Setzling", description_en="Sapling"),
        Level.objects.create(klimapunkte=500, description="Baum", description_en="Tree"),
    ]


@pytest.fixture
def make_user(db, worldwide):
    def _make(username=None, lang="de", **extra):
        username = username or f"user{next(_counter)}"
        email = extra.pop("email", "")
        profile = {
            key: extra.pop(key)
            for key in list(extra)
            if key in {"mail_verified", "mailinglist", "weekly_goal", "allows_data_view", "additional_klimapunkte"}
        }
        user = User.objects.create_user(username=username, password="pw12345!", email=email, **extra)
        UserErweitert.objects.create(user=user, lang=lang, **profile)
        worldwide.members.add(user)
        return user

    return _make


@pytest.fixture
def user(make_user):
    return make_user("alice")


@pytest.fixture
def other(make_user):
    return make_user("bob", allows_data_view=True)


@pytest.fixture
def staff(make_user):
    return make_user("staffer", is_staff=True)


@pytest.fixture
def logged_in(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Mobilität", name_en="Mobility")


@pytest.fixture
def action_type(category):
    return AktionenListe.objects.create(
        name="Fahrrad",
        name_en="Bike",
        klimapunkte=2.0,
        mengeBeschreibung="Kilometer",
        mengeBeschreibung_en="kilometers",
        mengeBeschreibungSingular="Kilometer",
        mengeBeschreibungSingular_en="kilometer",
        anmerkung="a",
        anmerkung_en="a",
        source="s",
        source_en="s",
        max=50,
        category=category,
    )


@pytest.fixture
def make_aktion(db):
    def _make(user, action_type, quantity=1.0, date=None, **extra):
        kwargs = {"date": date} if date else {}
        return Aktion.objects.create(user=user, aktion=action_type, quantity=quantity, **kwargs, **extra)

    return _make
