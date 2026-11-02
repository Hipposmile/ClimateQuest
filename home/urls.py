from django.urls import path

from .views import (
    admin,
    benachrichtigungen_view,
    companies_and_schools,
    count_benachrichtigungen,
    dashboard,
    datenschutz,
    delete_benachrichtigung,
    feedback,
    home,
    impressum,
    nutzungsbedingungen,
    support,
)

urlpatterns = [
    path("", home, name="home"),
    path("dashboard/", dashboard, name="dashboard"),
    path("count-benachrichtigungen/", count_benachrichtigungen, name="count_benachrichtigungen"),
    path("benachrichtigungen/", benachrichtigungen_view, name="benachrichtigungen_view"),
    path(
        "benachrichtigungen/<int:benachrichtigungen_id>/",
        benachrichtigungen_view,
        name="benachrichtigungen_view_focused",
    ),
    path("delete-benachrichtigung/<int:id>/", delete_benachrichtigung, name="delete_benachrichtigung"),
    path("admin/", admin, name="admin"),
    path("nutzungsbedingungen/", nutzungsbedingungen, name="nutzungsbedingungen"),
    path("datenschutz/", datenschutz, name="datenschutz"),
    path("impressum/", impressum, name="impressum"),
    path("companies-schools", companies_and_schools, name="companies_and_schools"),
    path("support/", support, name="support"),
    path("feedback/", feedback, name="feedback"),
]
