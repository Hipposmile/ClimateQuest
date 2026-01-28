from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class AddAktionenSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['add']

    def location(self, item):
        return reverse(item)