"""Notifications and flash messages after an action was created, edited or deleted."""

from django.contrib import messages
from django.urls import reverse

from utils.functions import create_notification

PARTY = '<span class="emoji">&#x1F973;</span>'
SAD = '<span class="emoji">&#x1F622;</span>'

# (german, english) templates per verb. ``{name}`` is the action type, ``{level}`` the new level.
LEVEL_UP = {
    "created": (
        "Du hast eine neue Aktion vom Typen {name} erstellt und bist so ins Level {level} aufgestiegen. " + PARTY,
        "You created an action (type: {name}) and so reached the level {level}. " + PARTY,
    ),
    "edited": (
        "Du hast eine Aktion vom Typen {name} bearbeitet und bist so ins Level {level} aufgestiegen. " + PARTY,
        "You edited an action (type: {name}) and so reached the level {level}. " + PARTY,
    ),
}
LEVEL_DOWN = {
    "edited": (
        "Du hast eine Aktion vom Typen {name} bearbeitet, dadurch Klimapunkte verloren und bist so ins Level "
        "{level} abgestiegen. " + SAD,
        "You edited an action (type: {name}), lost climate points and so descended to level {level}. " + SAD,
    ),
    "deleted": (
        "Du hast eine Aktion vom Typen {name} gelöscht, dadurch Klimapunkte verloren und bist so ins Level "
        "{level} abgestiegen. " + SAD,
        "You deleted an action (type: {name}), lost climate points and so descended to level {level}. " + SAD,
    ),
}
STREAK_UP = {
    "created": (
        "Du hast eine neue Aktion vom Typen {name} erstellt und so deine Streak verlängert. " + PARTY,
        "You created a new action (type: {name}) and so extended your streak. " + PARTY,
    ),
    "edited": (
        "Du hast eine Aktion vom Typen {name} bearbeitet und so deine Streak verlängert. " + PARTY,
        "You edited an action (type: {name}) and so extended your streak. " + PARTY,
    ),
}
STREAK_DOWN = {
    "edited": (
        "Du hast eine Aktion vom Typen {name} bearbeitet und so deine Streak verkürzt. " + SAD,
        "You edited an action (type: {name}) and so shortened your streak. " + SAD,
    ),
    "deleted": (
        "Du hast eine Aktion vom Typen {name} gelöscht und so deine Streak verkürzt. " + SAD,
        "You deleted an action (type: {name}) and so shortened your streak. " + SAD,
    ),
}


def _announce(request, templates, level_url, flash, **values):
    text_de = templates[0].format(name=values["name_de"], level=values.get("level_de", ""))
    text_en = templates[1].format(name=values["name_en"], level=values.get("level_en", ""))
    create_notification(request, text_de, text_en, request.user, url=level_url)
    flash(request, text_de if request.LANGUAGE_CODE == "de" else text_en)


def report_action_change(request, verb, action_type, old, new):
    """Notify the user about level and streak changes caused by creating/editing/deleting an action.

    ``old`` and ``new`` are ``(level_info, streak)`` tuples taken before and after the change.
    """
    (old_level, old_streak), (new_level, new_streak) = old, new
    names = {"name_de": action_type.name, "name_en": action_type.name_en}
    current = new_level["current_level"]

    if current is not None:
        levels = {"level_de": current.description, "level_en": current.description_en}
        if old_level["level_number"] < new_level["level_number"] and verb in LEVEL_UP:
            _announce(request, LEVEL_UP[verb], reverse("level_me"), messages.success, **names, **levels)
            if verb == "created":
                messages.info(request, "request-review")
        elif old_level["level_number"] > new_level["level_number"] and verb in LEVEL_DOWN:
            _announce(request, LEVEL_DOWN[verb], reverse("level_me"), messages.error, **names, **levels)

    if old_streak < new_streak and verb in STREAK_UP:
        _announce(request, STREAK_UP[verb], reverse("dashboard"), messages.success, **names)
    elif old_streak > new_streak and verb in STREAK_DOWN:
        _announce(request, STREAK_DOWN[verb], reverse("dashboard"), messages.error, **names)
