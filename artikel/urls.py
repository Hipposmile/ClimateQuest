from django.urls import path

from .views import artikel_overview, add_artikel, artikel_detail, edit_artikel, add_like

urlpatterns = [
    path('artikel_overview/', artikel_overview, name='artikel_overview'),
    path('add_artikel/', add_artikel, name='add_artikel'),
    path('artikel_detail/<int:artikel_id>', artikel_detail, name='artikel_detail'),
    path('edit_artikel/<int:artikel_id>', edit_artikel, name='edit_artikel'),
    path('add_like/<int:artikel_id>', add_like, name='add_like_artikel'),
]
