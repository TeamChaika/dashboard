from django.urls import path
from . import views


urlpatterns = [
    path('', views.waybills_view('all')),
    path('create', views.CreateWaybillView.as_view()),
    path('pending', views.get_pending_waybills),
    path('<int:pk>', views.waybill_view),
    path('<int:pk>/api/', views.waybill_view_api),
    path('<int:pk>/edit', views.EditWaybillView.as_view()),
    path('<int:pk>/<str:action>', views.process_waybill),
    path('incoming', views.waybills_view('incoming')),
    path('outgoing', views.waybills_view('outgoing')),
]
