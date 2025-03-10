from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):  
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("employee", "Employee"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="employee")
    #report_to = models.ForeignKey(AbstractUser, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="manager")