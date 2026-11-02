from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from core.all_messages import all_messages
from family.models import Family
from utils.functions import get_families_of_user, get_klimapunkte_by_user
from utils.groups import escaped, notify, require_admin_password, too_long
from utils.periods import InvalidPeriod, default_period, parse_period

from .models import Community, CommunityChatMessage


def community_detail_url(community):
    """``user -> url`` of the community page seen through the user's first family in that community."""
    first_family_of_user = {}
    for family in community.members.prefetch_related("members").order_by("id"):
        for member in family.members.all():
            first_family_of_user.setdefault(member.id, family.id)

    def url(user):
        family_id = first_family_of_user.get(user.id)
        return (
            reverse("community_detail", kwargs={"community_id": community.id, "family_id": family_id})
            if family_id
            else None
        )

    return url


def notify_community(request, community, text_de, text_en, exclude_requester=True):
    users = community.user_members()
    if exclude_requester:
        users = users.exclude(id=request.user.id)
    notify(request, users, text_de, text_en, url=community_detail_url(community))


def credentials_ok(request, family_name, family_admin_password, redirect_name):
    """Look up the family and verify its admin password. Returns ``(family, None)`` or ``(None, redirect)``."""
    family = Family.objects.filter(name=family_name).first()
    if family is None or not check_password(family_admin_password, family.admin_password):
        messages.error(request, all_messages["community__invalid_family_credentials"])
        return None, redirect(redirect_name)
    return family, None


def announce_family_joined(request, family, community):
    notify(
        request,
        family.members.exclude(id=request.user.id),
        f"Die Family {escaped(family.name)}, in der auch du Mitglied bist, ist der Community {escaped(community.name)} beigetreten",
        f"The family {escaped(family.name)}, of which you are also a member, has joined the community {escaped(community.name)}",
        url=reverse("community_detail", kwargs={"community_id": community.id, "family_id": family.id}),
    )


@login_required
def create_community(request):
    if request.method != "POST":
        return render(request, "./create_community.html")

    post = request.POST
    name = post.get("communityname")
    password = post.get("community_password")
    admin_password = post.get("community_admin_password")
    family_name = post.get("familyname")
    family_admin_password = post.get("family_admin_password")

    if not all([name, password, admin_password, family_name, family_admin_password]):
        messages.error(request, all_messages["missing_required_inputs"])
        return redirect("create_community")
    if too_long(request, name, password, admin_password):
        return redirect("create_community")
    if Community.objects.filter(name=name).exists():
        messages.error(request, all_messages["community_exists"])
        return redirect("create_community")
    family, response = credentials_ok(request, family_name, family_admin_password, "create_community")
    if response:
        return response

    community = Community.objects.create(name=name, password=password, admin_password=admin_password)
    community.members.add(family)
    announce_family_joined(request, family, community)
    messages.success(request, all_messages["community_created"])
    return redirect("communities_view")


@login_required
def join_community(request):
    if request.method != "POST":
        return render(request, "./join_community.html")

    post = request.POST
    community_name = post.get("communityname")
    community_password = post.get("community_password")
    if not all([community_name, community_password, post.get("familyname"), post.get("family_admin_password")]):
        messages.error(request, all_messages["missing_required_inputs"])
        return redirect("join_community")
    family, response = credentials_ok(request, post["familyname"], post["family_admin_password"], "join_community")
    if response:
        return response

    community = Community.objects.filter(name=community_name).first()
    if community is None or not check_password(community_password, community.password):
        messages.error(request, all_messages["invalid_community_credentials"])
        return redirect("join_community")
    if community.members.filter(id=family.id).exists():
        messages.error(request, all_messages["family_already_in_community"])
        return redirect("join_community")

    announce_family_joined(request, family, community)
    community.members.add(family)
    messages.success(request, all_messages["community_joined"].format(family=family, community=community))
    return redirect("communities_view")


@login_required
def communities_view(request):
    user_families = list(get_families_of_user(request.user))
    user_family_ids = {family.id for family in user_families}
    communities = (
        Community.objects.filter(members__in=user_family_ids).distinct().order_by("name").prefetch_related("members")
    )
    rows = [
        {"community": community, "families": [f for f in community.members.all() if f.id in user_family_ids]}
        for community in communities
    ]
    return render(request, "./communities.html", {"communities_with_user_families": rows})


def get_community_and_family(request, community_id, family_id):
    """Community and one of the user's families that belongs to it, or a redirect response to return."""
    community = Community.objects.filter(id=community_id).first()
    if community is None:
        messages.error(request, all_messages["community_not_found"])
        return None, None, redirect("communities_view")
    family = Family.objects.filter(id=family_id).first()
    if family is None:
        messages.error(request, all_messages["community__family_not_found"])
        return None, None, redirect("communities_view")
    if not family.members.filter(id=request.user.id).exists():
        messages.error(request, all_messages["community__not_member_of_family"])
        return None, None, redirect("dashboard")
    if not community.members.filter(id=family.id).exists():
        messages.error(request, all_messages["community__family_not_in_community"])
        return None, None, redirect("communities_view")
    return community, family, None


def _change_name(request, community, family):
    name = request.POST.get("new_communityname")
    if name is not None and too_long(request, name):
        return None
    if Community.objects.filter(name=name).exists():
        messages.error(request, all_messages["community_exists"])
        return None
    if not require_admin_password(
        request, request.POST.get("admin_password_communityname"), community.admin_password, name
    ):
        return None
    old_name = community.name
    community.name = name
    community.save()
    messages.success(request, all_messages["community_name_changed"])
    notify_community(
        request,
        community,
        f"Der Communityname der Community {escaped(old_name)} wurde von {escaped(request.user)} zu {escaped(name)} geändert",
        f"The community name of the community {escaped(old_name)} has been changed by {escaped(request.user)} to {escaped(name)}",
    )
    return None


def _change_password(request, community, family):
    new_password = request.POST.get("new_password")
    if too_long(request, new_password):
        return None
    if not require_admin_password(
        request, request.POST.get("admin_password_password"), community.admin_password, new_password
    ):
        return None
    community.password = new_password
    community.save()
    notify_community(
        request,
        community,
        f"Das Passwort der Community {escaped(community.name)} wurde von {escaped(request.user)} geändert.",
        f"The password of the community {escaped(community.name)} has been changed by {escaped(request.user)}.",
    )
    messages.success(request, all_messages["community_password_changed"])
    return None


def _change_admin_password(request, community, family):
    new_password = request.POST.get("new_admin_password")
    if too_long(request, new_password):
        return None
    if not require_admin_password(
        request, request.POST.get("current_admin_password"), community.admin_password, new_password
    ):
        return None
    community.admin_password = new_password
    community.save()
    notify_community(
        request,
        community,
        f"Das Admin-Passwort der Community {escaped(community.name)} wurde von {escaped(request.user)} geändert",
        f"The admin password of the community {escaped(community.name)} has been changed by {escaped(request.user)}.",
    )
    messages.success(request, all_messages["community_admin_password_changed"])
    return None


def _announce_family_removed(request, community, removed_family):
    notify_community(
        request,
        community,
        f"Die Family {escaped(removed_family.name)} wurde von {escaped(request.user)} aus der Community {escaped(community.name)} entfernt",
        f"The family {escaped(removed_family.name)} has been removed from the community {escaped(community.name)} by {escaped(request.user)}.",
    )


def _remove_family(request, community, family):
    family_name = request.POST.get("family_name")
    if not require_admin_password(
        request, request.POST.get("admin_password_remove"), community.admin_password, family_name
    ):
        return None
    removed = community.members.filter(name=family_name).first()
    if removed is None:
        messages.error(request, all_messages["community__family_not_found"])
        return "edit_community"
    _announce_family_removed(request, community, removed)
    community.members.remove(removed)
    if removed.id == family.id:
        messages.success(request, all_messages["family_left_community"])
        return "dashboard"
    messages.success(request, all_messages["community__family_removed"])
    return None


def _leave_community(request, community, family):
    if not require_admin_password(request, request.POST.get("family_admin_password"), family.admin_password):
        return None
    _announce_family_removed(request, community, family)
    community.members.remove(family)
    messages.success(request, all_messages["family_left_community"])
    return "dashboard"


def _change_chat_settings(request, community, family):
    if not require_admin_password(request, request.POST.get("admin_password_chat_settings"), community.admin_password):
        return None
    community.chat = request.POST.get("chat_checkbox") == "on"
    community.save()
    messages.success(request, all_messages["community_chat_enabled" if community.chat else "community_chat_disabled"])
    return None


def _delete_community(request, community, family):
    if not require_admin_password(request, request.POST.get("admin_password_delete"), community.admin_password):
        return None
    notify_community(
        request,
        community,
        f"Die Community {escaped(community.name)} wurde von {escaped(request.user)} gelöscht",
        f"The community {escaped(community.name)} has been deleted by {escaped(request.user)}.",
    )
    community.delete()
    messages.success(request, all_messages["community_deleted"])
    return "dashboard"


COMMUNITY_ACTIONS = {
    "change_communityname": _change_name,
    "change_password": _change_password,
    "change_admin_password": _change_admin_password,
    "remove_member": _remove_family,
    "leave_community": _leave_community,
    "change_chat_settings": _change_chat_settings,
    "delete_community": _delete_community,
}


@login_required
def edit_community(request, community_id, family_id):
    community, family, response = get_community_and_family(request, community_id, family_id)
    if response:
        return response

    if request.method == "POST":
        for button, handler in COMMUNITY_ACTIONS.items():
            if button in request.POST:
                target = handler(request, community, family)
                if target == "edit_community":
                    return redirect("edit_community", community_id, family_id)
                if target:
                    return redirect(target)
    return render(request, "edit_community.html", {"community": community, "family": family})


@login_required
def chat_community(request, community_id, family_id):
    community, family, response = get_community_and_family(request, community_id, family_id)
    if response:
        return response
    if not community.chat:
        messages.error(request, all_messages["chat_disabled_for_community"])
        return redirect("community_detail", community_id=community_id, family_id=family_id)

    if request.method == "POST":
        text = request.POST.get("message")
        if text:
            CommunityChatMessage.objects.create(community=community, user=request.user, message=text, family=family)
            notify_community(
                request,
                community,
                f"Neue Nachricht in Community {escaped(community.name)} von Family {escaped(family.name)} / User {escaped(request.user)}: {escaped(text)}",
                f"New message in community {escaped(community.name)} from family {escaped(family.name)} / User {escaped(request.user)}: {escaped(text)}",
            )
        return redirect("chat_community", community_id=community.id, family_id=family.id)

    msgs = CommunityChatMessage.objects.filter(community=community).select_related("user", "family")
    return render(
        request,
        "chat_community.html",
        {"community": community, "msgs": msgs.order_by("erstellt_am", "id"), "family": family},
    )


@login_required
def community_detail(request, community_id, family_id):
    community, family, response = get_community_and_family(request, community_id, family_id)
    if response:
        return response

    period = default_period()
    if request.method == "POST":
        try:
            period = parse_period(request.POST, request.LANGUAGE_CODE, timezone.localdate())
        except InvalidPeriod as error:
            messages.error(request, error.message)
            return redirect("community_detail", community_id, family_id)

    families = list(community.members.prefetch_related("members"))
    user_ids = {member.id for family_ in families for member in family_.members.all()}
    points = get_klimapunkte_by_user(user_ids, period.start, period.end)
    ranking = [
        {
            "member": family_,
            "klimapunkte": sum(points[member.id] for member in family_.members.all()) / len(family_.members.all())
            if family_.members.all()
            else 0,
        }
        for family_ in families
    ]
    ranking.sort(key=lambda row: row["klimapunkte"], reverse=True)
    return render(
        request,
        "./community_detail.html",
        {"community": community, "family": family, "members_with_klimapunkte": ranking, "zeitraum": period.text},
    )


@login_required
def check_communityname(request):
    return JsonResponse({"exists": Community.objects.filter(name=request.GET.get("communityname")).exists()})
