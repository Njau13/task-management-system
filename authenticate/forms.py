from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)
    department = forms.ChoiceField(choices=CustomUser.DEPARTMENT_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "role", "password1", "password2"]
