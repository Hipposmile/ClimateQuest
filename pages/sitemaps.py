from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class MobileAppsSitemap(Sitemap):
    changefreq = "monthly"
    priority = 4.0

    def items(self):
        return ['mobile_apps']

    def location(self, item):
        return reverse(item)


class AknachhaltigkeitSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.1

    def items(self):
        return ['aknachhaltigkeit']

    def location(self, item):
        return reverse(item)