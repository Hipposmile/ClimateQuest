from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class HomeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)


class DashboardSitemap(Sitemap):
    changefreq = "monthly"
    priority = 1.0

    def items(self):
        return ['dashboard']

    def location(self, item):
        return reverse(item)


class NutzungsbedingungenSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['nutzungsbedingungen']

    def location(self, item):
        return reverse(item)


class DatenschutzSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['datenschutz']

    def location(self, item):
        return reverse(item)


class ImpressumSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['impressum']

    def location(self, item):
        return reverse(item)

class SupportSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['support']

    def location(self, item):
        return reverse(item)

class FeedbackSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['feedback']

    def location(self, item):
        return reverse(item)