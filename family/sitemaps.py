from django.contrib.sitemaps import Sitemap
from django.urls import reverse
    
class FamilyOverviewSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['families_view']

    def location(self, item):
        return reverse(item)

class AddFamilySitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['create_family']

    def location(self, item):
        return reverse(item)

class JoinFamilySitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['join_family']

    def location(self, item):
        return reverse(item)