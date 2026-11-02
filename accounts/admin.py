from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'is_business', 'is_zoo_staff', 'rating_score')
    list_filter = ('is_business', 'is_zoo_staff')
    search_fields = ('user__username', 'phone')
