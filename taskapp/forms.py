from django import forms
from .models import Task, Project, User
from django.utils.timezone import now

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status", "priority", "due_date",  "project", "assigned_to"  ]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }
        assigned_to = forms.ModelChoiceField(
            queryset=User.objects.all(), required=False
        )

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < now():
            raise forms.ValidationError("Due date and time cannot be in the past. Please select a valid date")
        return due_date

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "due_date"]

        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }
    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < now():
            raise forms.ValidationError("Due date and time cannot be in the past. Please select a valid date")
        return due_date
        
class AssignTaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(queryset=User.objects.all(), label="Reassign Task To")

    class Meta:
        model = Task
        fields = ['assigned_to']


class SubTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description']

class RequestUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = []  # No input needed, just toggles `update_requested`


class ProvideUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status', 'update_response']
        widgets = {
            'update_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide an update...'}),
        }