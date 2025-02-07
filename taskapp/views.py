from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user) if request.user.role == "employee" else Task.objects.all()
    return render(request, "tasklist.html", {"tasks": tasks})

@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tasklist")
    else:
        form = TaskForm()
    return render(request, "createtask.html", {"form": form})
