from django.urls import path
from . import views


urlpatterns = [
    path('webhooks/github', views.github_webhook),
    path('webhooks/gitea', views.gitea_webhook),
]
