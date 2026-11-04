from django.urls import path
from .views import (
    lot_create_view,
    lot_detail_view,
    lot_edit_view,
    zoo_dashboard_view,
    zoo_accept_lot_view,
    help_request_list_view,
    help_request_create_view,
    help_request_close_view,
)
from reservations.views import lot_reserve_view

urlpatterns = [
    path('create/', lot_create_view, name='lot_create'),
    path('<int:pk>/', lot_detail_view, name='lot_detail'),
    path('<int:pk>/edit/', lot_edit_view, name='lot_edit'),
    path('<int:pk>/reserve/', lot_reserve_view, name='lot_reserve'),
    path('zoo/incoming/', zoo_dashboard_view, name='zoo_dashboard'),
    path('zoo/lots/<int:pk>/accept/', zoo_accept_lot_view, name='zoo_accept_lot'),
    path('help/', help_request_list_view, name='help_request_list'),
    path('help/create/', help_request_create_view, name='help_request_create'),
    path('help/<int:pk>/close/', help_request_close_view, name='help_request_close'),
]
