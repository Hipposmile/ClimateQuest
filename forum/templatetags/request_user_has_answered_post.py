from django import template

register = template.Library()


@register.filter
def request_user_has_answered_post(post, user):
    """Whether ``user`` answered ``post``; uses prefetched answers when available."""
    if not user.is_authenticated:
        return False
    return any(answer.creator_id == user.id for answer in post.answers.all())
