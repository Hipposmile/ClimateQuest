from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('count-benachrichtigungen/', count_benachrichtigungen, name='count_benachrichtigungen'),
    path('benachrichtigungen/', benachrichtigungen_view, name='benachrichtigungen_view'),
    path('delete-benachrichtigung/<int:id>', delete_benachrichtigung, name='delete_benachrichtigung'),
    path('admin/', admin, name='admin_view'),
    path('share/', share, name='share')
]