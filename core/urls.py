from django.urls import path
from . import views

urlpatterns = [
    path('', views.lot_list_view, name='lot_list'),
]
