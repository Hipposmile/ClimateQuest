from django.urls import path

from .views import testers, aknachhaltigkeit

urlpatterns = [
    path('testers/', testers, name='testers'),
    path('aknachhaltigkeit/', aknachhaltigkeit, name='aknachhaltigkeit')
]
