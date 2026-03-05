from django.urls import path

from .views import login_view, register_view, logout_view, settings_view, reset_password, credit_view, check_username, check_email, get_email_settings, activate, resend_verification_email

urlpatterns = [
    # Personals
    path('login/', login_view, name='login_view'),
    path('register/', register_view, name='register_view'),
    path('logout/', logout_view, name='logout_view'),
    path('settings/', settings_view, name='settings_view'),
    path('reset_password/', reset_password, name='reset_password'),
    path('credits/', credit_view, name='credit_view'),
    path('check-username/', check_username, name='check_username'),
    path('check-email/', check_email, name='check_email'),
    path('get_email_settings/', get_email_settings, name='get_email_settings'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('resend_verification_email/', resend_verification_email, name='resend_verification_email'),
]