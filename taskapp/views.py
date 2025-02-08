from django.shortcuts import render, redirect
from .models import Task
from .forms import TaskForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views import View
from django.db.models import Q

User = get_user_model()

@login_required
def task_list(request):
    #tasks = Task.objects.filter(assigned_to=request.user) if request.user.role == "employee" else Task.objects.all()
    tasks_pending = Task.objects.filter( Q(status="pending") & (Q(assigned_to=request.user) if request.user.role == "employee" else Q()))
    tasks_in_progress = Task.objects.filter(Q(status="in_progress") & (Q(assigned_to=request.user) if request.user.role == "employee" else Q()))
    tasks_completed = Task.objects.filter(Q(status="completed") & (Q(assigned_to=request.user) if request.user.role == "employee" else Q()))
    return render(request, "tasklist.html", { "tasks_pending": tasks_pending,
        "tasks_in_progress": tasks_in_progress,
        "tasks_completed": tasks_completed,})

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