from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    company = models.ForeignKey('accountant.Company', on_delete=models.SET_NULL, blank=True, null=True, related_name='employees')
