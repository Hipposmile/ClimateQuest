"""Validation and period rules for creating and editing actions (``Aktion``)."""

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.db.models.functions import Lower
from django.utils import timezone

from core.all_messages import all_messages
from utils.functions import QUANTITY_DECIMAL_PLACES, parse_id

from .models import Aktion, AktionenListe

MAX_DESCRIPTION_LENGTH = 200
MAX_PAST_MONTHS = 1
FORM_DATE_FORMAT = "%Y-%m-%d"
# Actions whose unit is a time span block that time span (e.g. "1 Woche" vegetarian diet): unit -> days.
DAYS_PER_TIMELY_UNIT = {"tag": 1, "woche": 7, "monat": 30}


class ActionInputError(Exception):
    """Invalid user input; ``message`` is the user-facing explanation."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass
class ValidatedAction:
    action_type: AktionenListe
    description: str
    quantity: float
    date: date


def is_timely_unit(unit):
    return unit.lower() in DAYS_PER_TIMELY_UNIT


def get_period_start(end, quantity, unit):
    """First day (exclusive) of the period an action of ``quantity`` ``unit`` ending on ``end`` covers."""
    days_per_unit = DAYS_PER_TIMELY_UNIT.get(unit.lower())
    if days_per_unit is None:
        return None
    try:
        return end - timedelta(days=days_per_unit * quantity)
    except OverflowError:
        return date.min


def validate_number(number, decimals=QUANTITY_DECIMAL_PLACES):
    """Parse a quantity typed by a user (decimal comma allowed). Returns None if it is not a finite number."""
    try:
        value = float(number.replace(",", "."))
    except (ValueError, AttributeError):
        return None
    return round(value, decimals) if math.isfinite(value) else None


def _conflicting_actions(action_type, user, exclude_id):
    actions = Aktion.objects.filter(user=user, aktion__in=[action_type, *action_type.forbidden_in_same_period.all()])
    return actions.exclude(id=exclude_id) if exclude_id else actions


def action_exists_in_period(action_type, end_date, quantity, user, exclude_id=None):
    start = get_period_start(end_date, quantity, action_type.mengeBeschreibungSingular)
    if start is None:
        return False
    return (
        _conflicting_actions(action_type, user, exclude_id)
        .filter(date__range=(start + timedelta(days=1), end_date))
        .exists()
    )


def action_is_in_different_action_period(action_type, end_date, user, exclude_id=None):
    """Whether ``end_date`` lies inside the period of an existing, later-dated action."""
    later_actions = (
        _conflicting_actions(action_type, user, exclude_id)
        .filter(date__gte=end_date)
        .values("date", "quantity", unit=Lower("aktion__mengeBeschreibungSingular"))
    )
    for existing in later_actions:
        start = get_period_start(existing["date"], existing["quantity"], existing["unit"])
        if start is not None and end_date > start + timedelta(days=1):
            return True
    return False


def action_date_invalid(action_type, end_date, quantity, user, exclude_id=None):
    return action_exists_in_period(
        action_type, end_date, quantity, user, exclude_id
    ) or action_is_in_different_action_period(action_type, end_date, user, exclude_id)


def validate_action_input(user, post, action_date=None, exclude_id=None):
    """Validate the add/edit action form.

    ``action_date`` is fixed when an existing action is edited, otherwise it is read from the form.
    Raises ``ActionInputError`` with a user-facing message.
    """
    if post.get("is_truth") != "on":
        raise ActionInputError(all_messages["not_is_truth"])

    action_type_id = post.get("action_type_id")
    if not action_type_id:
        raise ActionInputError(all_messages["action_name_missing"])
    action_type = AktionenListe.objects.filter(id=parse_id(action_type_id)).first()
    if action_type is None:
        raise ActionInputError(all_messages["action_not_found"])

    description = post.get("action_description") or ""
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ActionInputError(all_messages["too_long_input"])

    if action_date is None:
        action_date = _parse_form_date(post.get("action_date"))

    raw_quantity = post.get("action_quantity")
    if not raw_quantity:
        raise ActionInputError(all_messages["missing_required_inputs"])
    quantity = validate_number(raw_quantity)
    if quantity is None or quantity <= 0:
        raise ActionInputError(all_messages["invalid_quantity"])

    unit = action_type.mengeBeschreibungSingular
    if not is_timely_unit(unit):
        already_done = (
            Aktion.objects.filter(user=user, aktion=action_type, date=action_date)
            .exclude(id=exclude_id)
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        if already_done + quantity > action_type.max:
            raise ActionInputError(all_messages["max_action_quantity"])

    today = timezone.localdate()
    if action_date > today:
        raise ActionInputError(all_messages["date_in_future"])
    earliest_allowed = today - relativedelta(months=MAX_PAST_MONTHS)
    covered_since = get_period_start(action_date, quantity, unit) or action_date
    if covered_since < earliest_allowed:
        raise ActionInputError(all_messages["action_too_past"])

    if action_date_invalid(action_type, action_date, quantity, user, exclude_id):
        raise ActionInputError(all_messages["action_already_set_in_period"])

    return ValidatedAction(action_type=action_type, description=description, quantity=quantity, date=action_date)


def _parse_form_date(raw):
    if not raw:
        raise ActionInputError(all_messages["missing_required_inputs"])
    try:
        return datetime.strptime(raw, FORM_DATE_FORMAT).date()
    except ValueError:
        raise ActionInputError(all_messages["invalid_date"]) from None
