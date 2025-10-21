from django.contrib.sitemaps import Sitemap
from django.urls import reverse
    
class LoginSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['login_view']

    def location(self, item):
        return reverse(item)

class RegisterSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['register_view']

    def location(self, item):
        return reverse(item)

class PersonalSettingsSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['settings_view']

    def location(self, item):
        return reverse(item)
    
class ResetPasswordSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['reset_password']

    def location(self, item):
        return reverse(item)

class VerifyEmailSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return ['verifyEmail']

    def location(self, item):
        return reverse(item)