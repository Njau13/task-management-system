from django import forms
from .models import Task, Project, User, TaskReview
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
        fields = ["name", "description", "objectives","due_date","stakeholders", "start_date" ]

        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "start_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date < now():
            raise forms.ValidationError("Due date and time cannot be in the past. Please select a valid date")
        return start_date

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        start_date = self.cleaned_data.get("start_date")

        if due_date and due_date < now():
            raise forms.ValidationError("Due date and time cannot be in the past. Please select a valid date.")

        if start_date and due_date and due_date < start_date:
            raise forms.ValidationError("Due date cannot be before the start date.")

        return due_date
        
class AssignTaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(queryset=User.objects.all(), label="Reassign Task To")

    class Meta:
        model = Task
        fields = ['assigned_to','status']


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


class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['update_response', "status"]  # Only include the response field

class TaskReviewForm(forms.ModelForm):
    class Meta:
        model = TaskReview
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Explain what you have completed...'}),
        }

class TaskReviewResponseForm(forms.ModelForm):
    class Meta:
        model = TaskReview
        fields = ['reviewer_comment', 'status', 'attachments']
        widgets = {
            'reviewer_comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide feedback...'}),
        }