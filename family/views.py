from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from community.models import Community
from core.all_messages import all_messages
from utils.functions import (
    WORLDWIDE_RANKING_NAME,
    get_families_of_user,
    get_klimapunkte_by_user,
)
from utils.groups import escaped, notify, require_admin_password, too_long
from utils.periods import InvalidPeriod, default_period, parse_period

from .models import Family, FamilyChatMessage


@login_required
def create_family(request):
    if request.method != "POST":
        return render(request, "./create_family.html")

    name = request.POST.get("familyname")
    password = request.POST.get("family_password")
    admin_password = request.POST.get("family_admin_password")
    if not name or not password or not admin_password:
        messages.error(request, all_messages["missing_required_inputs"])
        return redirect("create_family")
    if too_long(request, name, password, admin_password):
        return redirect("create_family")
    if Family.objects.filter(name=name).exists():
        messages.error(request, all_messages["family_exists"])
        return redirect("create_family")
    if name == WORLDWIDE_RANKING_NAME:
        messages.error(request, all_messages["family_name_forbidden"])
        return redirect("create_family")

    family = Family.objects.create(name=name, password=password, admin_password=admin_password)
    family.members.add(request.user)
    messages.success(request, all_messages["family_created"])
    return redirect("families_view")


@login_required
def join_family(request):
    if request.method != "POST":
        return render(request, "./join_family.html")

    name = request.POST.get("familyname")
    password = request.POST.get("family_password")
    if not name or not password:
        messages.error(request, all_messages["missing_required_inputs"])
        return redirect("join_family")

    family = Family.objects.filter(name=name).first()
    if family is None or not check_password(password, family.password):
        messages.error(request, all_messages["invalid_family_credentials"])
        return redirect("join_family")
    if family.members.filter(id=request.user.id).exists():
        messages.error(request, all_messages["family_already_joined"].format(familyname=family))
        return redirect("join_family")

    notify(
        request,
        family.members.exclude(id=request.user.id),
        f"User {escaped(request.user)} ist der Family {escaped(family)} beigetreten",
        f"User {escaped(request.user)} has joined the family {escaped(family)}",
        url=reverse("family_detail", args=[family.id]),
    )
    family.members.add(request.user)
    messages.success(request, all_messages["family_joined"].format(familyname=family))
    return redirect("families_view")


def get_family_or_redirect(request, family_id, not_found_redirect="families_view"):
    """``(family, None)``, or ``(None, redirect response)`` if the family does not exist."""
    family = Family.objects.filter(id=family_id).first()
    if family is None:
        messages.error(request, all_messages["family_not_found"])
        return None, redirect(not_found_redirect)
    return family, None


@login_required
def chat_family(request, family_id):
    family, response = get_family_or_redirect(request, family_id)
    if response:
        return response
    if family.name == WORLDWIDE_RANKING_NAME:
        messages.error(request, all_messages["chat_not_enabled_for_worldwide_ranking"])
        return redirect("families_view")
    if not family.chat:
        messages.error(request, all_messages["chat_disabled_for_family"])
        return redirect("family_detail", family_id=family.id)
    if not family.members.filter(id=request.user.id).exists():
        messages.error(request, all_messages["not_part_of_family"].format(familyname=family))
        return redirect("families_view")

    if request.method == "POST":
        text = request.POST.get("message")
        if text:
            FamilyChatMessage.objects.create(family=family, user=request.user, message=text)
            notify(
                request,
                family.members.exclude(id=request.user.id),
                f"Neue Nachricht in Family {escaped(family.name)} von User {escaped(request.user)}: {escaped(text)}",
                f"New message in family {escaped(family.name)} from User {escaped(request.user)}: {escaped(text)}",
                url=reverse("chat_family", args=[family_id]),
            )
        return redirect("chat_family", family_id=family.id)

    msgs = FamilyChatMessage.objects.filter(family=family).select_related("user").order_by("erstellt_am", "id")
    return render(request, "chat_family.html", {"family": family, "msgs": msgs})


@login_required
def families_view(request):
    return render(request, "./families.html", {"families": get_families_of_user(request.user)})


def _notify_others(request, family, text_de, text_en):
    notify(
        request,
        family.members.exclude(id=request.user.id),
        text_de,
        text_en,
        url=reverse("family_detail", args=[family.id]),
    )


def _change_name(request, family):
    admin_password = request.POST.get("admin_password_familyname")
    name = request.POST.get("new_familyname")
    if name is not None and too_long(request, name):
        return None
    if Family.objects.filter(name=name).exists():
        messages.error(request, all_messages["family_exists"])
        return None
    if not require_admin_password(request, admin_password, family.admin_password, name):
        return None
    old_name = family.name
    family.name = name
    family.save()
    _notify_others(
        request,
        family,
        f"Der Familyname der Family {escaped(old_name)} wurde von {escaped(request.user)} zu {escaped(name)} geändert",
        f"The family name of the family {escaped(old_name)} has been changed by {escaped(request.user)} to {escaped(name)}",
    )
    messages.success(request, all_messages["family_name_changed"])
    return None


def _change_password(request, family):
    new_password = request.POST.get("new_password")
    if too_long(request, new_password):
        return None
    if not require_admin_password(
        request, request.POST.get("admin_password_password"), family.admin_password, new_password
    ):
        return None
    family.password = new_password
    family.save()
    _notify_others(
        request,
        family,
        f"Passwort der Family {escaped(family.name)} wurde von User {escaped(request.user)} geändert",
        f"Password of family {escaped(family.name)} has been changed by {escaped(request.user)}",
    )
    messages.success(request, all_messages["family_password_changed"])
    return None


def _change_admin_password(request, family):
    new_password = request.POST.get("new_admin_password")
    if too_long(request, new_password):
        return None
    if not require_admin_password(
        request, request.POST.get("current_admin_password"), family.admin_password, new_password
    ):
        return None
    family.admin_password = new_password
    family.save()
    _notify_others(
        request,
        family,
        f"Das Family-Admin-Passwort der Family {escaped(family.name)} wurde von User {escaped(request.user)} geändert",
        f"Admin password of family {escaped(family.name)} has been changed by {escaped(request.user)}",
    )
    messages.success(request, all_messages["family_admin_password_changed"])
    return None


def _remove_member(request, family):
    username = request.POST.get("username")
    if not require_admin_password(request, request.POST.get("admin_password_remove"), family.admin_password, username):
        return None
    if username == request.user.username:
        family.members.remove(request.user)
        messages.success(request, all_messages["family_left"])
        return "families_view"
    removed = family.members.filter(username=username).first()
    if removed is None:
        messages.error(request, all_messages["family_user_not_found"])
        return "edit_family"
    family.members.remove(removed)
    notify(
        request,
        [removed],
        f"Du wurdest von User {escaped(request.user)} aus der Family {escaped(family.name)} entfernt",
        f"You have been removed from family {escaped(family.name)} by {escaped(request.user)}",
        url=reverse("families_view"),
    )
    _notify_others(
        request,
        family,
        f"User {escaped(removed)} wurde von User {escaped(request.user)} aus Family {escaped(family.name)} entfernt.",
        f"User {escaped(removed)} has been removed from family {escaped(family.name)} by {escaped(request.user)}",
    )
    messages.error(request, all_messages["family_user_removed"])
    return None


def _leave_family(request, family):
    family.members.remove(request.user)
    messages.success(request, all_messages["family_left"])
    return "families_view"


def _change_chat_settings(request, family):
    if not require_admin_password(request, request.POST.get("admin_password_chat_settings"), family.admin_password):
        return None
    family.chat = request.POST.get("chat_checkbox") == "on"
    family.save()
    messages.success(request, all_messages["family_chat_enabled" if family.chat else "family_chat_disabled"])
    return None


def _delete_family(request, family):
    if not require_admin_password(request, request.POST.get("admin_password_delete"), family.admin_password):
        return None
    notify(
        request,
        family.members.exclude(id=request.user.id),
        f"Family {escaped(family.name)} wurde von User {escaped(request.user)} gelöscht.",
        f"Family {escaped(family.name)} has been deleted by {escaped(request.user)}",
        url=reverse("families_view"),
    )
    family.delete()
    messages.success(request, all_messages["family_deleted"])
    return "families_view"


FAMILY_ACTIONS = {
    "change_familyname": _change_name,
    "change_password": _change_password,
    "change_admin_password": _change_admin_password,
    "remove_member": _remove_member,
    "leave_family": _leave_family,
    "change_chat_settings": _change_chat_settings,
    "delete_family": _delete_family,
}


@login_required
def edit_family(request, family_id):
    family, response = get_family_or_redirect(request, family_id)
    if response:
        return response
    if family.name == WORLDWIDE_RANKING_NAME:
        messages.error(request, all_messages["family_name_forbidden"])
        return redirect("families_view")
    if not family.members.filter(id=request.user.id).exists():
        messages.error(request, all_messages["not_part_of_family"].format(familyname=family))
        return redirect("families_view")

    if request.method == "POST":
        for button, handler in FAMILY_ACTIONS.items():
            if button in request.POST:
                target = handler(request, family)
                if target == "edit_family":
                    return redirect("edit_family", family_id)
                if target:
                    return redirect(target)
    return render(request, "edit_family.html", {"family": family})


def can_view_family(user, family):
    """Members may see their family; so may members of other families in a shared community."""
    if family.members.filter(id=user.id).exists():
        return True
    return Community.objects.filter(members=family).filter(members__in=get_families_of_user(user)).exists()


@login_required
def family_detail(request, family_id):
    family = Family.objects.filter(id=family_id).first()
    if family is None:
        messages.error(request, all_messages["family_not_found"])
        return redirect("families_view")
    if not can_view_family(request.user, family):
        messages.error(request, all_messages["not_part_of_family"].format(familyname=family.name))
        return redirect("families_view")

    period = default_period()
    if request.method == "POST":
        try:
            period = parse_period(request.POST, request.LANGUAGE_CODE, timezone.localdate())
        except InvalidPeriod as error:
            messages.error(request, error.message)
            return redirect("family_detail", family_id)

    members = list(family.members.all())
    points = get_klimapunkte_by_user(
        [member.id for member in members], period.start, period.end, include_additional=period.is_total
    )
    ranking = sorted(
        ({"member": member, "klimapunkte": points[member.id]} for member in members),
        key=lambda row: row["klimapunkte"],
        reverse=True,
    )
    total = sum(row["klimapunkte"] for row in ranking)
    return render(
        request,
        "./family_detail.html",
        {
            "family": family,
            "members": ranking,
            "zeitraum": period.text,
            "average_klimapunkte": total / len(ranking) if ranking else 0,
            "total_klimapunkte": total,
            "members_count": len(ranking),
        },
    )


@login_required
def check_familyname(request):
    return JsonResponse({"exists": Family.objects.filter(name=request.GET.get("familyname")).exists()})
