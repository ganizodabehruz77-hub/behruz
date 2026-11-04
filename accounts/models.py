from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    address = models.CharField(max_length=200, blank=True)
    is_business = models.BooleanField(default=False)
    is_zoo_staff = models.BooleanField(default=False)
    rating_score = models.PositiveIntegerField(default=100)
    avatar = models.ImageField(upload_to='avatars', blank=True, null=True)

    def __str__(self):
        return f'Профиль {self.user.username}'


class PartnerReview(models.Model):
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.author.username} для {self.partner.username} ({self.rating}★)"
