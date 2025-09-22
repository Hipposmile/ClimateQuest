"""
URL configuration for ClimateQuest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
#import debug_toolbar

urlpatterns = [
    path('ClimateQuestAdmin/', admin.site.urls),
    path('', include('home.urls')),
    path('personals/', include('personals.urls')),
    path('verbrauch/', include('verbrauch.urls')),
    path('community/', include('community.urls')),
    path('family/', include('family.urls')),
    path('users/', include('users.urls')),
    path('events/', include('events.urls')),
    path('artikel/', include('artikel.urls')),
    path('forum/', include('forum.urls')),
]

#if settings.DEBUG:
#    urlpatterns += [
#        path('__debug__/', include(debug_toolbar.urls)),
#    ]

handler400 = 'core.views.custom_400'
handler403 = 'core.views.custom_403'
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
handler503 = 'core.views.custom_503'