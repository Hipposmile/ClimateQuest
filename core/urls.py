from django.urls import path, include
from .views import home, send_push
from django.views.generic import TemplateView

urlpatterns = [
    path('', home),
    path('send_push', send_push),
    path('webpush/', include('webpush.urls')),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/x-javascript'))
]
