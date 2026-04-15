from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from core.all_messages import all_messages

from utils.functions import clean_html, create_notification
from .models import ForumPost, Answer, Category


# Create your views here.
def forum_overview(request):
    all_categories = Category.objects.values_list('title', flat=True)

    forum_posts = ForumPost.objects.all()
    if request.method == 'POST':

        category = request.POST.get('category')
        if category != "Alle":
            forum_posts = forum_posts.filter(category__title=category)

        already_ordered = False
        ordered_by = request.POST.get('order_by')
        search_keyword = request.POST.get('search_keyword')
        order_map = {
            "Titel": "title",
            "Ersteller": "creator__username",
        }
        order_by = order_map.get(ordered_by, "name")

        if ordered_by == "von mir erstellte Posts":
            forum_posts = forum_posts.filter(creator=request.user)
            already_ordered = True
        if ordered_by == "von mir beantwortete Posts":
            forum_posts = ForumPost.objects.filter(answers__creator=request.user).distinct()
            already_ordered = True
        if ordered_by == "Erstellt am":
            if search_keyword:
                forum_posts = forum_posts.filter(**{f"date_time__icontains": search_keyword})
            else:
                forum_posts = forum_posts
            forum_posts = forum_posts.order_by("-date_time")
            already_ordered = True
        if not already_ordered:
            if search_keyword:
                forum_posts = forum_posts.filter(**{f"{order_by}__icontains": search_keyword})
            else:
                forum_posts = forum_posts
            forum_posts = forum_posts.order_by(order_by)

    else:
        forum_posts = forum_posts.order_by('title')
        ordered_by = "Titel"
        search_keyword = None
        category = "Alle"

    return render(request, './forum_overview.html',
                  {'forum_posts': forum_posts, 'ordered_by': ordered_by, 'search_keyword': search_keyword, 'category': category, 'all_categories': all_categories})


@login_required
def add_forum_post(request):
    all_categories = Category.objects.values_list('title', flat=True)

    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add_forum_post')

        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category')

        try:
            category = Category.objects.get(title=category)
        except Category.DoesNotExist:
            messages.error(request, all_messages["internal_error"])
            return redirect('add_artikel')

        if len(title) > 100:
            messages.error(request, all_messages["too_long_input"])
            return redirect('add_forum_post')

        if not title or not content:
            messages.error(request, all_messages['fill_all_required_fields'])
            return redirect('add_forum_post')

        clean_html(content)

        post = ForumPost.objects.create(title=title, content=content, creator=request.user, category=category)

        return redirect('post_detail', post.id)
    return render(request, './add_forum_post.html', {'categories': all_categories})


def post_detail(request, post_id):
    try:
        post = ForumPost.objects.get(id=post_id)
    except ForumPost.DoesNotExist:
        messages.error(request, all_messages['post_not_found'])
        return redirect('forum_overview')

    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('post_detail', post_id=post_id)

        content = request.POST.get('content')
        if not content:
            messages.error(request, all_messages['fill_all_required_fields'])
            return redirect('post_detail', post_id=post_id)

        clean_html(content)

        Answer.objects.create(content=content, creator=request.user, forum_post=post)
        create_notification(request, "Deine Forumsfrage wurde beantwortet", post.creator,
                            url=reverse('post_detail', args=[post_id]))
        return redirect('post_detail', post_id=post_id)
    return render(request, './forum_detail.html', {'post': post, 'answers': post.answers.all()})
