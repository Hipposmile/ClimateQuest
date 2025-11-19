from django.shortcuts import render
from django.shortcuts import render, redirect

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count


from django.utils import timezone
from datetime import timedelta

from core.all_messages import all_messages
from .models import *
from utils.functions import *

# Create your views here.
def artikel_overview(request):
    all_artikel = Artikel.objects.all()
    artikel = all_artikel.order_by('name')
    search_keyword = None
    if request.method == 'POST':
        already_ordered = False
        ordered_by = request.POST.get('order_by')
        search_keyword = request.POST.get('search_keyword')
        order_map = {
            "Name": "name",
            "Ersteller": "creator__username",
        }
        order_by = order_map.get(ordered_by, "name")
        if ordered_by == "von mir erstellte Artikel":
            artikel = artikel.filter(creator=request.user)
            already_ordered = True
        if ordered_by == "Zuletzt bearbeitet":
            if search_keyword:
                artikel = artikel.filter(**{f"date_time__icontains": search_keyword})
            else:
                artikel = artikel
            artikel = artikel.order_by("-date_time")
            already_ordered = True
        if not already_ordered:
            if search_keyword:
                artikel = artikel.filter(**{f"{order_by}__icontains": search_keyword})
            else:
                artikel = artikel
            artikel = artikel.order_by(order_by)
    else:
        ordered_by = "Name"
        artikel = all_artikel.order_by('name')

    return render(request, 'artikel_overview.html', {'artikel': artikel, 'ordered_by': ordered_by, 'search_keyword': search_keyword})

@login_required
def add_artikel(request):
    if request.method == 'POST':
        is_truth = request.POST.get('is_truth') == 'on'
        if not is_truth:
            messages.error(request, all_messages["not_is_truth"])
            return redirect('add_action')

        name = request.POST.get('name')
        content = request.POST.get('content')

        if not name or not content:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect('add_artikel')

        content = clean_html(content)

        Artikel.objects.create(
            name=name,
            content=content,
            creator=request.user
        )

        messages.success(request, all_messages["successfully_created_artikel"])

        return redirect('artikel_overview')

    return render(request, 'add_artikel.html')

@login_required
def edit_artikel(request, artikel_id):
    try:
        artikel = Artikel.objects.get(id=artikel_id)
    except Artikel.DoesNotExist:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect('artikel_overview')

    if artikel.creator != request.user:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect('artikel_detail', artikel.id)

    if request.method == 'POST':
        if 'edit_artikel' in request.POST:
            is_truth = request.POST.get('is_truth') == 'on'
            if not is_truth:
                messages.error(request, all_messages["not_is_truth"])
                return redirect('add_action')

            name = request.POST.get('name')
            content = request.POST.get('content')

            if not name or not content:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect('edit_artikel', artikel_id=artikel_id)

            content = clean_html(content)

            artikel.name = name
            artikel.content = content
            artikel.save()

            messages.success(request, all_messages["successfully_edited_artikel"])
            return redirect('artikel_detail', artikel_id=artikel.id)
        elif 'delete_artikel' in request.POST:
            artikel.delete()
            messages.success(request, all_messages["successfully_deleted_artikel"])
            return redirect('artikel_overview')
        else:
            messages.error(request, all_messages["internal_error"])
            return redirect('artikel_overview')

    return render(request, 'edit_artikel.html', {'artikel': artikel})

def artikel_detail(request, artikel_id):
    try:
        artikel = Artikel.objects.get(id=artikel_id)
    except Artikel.DoesNotExist:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect('artikel_overview')

    if request.method == 'POST':
        if 'add_comment' in request.POST:
            comment_text = request.POST.get('comment')
            comment = Comment.objects.create(comment=comment_text, user=request.user)
            artikel.comments.add(comment)

            messages.success(request, all_messages["successfully_asked_comment"])
            return redirect('artikel_detail', artikel_id)

        elif 'answer_comment' in request.POST:
            comment_id = request.POST.get('comment_id')
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                messages.error(request, all_messages["internal_error"])
                return redirect('artikels_overview')

            answer_text = request.POST.get('answer')

            answer = Answer.objects.create(answer=answer_text, user=request.user)
            comment.answers.add(answer)

            messages.success(request, all_messages["successfully_answered_comment"])
            return redirect('artikel_detail', artikel_id)

    has_liked = False
    if request.user.is_authenticated:
        if request.user in artikel.like.all():
            has_liked = True

    return render(request, 'artikel_detail.html', {'artikel': artikel, 'has_liked': has_liked})

@login_required
def add_like(request, artikel_id):
    try:
        artikel = Artikel.objects.get(id=artikel_id)
        if request.user in artikel.like.all():
            artikel.like.remove(request.user)
            messages.success(request, all_messages["successfully_removed_like"])
        else:
            artikel.like.add(request.user)
            messages.success(request, all_messages["successfully_added_like"])
        artikel.save()
        return redirect('artikel_detail', artikel_id)
    except Artikel.DoesNotExist:
        messages.error(request, all_messages["artikel_not_existing"])
        return redirect('artikel_overview')