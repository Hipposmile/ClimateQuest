from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class TestersSitemap(Sitemap):
    changefreq = "monthly"
    priority = 4.0

    def items(self):
        return ['testers']

    def location(self, item):
        return reverse(item)


class AknachhaltigkeitSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.1

    def items(self):
        return ['aknachhaltigkeit']

    def location(self, item):
        return reverse(item)