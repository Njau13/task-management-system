from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):  
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("employee", "Employee"),
    ]
    DEPARTMENT_CHOICES = [
        ("hr", "Human Resources"),
        ("treasury","Treasury"),
        ("operations","Operations"),
        ("risk", "Risk Management"),
        ("technology","Technology"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="employee")
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default="technology")


    #report_to = models.ForeignKey(AbstractUser, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="manager")