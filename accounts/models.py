from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='profile')
    phone =models.CharField(max_length=100)
    is_business = models.BooleanField(default=False)
    is_zoo_staff=models.BooleanField(default=False)
    rating_score=models.PositiveIntegerField(default=100)
    avatar = models.ImageField(upload_to='avatars',blank=True,null=True)
    def __str__(self):
        return f'Профиль {self.user.username}'
