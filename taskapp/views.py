from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Task
from .forms import  ProjectForm, TaskForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import DetailView
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, localtime

User = get_user_model()

@login_required
def employee_dashboard(request):
    tasks_pending = Task.objects.filter(assigned_to=request.user, status="pending")
    tasks_completed = Task.objects.filter(assigned_to=request.user, status="completed")
    tasks_in_progress = Task.objects.filter(assigned_to=request.user, status="in_progress")
    today = localtime().date()
    tasks_today =Task.objects.filter(assigned_to=request.user, due_date__date=today) #Uses .date() to match only the date part of due_date (ignores time).
    overdue = localtime().date()
    tasks_overdue= Task.objects.filter(assigned_to=request.user, due_date__date__lt=overdue).exclude(status="completed") #lt means less than today
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_to = request.user  # Assign task to logged-in user
            task.assigned_by = request.user
            task.save()
            return redirect("employee_dashboard")  # Refresh the page after adding
    else:
        form = TaskForm()

    return render(request, "dashboard.html", {
        "tasks_pending": tasks_pending,
        "tasks_completed": tasks_completed,
        "tasks_in_progress": tasks_in_progress,
        "tasks_today":tasks_today,
        "tasks_overdue":tasks_overdue,
        "form": form,
    })

@login_required
def marketplace(request):
    tasks_marketplace= Task.objects.filter(status="marketplace")
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = "marketplace"
            task.assigned_by = request.user
            task.assigned_to = request.user
            task.save()
            return redirect("marketplace")  # Refresh the page after adding
        else:
            print(form.errors)
    else:
        form = TaskForm()
    return render(request, "marketplace.html", {"form": form,"tasks_marketplace":tasks_marketplace})
    
@login_required
def takeon(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.assigned_to=request.user
    task.status="pending"
    task.save()
    return redirect("employee_dashboard")


@login_required
def manager_dashboard(request):
    projects = Project.objects.filter(manager=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            return redirect("manager_dashboard")  # Refresh the page after adding
    else:
        form = TaskForm()
    return render(request, "managerdashboard.html", {"projects": projects, "form": form, })

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, manager=request.user)
    tasks = project.tasks.all().order_by("order")
    # Find the next task that should be pending
    for task in tasks:
        if task.status == "completed":
            continue
        elif task.status == "pending":
            task.status = "in_progress"
            task.save()
            break
    return render(request, "projectdetail.html", {"project": project, "tasks": tasks, "progress": project.progress()})

@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.manager = request.user
            project.save()
            return redirect("manager_dashboard")
    else:
        form = ProjectForm()
    return render(request, "createproject.html", {"form": form})

@login_required
def create_projecttask(request, project_id):
    project = get_object_or_404(Project, id=project_id)  # Get the project
    form = TaskForm(request.POST or None)

    if request.method == "POST"and form.is_valid():
        #form = TaskForm(request.POST)
        #if form.is_valid():
        #form.save()
        task = form.save(commit=False)
        task.project = project
        task.assigned_by = request.user  # Set the user who assigned the task
        task.save()
        return redirect("project_detail", project_id=project.id)
    #else:
        #form = TaskForm()        
    return render(request, "createprojecttask.html", {"form": form, "project": project})

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
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Ensure only the assigned user or manager can delete
    if request.user == task.assigned_to or request.user.role == "manager":
        task.delete()
        return redirect("employee_dashboard")  # Redirect after deletion
    else:
        return redirect("task_detail", task_id=task.id)  # Prevent unauthorized deletion

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
        return redirect("employee_dashboard")

def testlist(request):
    return render(request, "tests.html")