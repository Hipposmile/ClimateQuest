from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import Count, F, Sum, Q
from django.shortcuts import render

from hall_of_fame.models import HallOfFameEntry


# Create your views here.
def intro(request):
    return render(request, './intro.html')


def hall_of_fame_detail(request):
    user_entries = {}
    users = User.objects.filter(hall_of_fame_entry__isnull=False).prefetch_related(
        'hall_of_fame_entry').distinct().annotate(entry_count=Count('hall_of_fame_entry')).order_by('-entry_count')
    for user in users:
        user_entries[user] = user.hall_of_fame_entry.all()
    return render(request, './hall_of_fame_detail.html', {'user_entries': user_entries})


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
        .filter(weekly_klimapunkte__gte=150)
    )

    entries = [
        HallOfFameEntry(user=user, description_de=description_de, description_en=description_en)
        for user in qualifying_users
    ]
    HallOfFameEntry.objects.bulk_create(entries)
