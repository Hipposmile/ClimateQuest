from django.contrib.sitemaps import Sitemap
from django.urls import reverse
    
class CommunityOverviewSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['communities_view']

    def location(self, item):
        return reverse(item)

class AddCommunitySitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['create_community']

    def location(self, item):
        return reverse(item)

class JoinCommunitySitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['join_community']

    def location(self, item):
        return reverse(item)