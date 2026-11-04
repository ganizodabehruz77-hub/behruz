from django.urls import path
from .views import (
    register,
    activate,
    login_user,
    logout_user,
    partner_list_view,
    partner_detail_view,
)

urlpatterns = [
    path('register/', register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', activate, name='activate'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('partners/', partner_list_view, name='partner_list'),
    path('partners/<str:username>/', partner_detail_view, name='partner_detail'),
]
