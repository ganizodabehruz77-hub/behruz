from django.urls import path
from . import views

urlpatterns = [
    path('', views.lot_list_view, name='lot_list'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/go/', views.notification_click_view, name='notification_click'),
]
