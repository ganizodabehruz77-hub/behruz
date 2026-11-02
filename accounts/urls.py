from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register, name='register'),
    path('activate/<str:uidb64>/<str:token>/', activate, name='activate'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
]
