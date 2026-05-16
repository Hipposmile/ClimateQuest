from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import Count, F, Sum, Q
from django.shortcuts import render

from core.views import fake_request
from hall_of_fame.models import HallOfFameEntry
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
    return render(request, './hall_of_fame_detail.html', {'user_entries': user_entries, 'in_hall_of_fame': in_hall_of_fame})


def add_to_hall_of_fame():
    week_start = date.today() - timedelta(days=date.today().weekday())
    description_de = f"Hat zwischen {week_start.strftime('%d.%m.%Y')} und {date.today().strftime('%d.%m.%Y')} 150 oder mehr Klimapunkte gesammelt."
    description_en = f"Has collected 150 or more climate points between {week_start.strftime('%m/%d/%Y')} and {date.today().strftime('%m/%d/%Y')}."

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
        create_notification(fake_request, notification_de="Du wurdest in die Hall of Fame aufgenommen", notification_en="You have been inducted into the hall of fame", user=user)

