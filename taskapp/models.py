from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=now() + timedelta(days=7))
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("on hold", "On Hold")])

    def progress(self):
        tasks = self.tasks.all()
        if not tasks:
            return 0
        completed_tasks = tasks.filter(status="completed").count()
        return (completed_tasks / tasks.count()) * 100  # Percentage complete

    def __str__(self):
        return self.name
    


class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("marketplace", "Market Place"),
    ]

    PRIORITY_CHOICES = [
        ("high","High"),
        ("medium", "Medium"),
        ("low","Low"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name="tasks")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, default=None, related_name="tasks_assigned")
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks_created")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending",blank=True )
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    order = models.PositiveIntegerField(default=0)  # Defines task order
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="medium",blank=True )
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    update_requested = models.BooleanField(default=False)  # Manager requests update
    update_response = models.TextField(blank=True, null=True)  # User's response 
    
    def __str__(self):
        return self.title

class ToDoItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="todo_items")
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task