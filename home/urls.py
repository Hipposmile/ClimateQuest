from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('count-benachrichtigungen/', count_benachrichtigungen, name='count_benachrichtigungen'),
    path('benachrichtigungen/', benachrichtigungen_view, name='benachrichtigungen_view'),
    path('delete-benachrichtigung/<int:id>', delete_benachrichtigung, name='delete_benachrichtigung'),
    path('admin/', admin, name='admin'),
    path('share/', share, name='share'),
    path('nutzungsbedingungen/', nutzungsbedingungen, name='nutzungsbedingungen'),
    path('datenschutz/', datenschutz, name='datenschutz'),
    path('impressum/', impressum, name='impressum'),
    path('aktionenTable/', actions_table, name='aktionenTable'),
]