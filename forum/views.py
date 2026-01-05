from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from core.all_messages import all_messages
from utils.functions import *
from .models import *


# Create your views here.
def forum_overview(request):
    forum_posts = ForumPost.objects.all()
    if request.method == 'POST':
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
    return render(request, './forum_overview.html', {'forum_posts': forum_posts, 'ordered_by': ordered_by, 'search_keyword': search_keyword})

@login_required
def add_forum_post(request):
    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add_forum_post')

        title = request.POST.get('title')
        content = request.POST.get('content')

        if len(title) > 100:
            messages.error(request, all_messages["input_too_long"])
            return redirect('add_forum_post')

        if not title or not content:
            messages.error(request, all_messages['fill_all_required_fields'])
            return redirect('add_forum_post')

        clean_html(content)

        ForumPost.objects.create(title=title, content=content, creator=request.user)
        return redirect('forum_overview')
    return render(request, './add_forum_post.html')

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
            return redirect('add_forum_post')

        content = request.POST.get('content')
        if not content:
            messages.error(request, all_messages['fill_all_required_fields'])
            return redirect('post_detail', post_id=post_id)

        clean_html(content)

        Answer.objects.create(content=content, creator=request.user, forum_post=post)
        create_notification(request, "Deine Forumsfrage wurde beantwortet", post.creator)
        return redirect('post_detail', post_id=post_id)
    return render(request, './forum_detail.html', {'post': post, 'answers': post.answers.all()})