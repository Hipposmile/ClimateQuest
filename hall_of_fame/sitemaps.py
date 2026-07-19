from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class HallOfFameDetailSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['hall_of_fame_detail']

    def location(self, item):
        return reverse(item)