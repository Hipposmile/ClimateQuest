from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Artikel


class ArtikelDetailSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.9

    def items(self):
        return Artikel.objects.all()

    def lastmod(self, obj):
        return obj.date_time
    
    def location(self, obj):
        return reverse('artikel_detail', args=[obj.id])
    
class ArtikelOverviewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ['artikel_overview']

    def location(self, item):
        return reverse(item)

class AddArtikelSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['add_artikel']

    def location(self, item):
        return reverse(item)