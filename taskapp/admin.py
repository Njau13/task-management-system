from django.contrib import admin
from .models import Project, Task ,TaskAttachment ,SubTask, ProjectObjective, ProjectStakeholder, ProjectMember, ProjectMilestone, Notification

class SubTaskInline(admin.TabularInline):
    model = Task
    extra = 1

class TaskAdmin(admin.ModelAdmin):
    inlines = [SubTaskInline]
    
admin.site.register(Task)
admin.site.register(SubTask)


