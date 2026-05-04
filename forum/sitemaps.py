from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import ForumPost


class ForumPostDetailSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return ForumPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('post_detail', args=[obj.id])

class ForumOverviewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ['forum_overview']

    def location(self, item):
        return reverse(item)

class AddForumPostSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['add_forum_post']

    def location(self, item):
        return reverse(item)