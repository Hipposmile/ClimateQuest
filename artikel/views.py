from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from core.all_messages import all_messages
from utils.functions import clean_html, parse_id

from .models import Answer, Artikel, Category, Comment

MAX_NAME_LENGTH = 100
DEFAULT_BLOCK_MESSAGE = "Dieser Artikel enthält Fake News"
ALL_CATEGORIES = "Alle"


def artikel_overview(request):
    all_categories = Category.objects.values_list("title", flat=True)
    all_artikel = (
        Artikel.objects.select_related("creator", "category")
        .prefetch_related("like")
        .annotate(num_likes=Count("like", distinct=True))
    )
    order_by_name = "name_de" if request.LANGUAGE_CODE == "de" else "name_en"
    search_keyword = None

    if request.method != "POST":
        return render(
            request,
            "artikel_overview.html",
            {
                "artikel": all_artikel.order_by("name_de"),
                "ordered_by": "Name",
                "search_keyword": None,
                "category": ALL_CATEGORIES,
                "all_categories": all_categories,
            },
        )

    category = request.POST.get("category")
    if category != ALL_CATEGORIES:
        all_artikel = all_artikel.filter(category__title=category)
    ordered_by = request.POST.get("order_by")
    search_keyword = request.POST.get("search_keyword")
    user = request.user if request.user.is_authenticated else None

    if ordered_by == "von mir erstellte Artikel":
        artikel = all_artikel.filter(creator=user) if user else all_artikel.none()
        artikel = artikel.order_by(order_by_name)
    elif ordered_by == "von mir gelikte Artikel":
        artikel = all_artikel.filter(like=user) if user else all_artikel.none()
        artikel = artikel.order_by(order_by_name)
    elif ordered_by == "Zuletzt bearbeitet":
        if search_keyword:
            all_artikel = all_artikel.filter(updated_at__icontains=search_keyword)
        artikel = all_artikel.order_by("-updated_at")
    elif ordered_by == "Likes":
        if search_keyword:
            try:
                search_keyword = int(search_keyword)
            except ValueError:
                messages.error(request, all_messages["likes_search_keyword_not_a_number"])
                return redirect("artikel_overview")
            all_artikel = all_artikel.filter(num_likes__icontains=search_keyword)
        artikel = all_artikel.order_by("-num_likes")
    else:
        order_by = "creator__username" if ordered_by == "Ersteller" else order_by_name
        if search_keyword:
            all_artikel = all_artikel.filter(**{f"{order_by}__icontains": search_keyword})
        artikel = all_artikel.order_by(order_by)

    return render(
        request,
        "artikel_overview.html",
        {
            "artikel": artikel,
            "ordered_by": ordered_by,
            "search_keyword": search_keyword,
            "category": category,
            "all_categories": all_categories,
        },
    )


def read_artikel_form(request):
    """Validated form values of the add/edit article form as a dict, or None after flashing the problem."""
    post = request.POST
    if post.get("is_truth") != "on":
        messages.error(request, all_messages["not_is_truth"])
        return None
    values = {field: post.get(field) or "" for field in ("name_de", "name_en", "content_de", "content_en")}
    if not all(values.values()):
        messages.error(request, all_messages["missing_required_inputs"])
        return None
    if len(values["name_de"]) > MAX_NAME_LENGTH or len(values["name_en"]) > MAX_NAME_LENGTH:
        messages.error(request, all_messages["too_long_input"])
        return None
    category = Category.objects.filter(title=post.get("category")).first()
    if category is None:
        messages.error(request, all_messages["internal_error"])
        return None
    values["content_de"] = clean_html(values["content_de"])
    values["content_en"] = clean_html(values["content_en"])
    return {**values, "category": category}


@login_required
def add_artikel(request):
    if request.method == "POST":
        values = read_artikel_form(request)
        if values is None:
            return redirect("add_artikel")
        artikel = Artikel.objects.create(creator=request.user, **values)
        messages.success(request, all_messages["successfully_created_artikel"])
        return redirect("artikel_detail", artikel.id)
    return render(request, "add_artikel.html", {"categories": Category.objects.values_list("title", flat=True)})


@login_required
def edit_artikel(request, artikel_id):
    artikel = Artikel.objects.filter(id=artikel_id).first()
    if artikel is None:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect("artikel_overview")
    if artikel.creator != request.user:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect("artikel_detail", artikel.id)

    if request.method == "POST":
        if "edit_artikel" in request.POST:
            values = read_artikel_form(request)
            if values is None:
                return redirect("edit_artikel", artikel_id=artikel_id)
            for field, value in values.items():
                setattr(artikel, field, value)
            artikel.save()
            messages.success(request, all_messages["successfully_edited_artikel"])
            return redirect("artikel_detail", artikel_id=artikel.id)
        if "delete_artikel" in request.POST:
            artikel.delete()
            messages.success(request, all_messages["successfully_deleted_artikel"])
            return redirect("artikel_overview")
    return render(
        request,
        "edit_artikel.html",
        {"artikel": artikel, "categories": Category.objects.values_list("title", flat=True)},
    )


def _comment_on_artikel(request, artikel):
    text = (request.POST.get("comment") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    artikel.comments.add(Comment.objects.create(comment=text, user=request.user))
    messages.success(request, all_messages["successfully_asked_comment"])


def _answer_comment(request, artikel):
    comment = artikel.comments.filter(id=parse_id(request.POST.get("comment_id"))).first()
    if comment is None:
        messages.error(request, all_messages["internal_error"])
        return
    text = (request.POST.get("answer") or "").strip()
    if not text:
        messages.error(request, all_messages["missing_required_inputs"])
        return
    comment.answers.add(Answer.objects.create(answer=text, user=request.user))
    messages.success(request, all_messages["successfully_answered_comment"])


def _toggle_verified(request, artikel):
    if artikel.verified:
        artikel.verified = False
        messages.success(request, all_messages["successfully_unverified_article"])
    else:
        artikel.blocked = False
        artikel.verified = True
        messages.success(request, all_messages["successfully_verified_article"])
    artikel.save()


def _toggle_blocked(request, artikel):
    if artikel.blocked:
        artikel.blocked = False
        messages.success(request, all_messages["successfully_unblocked_article"])
    else:
        artikel.verified = False
        artikel.msg_if_wrong = request.POST.get("block_msg") or DEFAULT_BLOCK_MESSAGE
        artikel.blocked = True
        messages.success(request, all_messages["successfully_blocked_article"])
    artikel.save()


def artikel_detail(request, artikel_id):
    artikel = (
        Artikel.objects.select_related("creator", "category")
        .prefetch_related("comments__user", "comments__answers__user")
        .filter(id=artikel_id)
        .first()
    )
    if artikel is None:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect("artikel_overview")

    if request.method == "POST" and request.user.is_authenticated:
        post = request.POST
        handler = None
        if "add_comment" in post:
            handler = _comment_on_artikel
        elif "answer_comment" in post:
            handler = _answer_comment
        elif request.user.is_staff and "verify" in post:
            handler = _toggle_verified
        elif request.user.is_staff and "block" in post:
            handler = _toggle_blocked
        if handler:
            handler(request, artikel)
            return redirect("artikel_detail", artikel_id)

    has_liked = request.user.is_authenticated and artikel.like.filter(id=request.user.id).exists()
    return render(request, "artikel_detail.html", {"artikel": artikel, "has_liked": has_liked})


@login_required
def add_like(request, artikel_id):
    artikel = Artikel.objects.filter(id=artikel_id).first()
    if artikel is None:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect("artikel_overview")
    if request.user == artikel.creator:
        messages.error(request, all_messages["not_allowed_to_like_own_article"])
    elif artikel.like.filter(id=request.user.id).exists():
        artikel.like.remove(request.user)
        messages.success(request, all_messages["successfully_removed_like"])
    else:
        artikel.like.add(request.user)
        messages.success(request, all_messages["successfully_added_like"])
    return redirect("artikel_detail", artikel_id)
