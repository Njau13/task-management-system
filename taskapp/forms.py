from django import forms
from .models import Task
from django.utils.timezone import now

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "assigned_to", "status", "due_date"]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < now():
            raise forms.ValidationError("Due date and time cannot be in the past. Please select a valid date")
        return due_date