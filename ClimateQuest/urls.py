"""
URL configuration for ClimateQuest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

from home.sitemaps import HomeSitemap, NutzungsbedingungenSitemap, AktionenTableSitemap, SupportSitemap, FeedbackSitemap
from artikel.sitemaps import ArtikelDetailSitemap, ArtikelOverviewSitemap, AddArtikelSitemap
from events.sitemaps import EventDetailSitemap, EventsOverviewSitemap, AddEventSitemap
from forum.sitemaps import ForumOverviewSitemap, ForumPostDetailSitemap, AddForumPostSitemap
from family.sitemaps import FamilyOverviewSitemap, AddFamilySitemap, JoinFamilySitemap
from community.sitemaps import CommunityOverviewSitemap, AddCommunitySitemap, JoinCommunitySitemap
from personals.sitemaps import LoginSitemap, RegisterSitemap, PersonalSettingsSitemap, ResetPasswordSitemap
from users.sitemaps import KlimapunkteViewSitemap, LevelViewSitemap, HistorySitemap
from aktionen.sitemaps import AddAktionenSitemap
from pages.sitemaps import MobileAppsSitemap, AknachhaltigkeitSitemap
from hall_of_fame.sitemaps import HallOfFameDetailSitemap

sitemaps = {
    "home": HomeSitemap(),
    "nutzungsbedingungen": NutzungsbedingungenSitemap(),
    "aktionen_table": AktionenTableSitemap(),
    "support": SupportSitemap(),
    "feedback": FeedbackSitemap(),

    "family_overview": FamilyOverviewSitemap(),
    "add_family": AddFamilySitemap(),
    "join_family": JoinFamilySitemap(),

    "community_overview": CommunityOverviewSitemap(),
    "add_community": AddCommunitySitemap(),
    "join_community": JoinCommunitySitemap(),

    "login": LoginSitemap(),
    "register": RegisterSitemap(),
    "personal_settings": PersonalSettingsSitemap(),
    "reset_password": ResetPasswordSitemap(),

    "klimapunkte_view": KlimapunkteViewSitemap(),
    "level_view": LevelViewSitemap(),
    "history": HistorySitemap(),

    "add_aktionen": AddAktionenSitemap(),

    "artikel_detail": ArtikelDetailSitemap(),
    "artikel_overview": ArtikelOverviewSitemap(),
    "add_artikel": AddArtikelSitemap(),

    "event_detail": EventDetailSitemap(),
    "events_overview": EventsOverviewSitemap(),
    "add_event": AddEventSitemap(),

    "forum_post_detail": ForumPostDetailSitemap(),
    "forum_overview": ForumOverviewSitemap(),
    "add_forum_post": AddForumPostSitemap(),

    "mobile_apps": MobileAppsSitemap(),
    "aknachhaltigkeit": AknachhaltigkeitSitemap(),

    "hall_of_fame_detail": HallOfFameDetailSitemap(),
}

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('ClimateQuestAdmin/', admin.site.urls),
    path('', include('home.urls')),
    path('personals/', include('personals.urls')),
    path('aktionen/', include('aktionen.urls')),
    path('community/', include('community.urls')),
    path('family/', include('family.urls')),
    path('users/', include('users.urls')),
    path('events/', include('events.urls')),
    path('artikel/', include('artikel.urls')),
    path('forum/', include('forum.urls')),
    path('petitions/', include('petitions.urls')),
    path('hall_of_fame/', include('hall_of_fame.urls')),
    path('pages/', include('pages.urls')),

    # Notifications
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/x-javascript')),
    path('.well-known/assetlinks.json',
         TemplateView.as_view(template_name='assetlinks.json', content_type='application/json')),
    path('apple-app-site-association',
         TemplateView.as_view(template_name='aasa.json', content_type='application/json')),

    # Webpush
    path('webpush/', include('webpush.urls')),

    # Hot Reload
    path("__reload__/", include("django_browser_reload.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'core.views.custom_400'
handler403 = 'core.views.custom_403'
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
handler503 = 'core.views.custom_503'
