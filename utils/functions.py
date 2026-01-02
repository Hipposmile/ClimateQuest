import random
import string
import traceback
import logging

import bleach
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from webpush import send_user_notification

from ClimateQuest import settingsprod
from artikel.models import Artikel
from community.models import *
from home.models import *
from personals.models import *
from verbrauch.models import *

dezimalstellen = 4

logger = logging.getLogger("django")

def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation.replace('"', '').replace("'", ""), k=12)) # Removes " so string can´t be interrupted

def send_mail_function(**kwargs):
    request = kwargs.get('request')
    fehlermeldung = kwargs.get('fehlermeldung', 'Fehler beim E-Mail-Versand')
    subject = kwargs.get('subject')
    message = kwargs.get('message')
    fail_silently = kwargs.get('fail_silently')
    mailinglist_needless = kwargs.get('mailinglist_needless')

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
    <style>
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
        {message}
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
                <style>
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
                    {message}
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
    # Klimapunkte abrufen
    klimapunkte = get_klimapunkte(aktionen)
    klimapunkte += get_klimapunkte_from_likes(user)

    # Alle Level sortiert abrufen
    levels = Level.objects.order_by('klimapunkte')

    # Variablen einführen
    current_level = None
    next_level = None
    level_number = 1
    progress_percent = 100  # Default für höchstes Level

    for i, level in enumerate(levels):
        if klimapunkte >= level.klimapunkte:
            current_level = level
            # Wenn es noch ein Level danach gibt:
            if i + 1 < len(levels):
                next_level = levels[i + 1]
                differenz = next_level.klimapunkte - current_level.klimapunkte
                fortschritt = klimapunkte - current_level.klimapunkte
                progress_percent = int((fortschritt / differenz) * 100) if differenz > 0 else 100
                level_number = i + 1
            else:
                level_number = i + 1
                return {
                    'info': f'Du hast das höchste Level bereits erreicht: {current_level.description} <span class="emoji">&#x1F973;</span>',
                    'current_level': current_level, 'levels': levels, 'klimapunkte': klimapunkte,
                    'level_number': level_number}

    return {'current_level': current_level.description, 'next_level': next_level.description, 'progress_percent': progress_percent,
            'levels': levels, 'klimapunkte': klimapunkte, 'level_number': level_number}


def get_all_klimapunkte_from_user(user):
    aktionen = Aktion.objects.filter(user=user)
    klimapunkte = get_klimapunkte(aktionen)
    klimapunkte += get_klimapunkte_from_likes(user)
    return klimapunkte

def get_klimapunkte(aktionen):
    klimapunkte = sum(aktion.impact for aktion in aktionen)
    return klimapunkte


def create_internal_error(request, beschreibung, fehlermeldung="interner Fehler", exception=None):
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
    messages.error(request, fehlermeldung)

    logging.error(error_message)

    with open('logs/errors.log', 'a') as file:
        file.write(f'{error_message}\n\n')


def create_notification(request, notification, user=None):
    if user is None:
        user = request.user
    Benachrichtigung.objects.create(benachrichtigung=notification, user=user)
    send_mail_function(
        request=request,
        fehlermeldung='Beim Erstellen einer Benachrichtigung ist beim Versenden der E-Mail ein Fehler aufgetreten. Die Benachrichtigung kann nur in dem Benachrichtigungsteil hier auf der Webseite gefunden werden!',
        subject='ClimateQuest - neue Benachrichtigung',
        message=notification,
        recipient_list=user.email,
        fail_silently=False,
        user=user
    )
    res = send_push(benachrichtigung=notification, user=user)
    if res == 500:
        create_internal_error(request, "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.", "Beim Erstellen einer Benachrichtigung an das Gerät ist ein Fehler aufgetreten.")

def send_push(benachrichtigung, user, head="Neue Benachrichtigung"):
    try:
        payload = {'head': head, 'body': benachrichtigung}
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
