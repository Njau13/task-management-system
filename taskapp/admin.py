from django.contrib import admin
from .models import Task

class SubTaskInline(admin.TabularInline):
    model = Task
    extra = 1

class TaskAdmin(admin.ModelAdmin):
    inlines = [SubTaskInline]
    
admin.site.register(Task)


