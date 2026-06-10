import logging
import random
import string
import time
import traceback
from datetime import timedelta, date

import bleach
import httpx
import jwt
from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db.models import Sum, F
from django.db.models.functions import TruncWeek
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from webpush import send_user_notification

from ClimateQuest import settingsprod
from aktionen.models import Aktion, Category
from artikel.models import Artikel
from community.models import Community
from core.all_messages import all_messages
from family.models import Family
from hall_of_fame.models import HallOfFameEntry
from home.models import Benachrichtigung
from personals.models import UserErweitert, Level, IOSDevice

dezimalstellen = 4

logger = logging.getLogger("django")


def generate_random_password():
    return ''.join(
        random.choices(string.ascii_letters + string.digits + string.punctuation.replace('"', '').replace("'", ""),
                       k=12))  # Removes " so string can´t be interrupted


def send_mail_function(**kwargs):
    request = kwargs.get('request')
    fehlermeldung = kwargs.get('fehlermeldung', 'Fehler beim E-Mail-Versand')
    subject = kwargs.get('subject')
    message = kwargs.get('message')
    fail_silently = kwargs.get('fail_silently', False)
    mailinglist_needless = kwargs.get('mailinglist_needless', False)
    url = kwargs.get('url', '/dashboard/')

    if request is None or subject is None or message is None or fail_silently is None:
        create_internal_error(request, 'Beim E-Mail Versand wurden nicht alle notwendigen Elemente übergeben',
                              fehlermeldung)

    user = kwargs.get('user')
    if not user:
        try:
            user = request.user
        except Exception:
            create_internal_error(request, 'Bei send_mail_function wurde kein User übergeben', fehlermeldung)

    recipient_list = kwargs.get('recipient_list')
    if not recipient_list:
        recipient_list = user.email

    if not mailinglist_needless and user.email != '':
        try:
            user_erweitert = UserErweitert.objects.get(user=user)
        except UserErweitert.DoesNotExist:
            create_internal_error(request, f'UserErweitert zu User {user} nicht gefunden', fehlermeldung)
        if not user_erweitert.mail_verified:
            return True
        if user_erweitert.mailinglist:
            try:
                html_content = f"""
                    <!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <title>{subject}</title>
    <style nonce="{{ request.csp_style_nonce }}">
      body {{
        margin: 0; padding: 0;
        background: #f5f7fa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1f2937;
        line-height: 1.5;
      }}
      .container {{
        max-width: 600px;
        margin: 24px auto;
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        overflow: hidden;
      }}
      .header {{
        padding: 20px 24px;
        border-bottom: 1px solid #e5e7eb;
      }}
      .header h1 {{
        font-size: 20px;
        margin: 0;
        color: #14532d; /* kräftiges Grün */
      }}
      .content {{
        padding: 24px;
        font-size: 16px;
      }}
      .footer {{
        padding: 16px 24px;
        border-top: 1px solid #e5e7eb;
        font-size: 12px;
        color: #6b7280;
        background: #f9fafb;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>{subject}</h1>
      </div>
      <div class="content">
        {message} <a href="{url}">Mehr</a>
      </div>
      <div class="footer">
        <p>Du erhältst diese E-Mail, weil du <i>Benachrichtigungen auch per E-Mail erhalten</i> aktiviert hast <a href="https://climate-quest.de/personals/settings/#mailinglist_checkbox">Hier abmelden</a>.</p>
        <p><a href="https://climate-quest.de/impressum/">Impressum</a> • <a href="https://climate-quest.de/datenschutz/">Datenschutz</a></p>
      </div>
    </div>
  </body>
</html>
                """
                text_content = message
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settingsprod.EMAIL_HOST_USER,
                    to=[recipient_list]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                return True
            except Exception as e:
                create_internal_error(request, f'Fehler beim E-Mail-Versand an {recipient_list}: {e}', fehlermeldung)

    elif mailinglist_needless:
        try:
            html_content = f"""
                                <!doctype html>
            <html lang="de">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width">
                <title>{subject}</title>
                <style nonce="{{ request.csp_style_nonce }}">
                  body {{
                    margin: 0; padding: 0;
                    background: #f5f7fa;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #1f2937;
                    line-height: 1.5;
                  }}
                  .container {{
                    max-width: 600px;
                    margin: 24px auto;
                    background: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                    overflow: hidden;
                  }}
                  .header {{
                    padding: 20px 24px;
                    border-bottom: 1px solid #e5e7eb;
                  }}
                  .header h1 {{
                    font-size: 20px;
                    margin: 0;
                    color: #14532d; /* kräftiges Grün */
                  }}
                  .content {{
                    padding: 24px;
                    font-size: 16px;
                  }}
                  .footer {{
                    padding: 16px 24px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #6b7280;
                    background: #f9fafb;
                  }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1>{subject}</h1>
                  </div>
                  <div class="content">
                    {message} <a href="{url}">Mehr</a>
                  </div>
                  <div class="footer">
                    <p><a href="https://climate-quest.de/impressum/">Impressum</a> • <a href="https://climate-quest.de/datenschutz/">Datenschutz</a></p>
                  </div>
                </div>
              </body>
            </html>
                            """
            text_content = message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settingsprod.EMAIL_HOST_USER,
                to=[recipient_list]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            return True
        except Exception as e:
            create_internal_error(request, f'Fehler beim E-Mail-Versand an {recipient_list}: {e}', fehlermeldung)
            return False

    elif user.email == '':
        return True
    else:
        return True

    return False


def get_level(user):
    aktionen = Aktion.objects.filter(user=user)
    klimapunkte = get_klimapunkte(aktionen)
    klimapunkte += get_additional_klimapunkte(user)

    levels = Level.objects.order_by('klimapunkte')

    current_level = None
    next_level = None
    level_number = 1
    progress_percent = 100

    for i, level in enumerate(levels):
        if klimapunkte >= level.klimapunkte:
            current_level = level
            if i + 1 < len(levels):
                next_level = levels[i + 1]
                differenz = next_level.klimapunkte - current_level.klimapunkte
                fortschritt = klimapunkte - current_level.klimapunkte
                progress_percent = int((fortschritt / differenz) * 100) if differenz > 0 else 100
                level_number = i + 1
            else:
                level_number = i + 1
                return {
                    'info': _(
                        'Du hast das höchste Level bereits erreicht: %(level)s <span class="emoji">&#x1F973;</span>') % {
                                'level': current_level.description},
                    'current_level': current_level, 'levels': levels, 'klimapunkte': klimapunkte,
                    'level_number': level_number}

    klimapunkte_missing = next_level.klimapunkte - klimapunkte

    return {'current_level': current_level, 'next_level': next_level, 'progress_percent': progress_percent,
            'levels': levels, 'klimapunkte_missing': klimapunkte_missing, 'level_number': level_number}


def get_weekly_goal_from_user(user):
    weekly_goal = user.usererweitert.weekly_goal
    weekly_klimapunkte = (
            Aktion.objects
            .filter(user=user, date__gte=(date.today() - timedelta(days=date.today().weekday())))
            .annotate(impact=(F("aktion__klimapunkte") * F("quantity")))
            .aggregate(total=Sum('impact'))['total'] or 0
    )
    weekly_goal_progress_percent = round((weekly_klimapunkte / weekly_goal) * 100)
    return weekly_goal, weekly_klimapunkte, weekly_goal_progress_percent


def get_all_klimapunkte_from_user(user):
    aktionen = Aktion.objects.filter(user=user)
    klimapunkte = get_klimapunkte(aktionen)
    klimapunkte += get_additional_klimapunkte(user)
    return klimapunkte


def get_klimapunkte(aktionen):
    klimapunkte = sum(aktion.impact for aktion in aktionen)
    return klimapunkte


def create_internal_error(request, beschreibung, fehlermeldung="interner Fehler", exception=None, throw_exception=True):
    def sanitize_post_data(post_data):
        return {
            k: ('***' if 'password' in k.lower() or 'token' in k.lower() else v)
            for k, v in post_data.items()
        }

    def sanitize_cookies(cookies):
        return {k: '***' for k in cookies}

    def extract_files(files):
        return {k: f.name for k, f in files.items()}

    def extract_meta(meta):
        # Nur HTTP-Header, keine IP-Adresse oder andere sensible Felder
        return {k: v for k, v in meta.items() if k.startswith('HTTP_')}

    error_message = {
        'timestamp': timezone.now().isoformat(),
        'method': request.method,
        'path': request.path,
        'full_path': request.get_full_path(),
        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
        'GET': request.GET.dict(),
        'POST': sanitize_post_data(request.POST.dict()),
        'COOKIES': sanitize_cookies(request.COOKIES),
        'FILES': extract_files(request.FILES),
        'META': extract_meta(request.META),
        'beschreibung': beschreibung
    }

    if exception:
        error_message['exception'] = str(exception)
        error_message['traceback'] = traceback.format_exc()

    if throw_exception:
        messages.error(request, fehlermeldung)

    logging.error(error_message)

    with open('logs/errors.log', 'a') as file:
        file.write(f'{error_message}\n\n')


def create_notification(request, notification_de, notification_en, user=None, url=None):
    if user is None:
        user = request.user
    if url is None:
        url = reverse('dashboard')

    head = "Neue Benachrichtigung" if user.usererweitert.lang == "de" else "New notification"

    benachrichtigung = Benachrichtigung.objects.create(benachrichtigung_de=notification_de,
                                                       benachrichtigung_en=notification_en, user=user,
                                                       url=url)
    send_mail_function(
        request=request,
        fehlermeldung='Beim Erstellen einer Benachrichtigung ist beim Versenden der E-Mail ein Fehler aufgetreten. Die Benachrichtigung kann nur in dem Benachrichtigungsteil hier auf der Webseite gefunden werden!' if user.usererweitert.lang == 'de' else 'An error occurred while sending the email during the creation of the notification. The notification can only be found in the notifications section here on the website!',
        subject='ClimateQuest - neue Benachrichtigung',
        message=notification_de if user.usererweitert.lang == 'de' else notification_en,
        recipient_list=user.email,
        user=user,
        url=url
    )

    mobile_notification_redirect_url = reverse('benachrichtigungen_view_focused', args=[benachrichtigung.id])
    mobile_msg_de = notification_de.split('<span>')[0]
    mobile_msg_en = notification_en.split('<span>')[0]

    tokens = IOSDevice.objects.filter(user=user).values_list("apns_token", flat=True)
    for t in tokens:
        try:
            send_ios_push(device_token=t, title=head,
                          body=mobile_msg_de if user.usererweitert.lang == 'de' else mobile_msg_en,
                          data={"url": mobile_notification_redirect_url})
        except Exception as e:
            logging.error(e)

    res = send_push(benachrichtigung=mobile_msg_de if user.usererweitert.lang == "de" else mobile_msg_en,
                    user=user, url=mobile_notification_redirect_url, head=head)
    if res == 500:
        create_internal_error(request, "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.",
                              "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.")


def send_ios_push(device_token: str, title: str, body: str, data: dict = None):
    token = _make_jwt()

    payload = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
            "badge": 1,
        }
    }
    if data:
        payload.update(data)

    url = f"{settings.APNS_HOST}/3/device/{device_token}"

    with httpx.Client(http2=True) as client:
        response = client.post(
            url,
            headers={
                "authorization": f"bearer {token}",
                "apns-topic": settings.APPLE_BUNDLE_ID,
                "apns-push-type": "alert",
            },
            json=payload,
        )

    if response.status_code != 200:
        raise Exception(f"APNs Fehler {response.status_code}: {response.text}")


def _make_jwt():
    with open(settings.APN_KEY_PATH) as f:
        key = f.read()
    return jwt.encode(
        {"iss": settings.APPLE_TEAM_ID, "iat": int(time.time())},
        key,
        algorithm="ES256",
        headers={"kid": settings.APN_KEY_ID},
    )


def send_push(benachrichtigung, user, url='/benachrichtigungen/', head="Neue Benachrichtigung"):
    try:
        payload = {'head': head, 'body': benachrichtigung, 'url': url}
        send_user_notification(user=user, payload=payload, ttl=1000)

        return 200
    except TypeError:
        return 500


def ist_email_gueltig(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def check_worldwide_ranking_exists(request):
    try:
        Family.objects.get(name='worldwide ranking')
        return True
    except Family.DoesNotExist:
        create_internal_error(request, 'Family "worldwide ranking" existiert nicht')
        return False


def get_families_of_user(user):
    return Family.objects.filter(members=user).order_by('name')


def get_communities_of_user(user):
    # Hole die IDs der Familien des aktuellen Nutzers
    user_families = get_families_of_user(user)

    # Verwende diese IDs zum Filtern der Communities
    communities = Community.objects.filter(members__id__in=user_families).distinct().order_by('name')

    return communities


def get_communities_of_family(family):
    family_communities = Community.objects.filter(members=family).distinct().order_by('name')
    return family_communities


ALLOWED_TAGS = [
    'p', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a', 'br', 'h1', 'h2'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'target', 'rel']
}


def clean_html(html):
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    return bleach.linkify(cleaned, callbacks=[bleach.callbacks.nofollow])


def get_klimapunkte_from_likes(user):
    klimapunkte_per_like = 0.1
    artikel = Artikel.objects.filter(creator=user)
    klimapunkte = 0
    for single_artikel in artikel:
        likes = single_artikel.like_count()
        klimapunkte_artikel = likes * klimapunkte_per_like
        klimapunkte += klimapunkte_artikel
    return klimapunkte


def get_additional_klimapunkte(user):
    klimapunkte_from_likes = get_klimapunkte_from_likes(user)
    additional_klimapunkte = user.usererweitert.additional_klimapunkte
    return klimapunkte_from_likes + additional_klimapunkte


def get_streak_from_user(user):
    weekly_goal = user.usererweitert.weekly_goal

    weekly_data = (
        Aktion.objects
        .filter(user=user)
        .annotate(week=TruncWeek('date'))
        .values('week')
        .annotate(
            total_impact=Sum(F("aktion__klimapunkte") * F("quantity"))
        )
        .order_by('-week')
    )

    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())

    successful_weeks = 0
    expected_week = current_week_start

    # Falls diese Woche gar kein Eintrag existiert, expected_week direkt auf Vorwoche setzen
    if not weekly_data or weekly_data[0]["week"] != current_week_start:
        expected_week = current_week_start - timedelta(days=7)

    for entry in weekly_data:
        week_start = entry["week"]

        if week_start == current_week_start:
            if entry["total_impact"] >= weekly_goal:
                successful_weeks += 1
                expected_week -= timedelta(days=7)
            else:
                expected_week = current_week_start - timedelta(days=7)
            continue

        if week_start != expected_week:
            break

        if entry["total_impact"] >= weekly_goal:
            successful_weeks += 1
            expected_week -= timedelta(days=7)
        else:
            break

    return successful_weeks


def clean_img(img, ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "webp", "avif"],
              ALLOWED_MIME_TYPES=["image/jpeg", "image/png", "image/webp", "image/avif", ],
              ALLOWED_FORMATS=["JPEG", "PNG", "WEBP", "AVIF"], MAX_SIZE_MB=5):
    if img.size > MAX_SIZE_MB * 1024 * 1024:
        return False, all_messages["size_exceeded_maximum"].format(max_size_mb=MAX_SIZE_MB)

    ext = img.name.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, all_messages["invalid_file_extension"]

    try:
        image = Image.open(img)
        image.verify()
    except Exception:
        return False, all_messages["invalid_img"]

    if image.format not in ALLOWED_FORMATS:
        return False, all_messages["invalid_file_type"]

    if img.content_type not in ALLOWED_MIME_TYPES:
        return False, all_messages["invalid_mime_type"]

    img.seek(0)
    return True, img


def check_is_truth(request):
    is_truth = request.POST.get('is_truth') == 'on'
    if not is_truth:
        messages.error(request, all_messages["not_is_truth"])
        return False
    return True


def get_perfect_week_progress(user, date_given):
    week_start = date_given - timedelta(days=date_given.weekday())
    week_end = week_start + timedelta(days=6)

    output_de = {}
    output_en = {}
    for category in Category.objects.all():
        has_action = Aktion.objects.filter(user=user, aktion__category=category,
                                           date__range=(week_start, week_end)).exists()
        output_de[category.name] = has_action
        output_en[category.name_en] = has_action

    return output_de, output_en


def get_family_rank_from_user(user, family):
    members_with_klimapunkte = []
    members = family.members.all()

    for member in members:
        klimapunkte = get_all_klimapunkte_from_user(member)
        members_with_klimapunkte.append({'member': member, 'klimapunkte': klimapunkte})

    members_with_klimapunkte_sortiert = sorted(
        members_with_klimapunkte,
        key=lambda x: x['klimapunkte'],
        reverse=True
    )

    rank = next(i for i, d in enumerate(members_with_klimapunkte_sortiert) if d['member'] == user)
    return rank + 1


"""def get_family_rank_from_user(user, family):
    result = (
        family.members
        .annotate(
            total_klimapunkte=Sum(
                F("aktion__aktion__klimapunkte") * F("aktion__quantity")
            ),
            rank=Window(
                expression=Rank(),
                order_by=F("total_klimapunkte").desc(),
            ),
        )
        .filter(pk=user.pk)
        .values("rank")
        .first()
    )
    return result["rank"] if result else None"""


def get_date_range(zeitraum: str, heute: date) -> tuple[date | None, date | None]:
    offsets = {
        'Heute': timedelta(days=0),
        'Sieben Tage': timedelta(days=7),
        'Dreißig Tage': timedelta(days=30),
        'Dreihundertfünfundsechzig Tage': timedelta(days=365),
    }
    if zeitraum in offsets:
        return heute - offsets[zeitraum], heute
    return None, None


def get_klimapunkte_for_member(member, start: date | None, end: date | None) -> int:
    if start is not None and end is not None:
        aktionen = Aktion.objects.filter(user=member, date__range=(start, end))
    elif start is not None:
        aktionen = Aktion.objects.filter(user=member, date__gte=start)
    else:
        aktionen = Aktion.objects.filter(user=member)

    punkte = get_klimapunkte(aktionen) or 0
    return punkte


def get_klimapunkte_for_member_with_additional_climate_points(member, start: date | None, end: date | None) -> int:
    klimapunkte: int = get_klimapunkte_for_member(member, start, end)
    klimapunkte += get_additional_klimapunkte(member)
    return klimapunkte


def get_hall_of_fame_entries(user: User) -> int:
    return HallOfFameEntry.objects.filter(user=user).count()


# -- Optimized for dashboard --
def get_all_klimapunkte_from_user_prefetched(user, prefetched_aktionen):
    klimapunkte = get_klimapunkte(prefetched_aktionen)
    klimapunkte += get_additional_klimapunkte(user)
    return klimapunkte


def get_perfect_week_progress_optimized(user, date_given, prefetched_aktionen):
    week_start = date_given - timedelta(days=date_given.weekday())
    week_end = week_start + timedelta(days=6)

    covered_category_ids = set(
        prefetched_aktionen
        .filter(date__range=(week_start, week_end))
        .values_list('aktion__category_id', flat=True)
        .distinct()
    )

    output_de = {}
    output_en = {}
    for category in Category.objects.all():
        has_action = category.id in covered_category_ids
        output_de[category.name] = has_action
        output_en[category.name_en] = has_action

    return output_de, output_en


def get_level_prefetched(user, klimapunkte):
    levels = Level.objects.order_by('klimapunkte')

    current_level = None
    next_level = None
    level_number = 1
    progress_percent = 100

    for i, level in enumerate(levels):
        if klimapunkte >= level.klimapunkte:
            current_level = level
            if i + 1 < len(levels):
                next_level = levels[i + 1]
                differenz = next_level.klimapunkte - current_level.klimapunkte
                fortschritt = klimapunkte - current_level.klimapunkte
                progress_percent = int((fortschritt / differenz) * 100) if differenz > 0 else 100
                level_number = i + 1
            else:
                level_number = i + 1
                return {
                    'info': _(
                        'Du hast das höchste Level bereits erreicht: %(level)s <span class="emoji">&#x1F973;</span>') % {
                                'level': current_level.description},
                    'current_level': current_level, 'levels': levels, 'klimapunkte': klimapunkte,
                    'level_number': level_number}

    klimapunkte_missing = next_level.klimapunkte - klimapunkte

    return {'current_level': current_level, 'next_level': next_level, 'progress_percent': progress_percent,
            'levels': levels, 'klimapunkte_missing': klimapunkte_missing, 'level_number': level_number}


def get_family_rank_optimized(user, user_klimapunkte):
    family = (
        Family.objects
        .prefetch_related('members__usererweitert')
        .get(name='worldwide ranking')
    )

    members = family.members.all()

    member_ids = members.values_list('id', flat=True)

    klimapunkte_per_member = (
        Aktion.objects
        .filter(user_id__in=member_ids)
        .values('user_id')
        .annotate(total=Sum(F('aktion__klimapunkte') * F('quantity')))
    )
    klimapunkte_map = {entry['user_id']: entry['total'] or 0 for entry in klimapunkte_per_member}

    members_with_klimapunkte = []
    for member in members:
        base = klimapunkte_map.get(member.id, 0)
        additional = get_additional_klimapunkte(member)
        total = base + additional
        if member == user:
            total = user_klimapunkte
        members_with_klimapunkte.append((member, total))

    members_with_klimapunkte.sort(key=lambda x: x[1], reverse=True)

    rank = next(i for i, (member, _) in enumerate(members_with_klimapunkte) if member == user)
    return rank + 1
