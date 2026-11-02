from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import reverse

from core.all_messages import all_messages
from utils.functions import check_is_truth, clean_html, create_notification, parse_id

from .models import Answer, Category, Comment, Petition, Update

MIN_GOAL = 10
MAX_GOAL = 2_000_000_000  # fits the database integer column
ALL_CATEGORIES = "Alle"
ORDER_FIELDS = {"Titel": "title", "Ersteller": "creator__username"}


def read_goal(request, goal):
    """Parse a petition goal. Returns the integer, or None after flashing the problem."""
    try:
        value = int(goal)
    except (TypeError, ValueError):
        messages.error(request, all_messages["goal_not_a_number"])
        return None
    if value < MIN_GOAL:
        messages.error(request, all_messages["goal_too_small"])
        return None
    if value > MAX_GOAL:
        messages.error(request, all_messages["goal_too_big"])
        return None
    return value


@login_required
def add_petition(request):
    if request.method == "POST":
        post = request.POST
        if not check_is_truth(request):
            return redirect("add_petition")
        fields = {name: post.get(name) or "" for name in ("title_de", "title_en", "content_de", "content_en", "goal")}
        if not all(fields.values()):
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect("add_petition")
        goal = read_goal(request, fields["goal"])
        if goal is None:
            return redirect("add_petition")
        category = Category.objects.filter(title=post.get("category")).first()
        if category is None:
            messages.error(request, all_messages["internal_error"])
            return redirect("add_petition")
        petition = Petition.objects.create(
            title_de=fields["title_de"],
            title_en=fields["title_en"],
            content_de=clean_html(fields["content_de"]),
            content_en=clean_html(fields["content_en"]),
            goal=goal,
            category=category,
            creator=request.user,
        )
        messages.success(request, all_messages["petition_added"])
        return redirect("petition_detail", petition.id)
    return render(request, "./add_petition.html", {"categories": Category.objects.order_by("title", "pk")})


def _toggle_signature(request, petition):
    if petition.signs.filter(id=request.user.id).exists():
        petition.signs.remove(request.user)
        messages.success(request, all_messages["petition_unsigned"])
    else:
        petition.signs.add(request.user)
        messages.success(request, all_messages["petition_signed"])


def _comment(request, petition):
    text = (request.POST.get("comment") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    petition.comments.add(Comment.objects.create(comment=text, user=request.user))
    messages.success(request, all_messages["successfully_asked_comment"])


def _answer_comment(request, petition):
    comment = petition.comments.filter(id=parse_id(request.POST.get("comment_id"))).first()
    if comment is None:
        messages.error(request, all_messages["internal_error"])
        return
    text = (request.POST.get("answer") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    comment.answers.add(Answer.objects.create(answer=text, user=request.user))
    messages.success(request, all_messages["successfully_answered_comment"])


PETITION_ACTIONS = {"sign": _toggle_signature, "add_comment": _comment, "answer_comment": _answer_comment}


def petition_detail(request, petition_id):
    petition = (
        Petition.objects.select_related("creator", "category")
        .prefetch_related("signs", "updates", "comments__user", "comments__answers__user")
        .filter(id=petition_id)
        .first()
    )
    if petition is None:
        messages.error(request, all_messages["petition_not_found"])
        return redirect("petitions_overview")

    if request.method == "POST" and request.user.is_authenticated:
        for button, handler in PETITION_ACTIONS.items():
            if button in request.POST:
                handler(request, petition)
                return redirect("petition_detail", petition_id)
    return render(request, "./petition_detail.html", {"petition": petition})


def _notify_signers(request, petition, text_de, text_en):
    url = reverse("petition_detail", args=(petition.id,))
    for user in petition.signs.all():
        create_notification(request, text_de, text_en, user, url)


def _add_update(request, petition):
    post = request.POST
    if not check_is_truth(request):
        return "edit_petition"
    values = {name: post.get(name) or "" for name in ("title_de", "title_en", "content_de", "content_en")}
    if not all(values.values()):
        messages.error(request, all_messages["missing_required_inputs"])
        return "edit_petition"
    petition.updates.add(
        Update.objects.create(
            title_de=values["title_de"],
            title_en=values["title_en"],
            content_de=clean_html(values["content_de"]),
            content_en=clean_html(values["content_en"]),
        )
    )
    _notify_signers(
        request,
        petition,
        f"Der Petition {petition.title}, die du unterschrieben hast, wurde ein Update hinzugefügt!",
        f"A new update has been added to the petition {petition.title}, which you signed!",
    )
    return "petition_detail"


def _change_goal(request, petition):
    if not request.POST.get("goal"):
        messages.error(request, all_messages["missing_required_inputs"])
        return "petition_detail"
    goal = read_goal(request, request.POST.get("goal"))
    if goal is None:
        return "add_petition"
    petition.goal = goal
    petition.save()
    messages.success(request, all_messages["successfully_updated_goal"])
    return "petition_detail"


def _toggle_success(request, petition):
    petition.success = not petition.success
    petition.save()
    if petition.success:
        messages.success(request, all_messages["added_success"])
        _notify_signers(
            request,
            petition,
            f"Die Petition {petition.title}, die du unterschrieben hast, war erfolgreich!",
            f"The petition {petition.title}, which you signed, was successful!",
        )
    else:
        messages.error(request, all_messages["removed_success"])
        _notify_signers(
            request,
            petition,
            f"Von der Petition {petition.title}, die du unterschrieben hast, wurde der Erfolg gelöscht!",
            f"The success of the petition {petition.title}, which you signed, was removed!",
        )
    return "petition_detail"


EDIT_ACTIONS = {"update": _add_update, "change_goal": _change_goal, "success": _toggle_success}


@login_required
def edit_petition(request, petition_id):
    petition = Petition.objects.filter(id=petition_id).first()
    if petition is None:
        messages.error(request, all_messages["petition_not_found"])
        return redirect("petitions_overview")
    if request.user != petition.creator:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect("add_petition")

    if request.method == "POST":
        for button, handler in EDIT_ACTIONS.items():
            if button in request.POST:
                return _redirect(handler(request, petition), petition_id)
    return render(request, "./edit_petition.html", {"petition": petition})


def _redirect(view_name, petition_id):
    """``add_petition`` is where invalid goals send the user (kept from the original behaviour)."""
    return redirect(view_name) if view_name == "add_petition" else redirect(view_name, petition_id)


def petitions_overview(request):
    all_categories = Category.objects.values_list("title", flat=True)
    petitions = Petition.objects.select_related("creator", "category").prefetch_related("signs")

    if request.method != "POST":
        return render(
            request,
            "./petitions_overview.html",
            {
                "petitions": petitions.filter(success=False).order_by("title", "pk"),
                "ordered_by": "Titel",
                "category": ALL_CATEGORIES,
                "search_keyword": None,
                "success_visible": False,
                "all_categories": all_categories,
            },
        )

    success_visible = request.POST.get("success_visible") == "on"
    if not success_visible:
        petitions = petitions.filter(success=False)
    category = request.POST.get("category")
    if category != ALL_CATEGORIES:
        petitions = petitions.filter(category__title=category)
    ordered_by = request.POST.get("order_by")
    search_keyword = request.POST.get("search_keyword")
    user = request.user if request.user.is_authenticated else None

    if ordered_by == "von mir erstellte Petitionen":
        petitions = (petitions.filter(creator=user) if user else petitions.none()).order_by("title", "pk")
    elif ordered_by == "von mir unterschriebene Petitionen":
        petitions = (petitions.filter(signs=user) if user else petitions.none()).order_by("title", "pk")
    elif ordered_by == "Erstellt am":
        if search_keyword:
            petitions = petitions.filter(created_at__icontains=search_keyword)
        petitions = petitions.order_by("-created_at", "pk")
    elif ordered_by == "Unterschriften":
        petitions = petitions.annotate(num_signs=Count("signs", distinct=True))
        if search_keyword:
            try:
                search_keyword = int(search_keyword)
            except ValueError:
                messages.error(request, all_messages["signs_search_keyword_not_a_number"])
                return redirect("petitions_overview")
            petitions = petitions.filter(num_signs__icontains=search_keyword)
        petitions = petitions.order_by("-num_signs", "pk")
    else:
        order_by = ORDER_FIELDS.get(ordered_by, "title")
        if search_keyword:
            petitions = petitions.filter(**{f"{order_by}__icontains": search_keyword})
        petitions = petitions.order_by(order_by, "pk")

    return render(
        request,
        "./petitions_overview.html",
        {
            "petitions": petitions,
            "ordered_by": ordered_by,
            "category": category,
            "search_keyword": search_keyword,
            "success_visible": success_visible,
            "all_categories": all_categories,
        },
    )
