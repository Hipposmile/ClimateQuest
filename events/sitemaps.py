from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Event


class EventDetailSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Event.objects.all()

    def lastmod(self, obj):
        return obj.last_modified
    
    def location(self, obj):
        return reverse('event_detail', args=[obj.id])
    
class EventsOverviewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['events_overview']

    def location(self, item):
        return reverse(item)

class AddEventSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['add_event']

    def location(self, item):
        return reverse(item)