from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'lot', 'user', 'reserved_units', 'pin_code', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('pin_code', 'user__username', 'lot__title')
