"""Parsing of the "time period" form shared by the user, family and community statistics pages."""

from dataclasses import dataclass
from datetime import date, datetime

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.all_messages import all_messages
from utils.functions import get_date_range

PERIOD_TOTAL = "Gesamt"
PERIOD_CUSTOM = "Benutzerdefiniert"
# Posted form values (German, kept for compatibility with the templates) -> translated labels.
PERIOD_LABELS = {
    PERIOD_TOTAL: gettext_lazy("Gesamt"),
    "Heute": gettext_lazy("Heute"),
    "Sieben Tage": gettext_lazy("Sieben Tage"),
    "Dreißig Tage": gettext_lazy("Dreißig Tage"),
    "Dreihundertfünfundsechzig Tage": gettext_lazy("Dreihundertfünfundsechzig Tage"),
}
FORM_DATE_FORMAT = "%Y-%m-%d"


class InvalidPeriod(Exception):
    """The submitted period is invalid; ``message`` is the user-facing explanation."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Period:
    text: str
    start: date | None = None
    end: date | None = None
    is_total: bool = True


def format_date(day, language_code):
    return day.strftime("%d.%m.%Y" if language_code == "de" else "%m/%d/%Y")


def parse_period(post, language_code, today):
    """Period selected in a POST form (``zeitraum``, ``start_date``, ``end_date``)."""
    zeitraum = post.get("zeitraum", PERIOD_TOTAL)
    if zeitraum == PERIOD_CUSTOM:
        return _parse_custom_period(post, language_code, today)
    if zeitraum not in PERIOD_LABELS:
        raise InvalidPeriod(all_messages["invalid_time_period"])
    start, end = get_date_range(zeitraum, today)
    return Period(text=str(PERIOD_LABELS[zeitraum]), start=start, end=end, is_total=zeitraum == PERIOD_TOTAL)


def _parse_custom_period(post, language_code, today):
    raw_start = post.get("start_date")
    raw_end = post.get("end_date")
    if not raw_start or not raw_end:
        raise InvalidPeriod(all_messages["missing_required_inputs"])
    try:
        start = datetime.strptime(raw_start, FORM_DATE_FORMAT).date()
        end = datetime.strptime(raw_end, FORM_DATE_FORMAT).date()
    except ValueError:
        raise InvalidPeriod(all_messages["invalid_date"]) from None
    if start > end:
        raise InvalidPeriod(all_messages["invalid_date_range"])
    if end > today:
        raise InvalidPeriod(all_messages["date_in_future"])
    text = _("%(start)s bis %(end)s") % {
        "start": format_date(start, language_code),
        "end": format_date(end, language_code),
    }
    return Period(text=text, start=start, end=end, is_total=False)


def default_period():
    return Period(text=str(PERIOD_LABELS[PERIOD_TOTAL]))
