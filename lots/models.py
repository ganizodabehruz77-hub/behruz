from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    LOT_TYPE_CHOICES = [
        ('food', 'Еда'),
        ('items', 'Вещи'),
    ]
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    lot_type = models.CharField(max_length=20, choices=LOT_TYPE_CHOICES)

    def __str__(self):
        return f'{self.name}'


class Location(models.Model):
    title = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    pickup_instructions = models.TextField()
    is_zoo = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.district})"


class ItemLot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('reserved', 'Забронирован'),
        ('completed', 'Передан человеку'),
        ('to_zoo', 'Направлен в зоопарк'),
        ('zoo_received', 'Принят зоопарком'),
        ('expired', 'Списан в утиль'),
    ]
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lots')
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(Category, related_name="lots", on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='lots')
    quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    expiry_time = models.DateTimeField()
    image = models.ImageField(upload_to='lots', blank=True, null=True)
    suitable_for_zoo = models.BooleanField(default=False)
    zoo_notes = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return self.expiry_time <= timezone.now()

    @property
    def is_food(self):
        return self.category.lot_type == 'food'


class HelpRequest(models.Model):
    STATUS_CHOICES = [
        ('open', 'Ищет помощь'),
        ('in_progress', 'Помощь в пути'),
        ('closed', 'Помощь получена'),
    ]
    URGENCY_CHOICES = [
        ('normal', 'Обычная'),
        ('high', 'Срочно!'),
    ]
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_requests')
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='help_requests')
    district = models.CharField(max_length=100)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    contact_phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.author.username})"
