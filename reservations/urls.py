from django.urls import path
from . import views

urlpatterns = [
    path('lots/<int:pk>/reserve/', views.lot_reserve_view, name='lot_reserve'),
    path('<int:pk>/cancel/', views.reservation_cancel_view, name='reservation_cancel'),
    path('<int:pk>/confirm/', views.reservation_confirm_view, name='reservation_confirm'),
    path('<int:pk>/confirm-qr/<str:pin>/', views.reservation_confirm_qr_view, name='reservation_confirm_qr'),
    path('<int:pk>/chat/', views.reservation_chat_view, name='reservation_chat'),
    path('my-cabinet/', views.user_cabinet_view, name='user_cabinet'),
]
