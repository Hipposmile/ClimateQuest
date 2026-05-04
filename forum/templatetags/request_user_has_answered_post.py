from django import template

register = template.Library()


@register.filter
def request_user_has_answered_post(post, user):
    return post.answers.filter(creator=user).exists()
