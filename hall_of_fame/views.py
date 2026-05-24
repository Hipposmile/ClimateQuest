from collections.abc import Callable
from datetime import date, timedelta
from typing import List

from django.contrib.auth.models import User
from django.db.models import Count, F, Sum, Q, QuerySet
from django.db.models import Window
from django.db.models.functions import Rank
from django.shortcuts import render
from django.test import RequestFactory
from django.urls import reverse

from core.views import fake_request
from family.models import Family
from hall_of_fame.models import HallOfFameEntry, HallOfFameData
from utils.functions import create_notification


def hall_of_fame_detail(request):
    user_entries = {}
    users = User.objects.filter(hall_of_fame_entry__isnull=False).prefetch_related(
        'hall_of_fame_entry').distinct().annotate(entry_count=Count('hall_of_fame_entry')).order_by('-entry_count')
    for user in users:
        user_entries[user] = user.hall_of_fame_entry.all()
    if request.user.is_authenticated:
        in_hall_of_fame = HallOfFameEntry.objects.filter(user=request.user).exists()
    else:
        in_hall_of_fame = False
    return render(request, './hall_of_fame_detail.html',
                  {'user_entries': user_entries, 'in_hall_of_fame': in_hall_of_fame})


factory = RequestFactory()
custom_fake_request = factory.get('/')

"""def add_to_hall_of_fame():
    week_start = date.today() - timedelta(days=date.today().weekday())
    today = date.today()

    def at_least_50_climate_points():
        description_de = f"Hat zwischen {week_start.strftime('%d.%m.%Y')} und {today.strftime('%d.%m.%Y')} 50 oder mehr Klimapunkte gesammelt."
        description_en = f"Has collected 50 or more climate points between {week_start.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."

        qualifying_users = (
            User.objects
            .annotate(
                weekly_klimapunkte=Sum(
                    F("aktion__aktion__klimapunkte") * F("aktion__quantity"),
                    filter=Q(aktion__date__gte=week_start)
                )
            )
            .filter(weekly_klimapunkte__gte=50)
        )

        entries = [
            HallOfFameEntry(user=user, description_de=description_de, description_en=description_en)
            for user in qualifying_users
        ]

        HallOfFameEntry.objects.bulk_create(entries)

        for user in qualifying_users:
            create_notification(fake_request, notification_de="Du wurdest in die Hall of Fame aufgenommen",
                                notification_en="You have been inducted into the hall of fame", user=user)

    def top_5_climate_point_collector():
        pass

    def at_least_50_bike_kilometers():
        pass

    def vegetarian():
        pass

    def vegan():
        pass

    def created_article():  # ToDo: Create created_at field in model
        pass

    def created_event():  # ToDo: Create created_at field in model
        pass

    def created_petition():
        pass

    data = HallOfFameData.objects.get_or_create(id=1)
    if data.weeks_count == 0:
        at_least_50_climate_points()
        data.weeks_count = 1
        data.to_do_de = "Sei in der nächsten Woche einer der Top-5 Klimapunkte-Sammler"
        data.to_do_en = "Be one of the top-5 climate points collector next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 1:
        top_5_climate_point_collector()
        data.weeks_count = 2
        data.to_do_de = "Fahre nächste Woche mindestens 50 Kilometer mit dem Fahrrad"
        data.to_do_en = "Drive at least 50 kilometer by bike next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 2:
        at_least_50_bike_kilometers()
        data.weeks_count = 3
        data.to_do_de = "Ernähre dich nächste Woche vegetarisch"
        data.to_do_en = "Eat vegetarian next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 3:
        vegetarian()
        data.weeks_count = 4
        data.to_do_de = "Ernähre dich nächste Woche vegan"
        data.to_do_en = "Eat vegan next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 4:
        vegan()
        data.weeks_count = 5
        data.to_do_de = "Erstelle nächste Woche mindestens einen Artikel"
        data.to_do_en = "Create at least one article next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 5:
        created_article()
        data.weeks_count = 6
        data.to_do_de = "Erstelle nächste Woche mindestens ein Event"
        data.to_do_en = "Create at least one event next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 6:
        created_event()
        data.weeks_count = 7
        data.to_do_de = "Erstelle nächste Woche mindestens eine Petition"
        data.to_do_en = "Create at least one Petition next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    elif data.weeks_count == 7:
        created_petition()
        data.weeks_count = 0
        data.to_do_de = "Sammle nächste Woche mindestens 50 Klimapunkte"
        data.to_do_en = "Collect at least 50 climate points next week"
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(request=custom_fake_request, notification_de=data.to_do_de,
                                notification_en=data.to_do_en, user=user, url=reverse('hall_of_fame_detail'))
    else:
        data.weeks_count = 0"""


def add_to_hall_of_fame_cron() -> None:
    week_start: date = date.today() - timedelta(days=date.today().weekday())
    today: date = date.today()

    def add_to_hall_of_fame(qualifying_users: QuerySet[User], description_de: str, description_en: str) -> None:
        entries: List[HallOfFameEntry] = [
            HallOfFameEntry(user=user, description_de=description_de, description_en=description_en)
            for user in qualifying_users
        ]
        HallOfFameEntry.objects.bulk_create(entries)

        for user in qualifying_users:
            create_notification(
                fake_request,
                notification_de="Du wurdest in die Hall of Fame aufgenommen",
                notification_en="You have been inducted into the hall of fame",
                user=user,
            )

    def at_least_50_climate_points() -> None:
        description_de: str = f"Hat zwischen {week_start.strftime('%d.%m.%Y')} und {today.strftime('%d.%m.%Y')} 50 oder mehr Klimapunkte gesammelt."
        description_en: str = f"Has collected 50 or more climate points between {week_start.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."

        qualifying_users: QuerySet[User] = (
            User.objects
            .annotate(
                weekly_klimapunkte=Sum(
                    F("aktion__aktion__klimapunkte") * F("aktion__quantity"),
                    filter=Q(aktion__date__gte=week_start)
                )
            )
            .filter(weekly_klimapunkte__gte=50)
        )

        add_to_hall_of_fame(qualifying_users, description_de, description_en)

    def top_5_climate_point_collector() -> None:
        description_de: str = f"War zwischen {week_start.strftime('%d.%m.%Y')} und {today.strftime('%d.%m.%Y')} einer der Top-5 Klimapunkt-Sammler."
        description_en: str = f"Was one of the top-5 climate point collector between {week_start.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."

        family: Family = Family.objects.get(name="worldwide ranking")

        qualifying_users: QuerySet[User] = (
            family.members
            .annotate(
                total_klimapunkte=Sum(
                    F("aktion__aktion__klimapunkte") * F("aktion__quantity")
                ),
                rank=Window(
                    expression=Rank(),
                    order_by=F("total_klimapunkte").desc(),
                ),
            )
            .filter(rank__lte=5)
        )

        add_to_hall_of_fame(qualifying_users, description_de, description_en)

    def at_least_50_bike_kilometers() -> None:
        description_de: str = f"Ist zwischen {week_start.strftime('%d.%m.%Y')} und {today.strftime('%d.%m.%Y')} mindestens 50 Kilometer Fahrrad gefahren."
        description_en: str = f"Drove at least 50 kilometers by bike between {week_start.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."

        qualifying_users: QuerySet[User] = (
            User.objects.annotate(
                weekly_klimapunkte_by_bike=Sum(
                    F("aktion__aktion__klimapunkte") * F("aktion__quantity"),
                    filter=Q(aktion__date__gte=week_start) & Q(aktion__aktion__id=19),
                )
            )
            .filter(weekly_klimapunkte_by_bike__gte=50)
        )

        add_to_hall_of_fame(qualifying_users, description_de, description_en)

    def vegetarian() -> None:
        description_de: str = f"Hat sich zwischen {week_start.strftime('%d.%m.%Y')} und {today.strftime('%d.%m.%Y')} vegetarisch ernährt."
        description_en: str = f"Lived as a vegetarian between {week_start.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."

        # ...

    def vegan() -> None:
        pass

    def created_article() -> None:  # ToDo: Create created_at field in model
        pass

    def created_event() -> None:  # ToDo: Create created_at field in model
        pass

    def created_petition() -> None:
        pass

    def run_weekly_step(
            evaluation_func: Callable[[], None],
            next_weeks_count: int,
            to_do_de: str,
            to_do_en: str,
    ) -> None:
        evaluation_func()
        data.weeks_count = next_weeks_count
        data.to_do_de = to_do_de
        data.to_do_en = to_do_en
        data.save()
        for user in User.objects.all():
            custom_fake_request.user = user
            create_notification(
                request=custom_fake_request,
                notification_de=to_do_de,
                notification_en=to_do_en,
                user=user,
                url=reverse('hall_of_fame_detail'),
            )

    weekly_steps: list[tuple[Callable[[], None], int, str, str]] = [
        (at_least_50_climate_points, 1,
         "Sei in der nächsten Woche einer der Top-5 Klimapunkte-Sammler",
         "Be one of the top-5 climate points collector next week"),
        (top_5_climate_point_collector, 2,
         "Fahre nächste Woche mindestens 50 Kilometer mit dem Fahrrad",
         "Drive at least 50 kilometer by bike next week"),
        (at_least_50_bike_kilometers, 3,
         "Ernähre dich nächste Woche vegetarisch",
         "Eat vegetarian next week"),
        (vegetarian, 4,
         "Ernähre dich nächste Woche vegan",
         "Eat vegan next week"),
        (vegan, 5,
         "Erstelle nächste Woche mindestens einen Artikel",
         "Create at least one article next week"),
        (created_article, 6,
         "Erstelle nächste Woche mindestens ein Event",
         "Create at least one event next week"),
        (created_event, 7,
         "Erstelle nächste Woche mindestens eine Petition",
         "Create at least one Petition next week"),
        (created_petition, 0,
         "Sammle nächste Woche mindestens 50 Klimapunkte",
         "Collect at least 50 climate points next week"),
    ]

    data: HallOfFameData
    data, _ = HallOfFameData.objects.get_or_create(id=1)

    if 0 <= data.weeks_count < len(weekly_steps):
        run_weekly_step(*weekly_steps[data.weeks_count])
    else:
        data.weeks_count = 0
