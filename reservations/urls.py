from django.urls import path
from . import views

urlpatterns = [
    path('lots/<int:pk>/reserve/', views.lot_reserve_view, name='lot_reserve'),
    path('<int:pk>/cancel/', views.reservation_cancel_view, name='reservation_cancel'),
    path('<int:pk>/confirm/', views.reservation_confirm_view, name='reservation_confirm'),
    path('my-cabinet/', views.user_cabinet_view, name='user_cabinet'),
]
