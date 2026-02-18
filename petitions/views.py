from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from core.all_messages import all_messages
from petitions.models import *
from utils.functions import clean_html, clean_img, check_is_truth
from django.db.models import Count

# Create your views here.
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif"]
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/avif", ]
MAX_SIZE_MB = 5


@login_required
def add_petition(request):
    categories = Category.objects.all().order_by('title')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        goal = request.POST.get('goal')
        img = request.FILES.get('img')
        category_input = request.POST.get('category')

        is_truth = check_is_truth(request)
        if not is_truth:
            return redirect("add_petition")

        if not title or not content or not goal:
            messages.error(request, all_messages["missing_required_inputs"])
            return redirect("add_petition")

        try:
            goal = int(goal)
        except ValueError:
            messages.error(request, all_messages["goal_not_a_number"])
            return redirect("add_petition")
        if goal < 10:
            messages.error(request, all_messages["goal_too_small"])
            return redirect("add_petition")

        try:
            category = Category.objects.get(title=category_input)
        except Category.DoesNotExist:
            messages.error(request, all_messages["internal_error"])
            return redirect("add_petition")

        content = clean_html(content)

        if img:
            valid, response = clean_img(img)
            if not valid:
                messages.error(request, response)
                return redirect("add_petition")
            img = response
            width, height = Image.open(img).size
            print(width, height)
            if width / height != 16 / 9:
                messages.error(request, all_messages["invalid_img_proportions"])
                return redirect("add_petition")

        petition = Petition.objects.create(title=title,
                                           content=content,
                                           goal=goal,
                                           img=img if img else None,
                                           category=category,
                                           creator=request.user)
        messages.success(request, all_messages["petition_added"])
        return redirect("petition_detail", petition.id)

    return render(request, "./add_petition.html", {'categories': categories})


def petition_detail(request, petition_id):
    try:
        petition = Petition.objects.get(id=petition_id)
    except Petition.DoesNotExist:
        messages.error(request, all_messages["petition_not_found"])
        return redirect("petitions_overview")

    if request.method == 'POST':
        if request.user.is_authenticated:
            if 'sign' in request.POST:
                if request.user not in petition.signs.all():
                    petition.signs.add(request.user)
                    petition.save()
                    messages.success(request, all_messages["petition_signed"])
                else:
                    petition.signs.remove(request.user)
                    petition.save()
                    messages.success(request, all_messages["petition_unsigned"])
            elif 'add_comment' in request.POST:
                comment_text = request.POST.get('comment')
                comment = Comment.objects.create(comment=comment_text, user=request.user)
                petition.comments.add(comment)

                messages.success(request, all_messages["successfully_asked_comment"])
                return redirect('petition_detail', petition_id)

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
                return redirect('petition_detail', petition_id)

    return render(request, "./petition_detail.html", {"petition": petition})


@login_required
def edit_petition(request, petition_id):
    try:
        petition = Petition.objects.get(id=petition_id)
    except Petition.DoesNotExist:
        messages.error(request, all_messages["petition_not_found"])
        return redirect("petitions_overview")

    if request.user != petition.creator:
        messages.error(request, all_messages["not_authorized_to_visit"])
        return redirect("add_petition")

    if request.method == 'POST':
        if 'update' in request.POST:
            title = request.POST.get('title')
            content = request.POST.get('content')

            content = clean_html(content)

            is_truth = check_is_truth(request)
            if not is_truth:
                return redirect("edit_petition", petition_id)

            if not title or not content:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect("edit_petition", petition_id)

            update = Update.objects.create(title=title, content=content)
            petition.updates.add(update)
            return redirect("petition_detail", petition_id)

        elif 'change_goal' in request.POST:
            goal = request.POST.get('goal')
            if not goal:
                messages.error(request, all_messages["missing_required_inputs"])
                return redirect("petition_detail", petition_id)
            try:
                goal = int(goal)
            except ValueError:
                messages.error(request, all_messages["goal_not_a_number"])
                return redirect("add_petition")
            if goal < 10:
                messages.error(request, all_messages["goal_too_small"])
                return redirect("add_petition")

            petition.goal = goal
            petition.save()
            messages.success(request, all_messages["successfully_updated_goal"])
            return redirect("petition_detail", petition_id)

        elif 'success' in request.POST:
            if petition.success:
                petition.success = False
                messages.error(request, all_messages["removed_success"])
            else:
                petition.success = True
                messages.success(request, all_messages["added_success"])
            petition.save()
            return redirect("petition_detail", petition_id)

    return render(request, "./edit_petition.html", {'petition': petition})


def petitions_overview(request):  # ToDo: Add category filter
    search_keyword = None
    if request.method == 'POST':
        success_visible = request.POST.get('success_visible') == 'on'
        if success_visible:
            all_petitions = Petition.objects.all()
        else:
            all_petitions = Petition.objects.filter(success=False)
        already_ordered = False
        ordered_by = request.POST.get('order_by')
        search_keyword = request.POST.get('search_keyword')
        order_map = {
            "Titel": "title",
            "Ersteller": "creator__username",
        }
        order_by = order_map.get(ordered_by, "title")
        if ordered_by == "von mir erstellte Petitionen":
            petitions = all_petitions.filter(creator=request.user)
            already_ordered = True
        if ordered_by == "von mir unterschriebene Petitionen":
            petitions = request.user.petition_sign.all()
            already_ordered = True
        if ordered_by == "Zuletzt bearbeitet":
            if search_keyword:
                petitions = all_petitions.filter(**{f"updated_at__icontains": search_keyword})
            else:
                petitions = all_petitions
            petitions = petitions.order_by("-updated_at")
            already_ordered = True
        if ordered_by == "Unterschriften":
            if search_keyword:
                try:
                    search_keyword = int(search_keyword)
                except ValueError:
                    messages.error(request, all_messages["signs_search_keyword_not_a_number"])
                    return redirect('petitions_overview')

            petitions = all_petitions.annotate(num_signs=Count('signs'))
            if search_keyword:
                petitions = petitions.filter(num_signs__icontains=search_keyword)
            petitions = petitions.order_by('-num_signs')
            already_ordered = True
        if not already_ordered:
            if search_keyword:
                petitions = all_petitions.filter(**{f"{order_by}__icontains": search_keyword})
            else:
                petitions = all_petitions
            petitions = petitions.order_by(order_by)
    else:
        success_visible = False
        ordered_by = "Titel"
        petitions = Petition.objects.filter(success=False).order_by('title')

    return render(request, './petitions_overview.html',
                  {'petitions': petitions, 'ordered_by': ordered_by, 'search_keyword': search_keyword,
                   'success_visible': success_visible})
