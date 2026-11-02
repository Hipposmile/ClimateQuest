from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from core.all_messages import all_messages
from utils.functions import clean_html, create_notification

from .models import Answer, Category, ForumPost

MAX_TITLE_LENGTH = 100
ALL_CATEGORIES = "Alle"
ORDER_FIELDS = {"Titel": "title", "Ersteller": "creator__username"}


def forum_overview(request):
    all_categories = Category.objects.values_list("title", flat=True)
    forum_posts = ForumPost.objects.select_related("creator", "category").prefetch_related("answers")

    if request.method != "POST":
        return render(
            request,
            "./forum_overview.html",
            {
                "forum_posts": forum_posts.order_by("title", "pk"),
                "ordered_by": "Titel",
                "search_keyword": None,
                "category": ALL_CATEGORIES,
                "all_categories": all_categories,
            },
        )

    category = request.POST.get("category")
    if category != ALL_CATEGORIES:
        forum_posts = forum_posts.filter(category__title=category)
    ordered_by = request.POST.get("order_by")
    search_keyword = request.POST.get("search_keyword")
    user = request.user if request.user.is_authenticated else None

    if ordered_by == "von mir erstellte Posts":
        forum_posts = forum_posts.filter(creator=user) if user else forum_posts.none()
        forum_posts = forum_posts.order_by("title", "pk")
    elif ordered_by == "von mir beantwortete Posts":
        forum_posts = forum_posts.filter(answers__creator=user).distinct() if user else forum_posts.none()
        forum_posts = forum_posts.order_by("title", "pk")
    elif ordered_by == "Erstellt am":
        if search_keyword:
            forum_posts = forum_posts.filter(date_time__icontains=search_keyword)
        forum_posts = forum_posts.order_by("-date_time", "pk")
    else:
        order_by = ORDER_FIELDS.get(ordered_by, "title")
        if search_keyword:
            forum_posts = forum_posts.filter(**{f"{order_by}__icontains": search_keyword})
        forum_posts = forum_posts.order_by(order_by, "pk")

    return render(
        request,
        "./forum_overview.html",
        {
            "forum_posts": forum_posts,
            "ordered_by": ordered_by,
            "search_keyword": search_keyword,
            "category": category,
            "all_categories": all_categories,
        },
    )


@login_required
def add_forum_post(request):
    if request.method == "POST":
        if request.POST.get("is_truth") != "on":
            messages.error(request, all_messages["not_is_truth"])
            return redirect("add_forum_post")
        title = request.POST.get("title") or ""
        content = request.POST.get("content") or ""
        category = Category.objects.filter(title=request.POST.get("category")).first()
        if category is None:
            messages.error(request, all_messages["internal_error"])
            return redirect("add_forum_post")
        if not title or not content:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect("add_forum_post")
        if len(title) > MAX_TITLE_LENGTH:
            messages.error(request, all_messages["too_long_input"])
            return redirect("add_forum_post")
        post = ForumPost.objects.create(
            title=title, content=clean_html(content), creator=request.user, category=category
        )
        return redirect("post_detail", post.id)
    return render(request, "./add_forum_post.html", {"categories": Category.objects.values_list("title", flat=True)})


def post_detail(request, post_id):
    post = ForumPost.objects.select_related("creator", "category").filter(id=post_id).first()
    if post is None:
        messages.error(request, all_messages["post_not_found"])
        return redirect("forum_overview")

    if request.method == "POST" and request.user.is_authenticated:
        if request.POST.get("is_truth") != "on":
            messages.error(request, all_messages["not_is_truth"])
            return redirect("post_detail", post_id=post_id)
        content = request.POST.get("content")
        if not content:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect("post_detail", post_id=post_id)
        Answer.objects.create(content=clean_html(content), creator=request.user, forum_post=post)
        create_notification(
            request=request,
            notification_de="Deine Forumsfrage wurde beantwortet",
            notification_en="Your forum question has been answered",
            user=post.creator,
            url=reverse("post_detail", args=[post_id]),
        )
        return redirect("post_detail", post_id=post_id)

    return render(
        request,
        "./forum_detail.html",
        {"post": post, "answers": post.answers.select_related("creator").order_by("date_time", "id")},
    )
