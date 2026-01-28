from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.contrib.auth.models import User

class KlimapunkteViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return User.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.last_login

    def location(self, obj):
        return reverse('klimapunkte_view', args=[obj.pk])

class LevelViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return User.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.last_login

    def location(self, obj):
        return reverse('klimapunkte_view', args=[obj.pk])

class HistorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return User.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.last_login

    def location(self, obj):
        return reverse('history', args=[obj.pk])