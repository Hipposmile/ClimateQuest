from django.urls import path

from .views import add_event, edit_event, event_detail, events_overview

urlpatterns = [
    path("overview/", events_overview, name="events_overview"),
    path("detail/<int:event_id>/", event_detail, name="event_detail"),
    path("add/", add_event, name="add_event"),
    path("edit/<int:event_id>/", edit_event, name="edit_event"),
]
