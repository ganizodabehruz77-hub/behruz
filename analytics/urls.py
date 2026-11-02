from django.urls import path
from . import views

urlpatterns = [
    path('impact/', views.impact_stats_view, name='impact_stats'),
]
