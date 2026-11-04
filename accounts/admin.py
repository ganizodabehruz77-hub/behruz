from django.contrib import admin
from .models import Profile, PartnerReview

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'phone', 'is_business', 'is_zoo_staff', 'rating_score')
    list_filter = ('is_business', 'is_zoo_staff')
    search_fields = ('user__username', 'company_name', 'phone')

@admin.register(PartnerReview)
class PartnerReviewAdmin(admin.ModelAdmin):
    list_display = ('partner', 'author', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('partner__username', 'author__username', 'comment')
