from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)
    report_to = forms.ModelChoiceField(queryset=CustomUser.objects.all(), required=False)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "role","report_to", "password1", "password2"]
