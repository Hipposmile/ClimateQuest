from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    # Personals
    path('login/', login_view, name='login_view'),
    path('register/', register_view, name='register_view'),
    path('verify-email/', verifyEmail, name='verifyEmail'),
    path('logout/', logout_view, name='logout_view'),
    path('settings/', settings_view, name='settings_view'),
    path('reset_password/', reset_password, name='reset_password'),
    path('check-username/', check_username, name='check_username'),
    path('check-email/', check_email, name='check_email'),
    path('get_email_settings/', get_email_settings, name='get_email_settings'),
]