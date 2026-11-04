from django.contrib import admin
from .models import Category, Location, ItemLot, HelpRequest

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'lot_type', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('title', 'district', 'address', 'is_zoo')
    list_filter = ('district', 'is_zoo')
    search_fields = ('title', 'address', 'district')

@admin.register(ItemLot)
class ItemLotAdmin(admin.ModelAdmin):
    list_display = ('title', 'donor', 'category', 'available_quantity', 'weight_kg', 'status', 'expiry_time', 'suitable_for_zoo')
    list_filter = ('status', 'suitable_for_zoo', 'category__lot_type', 'category')
    search_fields = ('title', 'description', 'donor__username')

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'district', 'urgency', 'status', 'created_at')
    list_filter = ('status', 'urgency', 'district', 'category')
    search_fields = ('title', 'description', 'author__username', 'district')
