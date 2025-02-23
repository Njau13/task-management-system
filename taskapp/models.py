from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")])

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

    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, default=None, related_name="tasks")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="tasks_assigned")
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks_created")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending",blank=True )
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    order = models.PositiveIntegerField(default=0)  # Defines task order

    def __str__(self):
        return self.title
