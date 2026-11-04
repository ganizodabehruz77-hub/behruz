from django.db import models
import random
from django.contrib.auth.models import User
from lots.models import ItemLot


def generate_pin_code():
    return f'{random.randint(1000,9999)}'


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'В ожидании'),
        ('completed', 'Получено'),
        ('cancelled', 'Отменено'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    lot = models.ForeignKey(ItemLot, on_delete=models.CASCADE, related_name='reservations')
    reserved_units = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    pin_code = models.CharField(max_length=4, default=generate_pin_code)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Бронь #{self.id}: {self.lot.title} для {self.user.username} (PIN: {self.pin_code})"


class ReservationMessage(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservation_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Сообщение от {self.sender.username} к брони #{self.reservation.id}"
