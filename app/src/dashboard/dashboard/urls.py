"""dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from .views import index, get_iiko_api_key

from core.views import get_nomenclature_api, search_nomenclature_api, sync_nomenclature_api
from authentication.urls import urlpatterns as auth_patterns

urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('stats/', include('stats.urls')),
    path('waybills/', include('waybills.urls')),
    path('spending/', include('spending.urls')),
    path('writeoffs/', include('writeoffs.urls')),
    path('git/', include('git.urls')),
    path('iiko-api-key', get_iiko_api_key),
    
    # API для номенклатуры
    path('api/nomenclature', get_nomenclature_api),
    path('api/nomenclature/search', search_nomenclature_api),
    path('api/nomenclature/sync', sync_nomenclature_api),
]

urlpatterns += auth_patterns
