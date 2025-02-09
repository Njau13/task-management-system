from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta

User = get_user_model()

@login_required
def task_list(request):
    filter_type = request.GET.get("filter")  # Get filter from URL
    today = datetime.today().date()

    tasks = Task.objects.filter(assigned_to=request.user)
    
    # **Apply additional filters dynamically using `Q`**
    filter_conditions = Q()

    if filter_type == "today":
        filter_conditions &= Q(due_date=today)
    elif filter_type == "tomorrow":
        filter_conditions &= Q(due_date=today + timedelta(days=1))
    elif filter_type == "this_week":
        week_start = today - timedelta(days=today.weekday())  # Start of the week (Monday)
        week_end = week_start + timedelta(days=6)  # End of the week (Sunday)
        filter_conditions &= Q(due_date__range=[week_start, week_end])
    elif filter_type == "this_month":
        filter_conditions &= Q(due_date__month=today.month)
    elif filter_type == "pending":
        filter_conditions &= Q(status="pending")
    elif filter_type == "in_progress":
        filter_conditions &= Q(status="in_progress")
    elif filter_type == "completed":
        filter_conditions &= Q(status="completed")

    # **Apply filters**
    tasks = tasks.filter(filter_conditions)

    return render(request, "tasklist.html", {"tasks": tasks})


@login_required
def manager_list(request):
    tasks_pending = Task.objects.filter(status="pending") 
    tasks_in_progress = Task.objects.filter(status="in_progress") 
    tasks_completed = Task.objects.filter(status="completed") 
    return render(request, "manager.html", {"tasks_pending": tasks_pending,
        "tasks_in_progress": tasks_in_progress,
        "tasks_completed": tasks_completed,})

@login_required
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            #form.save()
            task = form.save(commit=False)
            task.assigned_by = request.user  # Set the user who assigned the task
            task.save()
            return redirect("tasklist")
    else:
        form = TaskForm()        
    return render(request, "createtask.html", {"form": form})

class TaskDetailView(View):
    def get(self, request, pk):
        task = Task.objects.get(id=pk)
        return render(request, "taskdetail.html", {"task": task})

    def post(self, request, pk):
        task = Task.objects.get(id=pk)
        task.status = request.POST.get("status")
        task.save()
        return redirect("taskdetail", pk=task.id)

def testlist(request):
    return render(request, "tests.html")