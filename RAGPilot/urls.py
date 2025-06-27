"""
URL configuration for RAGPilot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views. home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('', include('home.urls')),
    path('profile/', include('profiles.urls')),
    path('admin/', admin.site.urls),
    path('', include('crawlers.urls')),
    path('conversations/', include('conversations.urls')),
    path('sources/', include('sources.urls')),
    path('accounts/', include('allauth.urls')),  # allauth URLs
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicon.ico')), name='favicon'),
]

# 在開發模式下提供靜態檔案
if settings.DEBUG:
    # 在開發模式下，Django 會自動尋找靜態檔案
    # 但我們還是明確加上以確保正確
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
