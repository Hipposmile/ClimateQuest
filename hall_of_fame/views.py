from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.shortcuts import render

from hall_of_fame.models import HallOfFameData, HallOfFameEntry
from hall_of_fame.services import run_weekly_hall_of_fame


def hall_of_fame_detail(request):
    data, _ = HallOfFameData.objects.get_or_create(id=1)
    to_to_next_week = {"de": data.to_do_de, "en": data.to_do_en}

    users = (
        User.objects.filter(hall_of_fame_entry__isnull=False)
        .annotate(entry_count=Count("hall_of_fame_entry"))
        .order_by("-entry_count", "username")
        .prefetch_related(
            Prefetch(
                "hall_of_fame_entry",
                queryset=HallOfFameEntry.objects.order_by("-created_at", "-id"),
                to_attr="ordered_entries",
            )
        )
    )
    user_entries = {user: user.ordered_entries for user in users}
    if request.user.is_authenticated:
        in_hall_of_fame = HallOfFameEntry.objects.filter(user=request.user).exists()
    else:
        in_hall_of_fame = False
    return render(
        request,
        "./hall_of_fame_detail.html",
        {"user_entries": user_entries, "in_hall_of_fame": in_hall_of_fame, "to_to_next_week": to_to_next_week},
    )


def add_to_hall_of_fame_cron() -> None:
    """Cron entry point (referenced by ``CRONJOBS`` in the production settings)."""
    run_weekly_hall_of_fame()
