from django.contrib.sitemaps import Sitemap
from django.urls import reverse
    
class HomeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)

class NutzungsbedingungenSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['nutzungsbedingungen']

    def location(self, item):
        return reverse(item)
    
class AktionenTableSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ['aktionenTable']

    def location(self, item):
        return reverse(item)

class ShareSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['share']

    def location(self, item):
        return reverse(item)