"""Weekly evaluation of the hall of fame challenges (run by a cron job, see ``CRONJOBS`` in the settings)."""

from collections.abc import Callable
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import F, Q, QuerySet, Sum, Window
from django.db.models.functions import Rank
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from family.models import Family
from hall_of_fame.models import HallOfFameData, HallOfFameEntry
from utils.functions import WORLDWIDE_RANKING_NAME, create_notification

MIN_WEEKLY_KLIMAPUNKTE = 50
MIN_WEEKLY_BIKE_KILOMETERS = 50
TOP_RANK_LIMIT = 5
# Primary keys of the predefined actions in the production database.
BIKE_ACTION_ID = 19
VEGAN_ACTION_ID = 20
VEGETARIAN_ACTION_IDS = [VEGAN_ACTION_ID, 22]


def _qualified_users_50_points(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.annotate(
        weekly_klimapunkte=Sum(
            F("aktion__aktion__klimapunkte") * F("aktion__quantity"), filter=Q(aktion__date__gte=week_start)
        )
    ).filter(weekly_klimapunkte__gte=MIN_WEEKLY_KLIMAPUNKTE)


def _qualified_users_top_5(week_start: date, today: date) -> QuerySet[User]:
    family = Family.objects.get(name=WORLDWIDE_RANKING_NAME)
    return (
        family.members.filter(aktion__date__gte=week_start)
        .annotate(
            total_klimapunkte=Sum(F("aktion__aktion__klimapunkte") * F("aktion__quantity")),
            rank=Window(expression=Rank(), order_by=F("total_klimapunkte").desc()),
        )
        .filter(rank__lte=TOP_RANK_LIMIT)
    )


def _qualified_users_bike(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.annotate(
        weekly_kilometers_by_bike=Sum(
            F("aktion__quantity"), filter=Q(aktion__date__gte=week_start) & Q(aktion__aktion__id=BIKE_ACTION_ID)
        )
    ).filter(weekly_kilometers_by_bike__gte=MIN_WEEKLY_BIKE_KILOMETERS)


def _qualified_users_vegetarian(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.filter(
        aktion__aktion_id__in=VEGETARIAN_ACTION_IDS, aktion__date=today, aktion__quantity__gte=1
    ).distinct()


def _qualified_users_vegan(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.filter(
        aktion__aktion_id=VEGAN_ACTION_ID, aktion__date=today, aktion__quantity__gte=1
    ).distinct()


def _qualified_users_article(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.filter(artikel__created_at__range=(week_start, today)).distinct()


def _qualified_users_event(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.filter(event__created_at__range=(week_start, today)).distinct()


def _qualified_users_petition(week_start: date, today: date) -> QuerySet[User]:
    return User.objects.filter(created_petitions__created_at__range=(week_start, today)).distinct()


# Description of the achievement with {start} and {end} placeholders: (german, english).
DESCRIPTIONS = {
    _qualified_users_50_points: (
        "Hat zwischen dem {start} und dem {end} 50 oder mehr Klimapunkte gesammelt.",
        "Has collected 50 or more climate points between {start} and {end}.",
    ),
    _qualified_users_top_5: (
        "War zwischen dem {start} und dem {end} einer der Top-5 Klimapunkt-Sammler.",
        "Was one of the top 5 climate point collectors between {start} and {end}.",
    ),
    _qualified_users_bike: (
        "Ist zwischen dem {start} und dem {end} mindestens 50 Kilometer Fahrrad gefahren.",
        "Rode at least 50 kilometers by bike between {start} and {end}.",
    ),
    _qualified_users_vegetarian: (
        "Hat sich zwischen dem {start} und dem {end} vegetarisch ernährt.",
        "Lived as a vegetarian between {start} and {end}.",
    ),
    _qualified_users_vegan: (
        "Hat sich zwischen dem {start} und dem {end} vegan ernährt.",
        "Lived vegan between {start} and {end}.",
    ),
    _qualified_users_article: (
        "Hat zwischen dem {start} und dem {end} einen Artikel veröffentlicht.",
        "Published an article between {start} and {end}.",
    ),
    _qualified_users_event: (
        "Hat zwischen dem {start} und dem {end} ein Event veröffentlicht.",
        "Published an event between {start} and {end}.",
    ),
    _qualified_users_petition: (
        "Hat zwischen dem {start} und dem {end} eine Petition erstellt.",
        "Created a petition between {start} and {end}.",
    ),
}

# (evaluation of the finished week, number of the following step, next week's challenge in German and English)
WEEKLY_STEPS: list[tuple[Callable[[date, date], QuerySet[User]], int, str, str]] = [
    (
        _qualified_users_50_points,
        1,
        "Sei in der nächsten Woche einer der Top-5 Klimapunkte-Sammler",
        "Be one of the top 5 climate point collectors next week",
    ),
    (
        _qualified_users_top_5,
        2,
        "Fahre nächste Woche mindestens 50 Kilometer mit dem Fahrrad",
        "Ride at least 50 kilometers by bike next week",
    ),
    (_qualified_users_bike, 3, "Ernähre dich nächste Woche vegetarisch", "Eat vegetarian next week"),
    (_qualified_users_vegetarian, 4, "Ernähre dich nächste Woche vegan", "Eat vegan next week"),
    (
        _qualified_users_vegan,
        5,
        "Erstelle nächste Woche mindestens einen Artikel",
        "Create at least one article next week",
    ),
    (
        _qualified_users_article,
        6,
        "Erstelle nächste Woche mindestens ein Event",
        "Create at least one event next week",
    ),
    (
        _qualified_users_event,
        7,
        "Erstelle nächste Woche mindestens eine Petition",
        "Create at least one petition next week",
    ),
    (
        _qualified_users_petition,
        0,
        "Sammle nächste Woche mindestens 50 Klimapunkte",
        "Collect at least 50 climate points next week",
    ),
]


def induct_into_hall_of_fame(request, users, description_de: str, description_en: str) -> None:
    users = list(users)
    HallOfFameEntry.objects.bulk_create(
        [HallOfFameEntry(user=user, description_de=description_de, description_en=description_en) for user in users]
    )
    for user in users:
        create_notification(
            request,
            notification_de="Du wurdest in die Hall of Fame aufgenommen",
            notification_en="You have been inducted into the hall of fame",
            user=user,
            url=reverse("hall_of_fame_detail"),
        )


def run_weekly_hall_of_fame(today: date | None = None) -> None:
    """Evaluate this week's challenge, induct the winners and announce the next challenge to everybody."""
    today = today or timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    request = RequestFactory().get("/")

    data, _ = HallOfFameData.objects.get_or_create(id=1)
    if not 0 <= data.weeks_count < len(WEEKLY_STEPS):
        data.weeks_count = 0
        data.save()
        return

    evaluate, next_step, to_do_de, to_do_en = WEEKLY_STEPS[data.weeks_count]
    description_de, description_en = DESCRIPTIONS[evaluate]
    induct_into_hall_of_fame(
        request,
        evaluate(week_start, today),
        description_de.format(start=week_start.strftime("%d.%m.%Y"), end=today.strftime("%d.%m.%Y")),
        description_en.format(start=week_start.strftime("%m/%d/%Y"), end=today.strftime("%m/%d/%Y")),
    )

    data.weeks_count = next_step
    data.to_do_de = to_do_de
    data.to_do_en = to_do_en
    data.save()
    for user in User.objects.all():
        request.user = user
        create_notification(
            request,
            notification_de=f"Es ist eine neue Challenge verfügbar, um nächste Woche in die Hall of Fame zu kommen: {to_do_de}",
            notification_en=f"A new challenge is available to become a member of the hall of fame: {to_do_en}",
            user=user,
            url=reverse("hall_of_fame_detail"),
        )
