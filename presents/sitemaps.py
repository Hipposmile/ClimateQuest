from django.contrib.sitemaps import Sitemap
from django.urls import reverse
    
class AddPresentSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['add_present']

    def location(self, item):
        return reverse(item)

class PresentsOverviewSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['presents_overview']

    def location(self, item):
        return reverse(item)