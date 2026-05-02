from django.urls import path
from . import views


urlpatterns = [
    path('', views.writeoffs_view),
    path('create', views.CreateWriteoffView.as_view()),
    path('pending', views.get_pending_writeoffs),
    path('<int:pk>', views.writeoff_view),
    path('<int:pk>/api/', views.writeoff_view_api),
    path('<int:pk>/<str:action>', views.process_writeoff),
]
