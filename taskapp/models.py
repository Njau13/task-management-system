from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    objectives = models.CharField(max_length=255,blank=True)
    stakeholders = models.EmailField(max_length=255,blank=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name="managed_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    start_date = models.DateTimeField()
    #due_date = models.DateTimeField(default=now() + timedelta(days=7))
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("on hold", "On Hold"), ("under_review", "Under Review")])

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
        ("submitforreview", "Submit for Review"),
        ("under_review", "Under Review"),
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
    update_requested = models.BooleanField(default=False)  # Manager requests update
    update_response = models.TextField(blank=True, null=True)  # User's response 
    explanation = models.TextField(blank=True, null=True)  # For review process
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_tasks")
    reviewed_at = models.DateTimeField(null=True, blank=True)  # Timestamp of review
    completed_on = models.DateTimeField(null=True, blank=True) 
    milestone = models.ForeignKey(
        'ProjectMilestone', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tasks'
    )
    
    def __str__(self):
        return self.title

class TaskAttachment(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Attachment for {self.task.title}"

class SubTask(models.Model):
    parent_task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ProjectObjective(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_objectives')
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.description[:50]}"

class ProjectStakeholder(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_stakeholders')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

class ProjectMilestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.title}"

class ProjectMember(models.Model):
    ROLE_CHOICES = (
        ('member', 'Team Member'),
        ('leader', 'Team Leader'),
        ('observer', 'Observer'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.project.name} - {self.user.username} ({self.role})"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('project_invite', 'Project Invitation'),
        ('task_assigned', 'Task Assigned'),
        ('update_requested', 'Update Requested'),
        ('update_provided', 'Update Provided'),
        ('task_completed', 'Task Completed'),
        ('milestone_due', 'Milestone Due'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    related_task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class TaskReview(models.Model):
    REVIEW_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reviews')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reviews')
    comment = models.TextField()
    status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_reviews', null=True, blank=True)
    reviewer_comment = models.TextField(null=True, blank=True)
    attachments = models.FileField(upload_to="task_reviews/", blank=True, null=True)
    ratings = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="Rate between 1 and 5")

    def __str__(self):
        return f"Review for {self.task.title} - {self.status}"


