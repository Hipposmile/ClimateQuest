from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import bleach
from django.utils import timezone
import traceback
from ClimateQuest import settingsprod
from artikel.models import Artikel
from home.models import *
from verbrauch.models import *
from family.models import *
from community.models import *
from personals.models import *
from datetime import datetime, timedelta, date
import random
import string

dezimalstellen = 2


# messages don´t use core.all_messages here because this would complicate everything

def generateRandomPassword():
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))


def send_mail_function(**kwargs):
    request = kwargs.get('request')
    fehlermeldung = kwargs.get('fehlermeldung', 'Fehler beim E-Mail-Versand')
    subject = kwargs.get('subject')
    message = kwargs.get('message')
    fail_silently = kwargs.get('fail_silently')
    mailinglist_needless = kwargs.get('mailinglist_needless')

    if request is None or subject is None or message is None or fail_silently is None:
        createInternerFehler(request, 'Beim E-Mail Versand wurden nicht alle notwendigen Elemente übergeben',
                             fehlermeldung)

    user = kwargs.get('user')
    if not user:
        try:
            user = request.user
        except Exception:
            createInternerFehler(request, 'Bei send_mail_function wurde kein User übergeben', fehlermeldung)

    recipient_list = kwargs.get('recipient_list')
    if not recipient_list:
        recipient_list = [user.email]

    if not mailinglist_needless and user.email != '':
        try:
            userErweitert = UserErweitert.objects.get(user=user)
        except UserErweitert.DoesNotExist:
            createInternerFehler(request, f'UserErweitert zu User {user} nicht gefunden', fehlermeldung)
        if userErweitert.mail_verified == False:
            return True
        if userErweitert.mailinglist:
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
                createInternerFehler(request, f'Fehler beim E-Mail-Versand an {recipient_list}: {e}', fehlermeldung)

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
            createInternerFehler(request, f'Fehler beim E-Mail-Versand an {recipient_list}: {e}', fehlermeldung)
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
                    'info': f'Du hast das höchste Level bereits erreicht: {current_level.description} <span class="emoji">&#x129395;</span>',
                    'current_level': current_level, 'levels': levels, 'klimapunkte': klimapunkte,
                    'level_number': level_number}

    return {'current_level': current_level, 'next_level': next_level, 'progress_percent': progress_percent,
            'levels': levels, 'klimapunkte': klimapunkte, 'level_number': level_number}


def get_klimapunkte(aktionen):
    klimapunkte = sum(aktion.impact for aktion in aktionen)
    return klimapunkte


def createInternerFehler(request, beschreibung, fehlermeldung="interner Fehler", exception=None):
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
    with open('logs/errors.log', 'a') as file:
        file.write(f'{error_message}\n\n')


def createBenachrichtigung(request, benachrichtigung, user=None):
    if user is None:
        user = request.user
    Benachrichtigung.objects.create(benachrichtigung=benachrichtigung, user=user)
    send_mail_function(
        request=request,
        fehlermeldung='Beim Erstellen einer Benachrichtigung ist beim Versenden der E-Mail ein Fehler aufgetreten. Die Benachrichtigung kann nur in dem Benachrichtigungsteil hier auf der Webseite gefunden werden!',
        subject='ClimateQuest - neue Benachrichtigung',
        message=benachrichtigung,
        recipient_list=user.email,
        fail_silently=False,
        user=user
    )


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
        createInternerFehler(request, 'Family "worldwide ranking" existiert nicht')
        return False


def getFamiliesOfUser(user):
    return Family.objects.filter(members=user).order_by('name')


def getCommunitiesOfUser(user):
    # Hole die IDs der Familien des aktuellen Nutzers
    user_families = getFamiliesOfUser(user)

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
