from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Task ,TaskAttachment ,SubTask, ProjectObjective, ProjectStakeholder, ProjectMember, ProjectMilestone
from .forms import  ProjectForm, TaskForm, AssignTaskForm, SubTaskForm, RequestUpdateForm, ProvideUpdateForm 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
#from django.views.generic import DetailView
from django.views import View
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, localtime
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages
from django.db.utils import IntegrityError
from django.http import HttpResponseForbidden

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
    total_tasks = Task.objects.filter(assigned_to=request.user).count()
    pending_tasks = Task.objects.filter(assigned_to=request.user, status="pending").count()
    due_today = Task.objects.filter(assigned_to=request.user, due_date__date=today).count()
    past_due = Task.objects.filter(assigned_to=request.user, due_date__date__lt=today).exclude(status="completed").count()
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = "pending"
            task.assigned_by = request.user
            task.save()

            # Handle attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                TaskAttachment.objects.create(
                    task=task,
                    file=file,
                    uploaded_by=request.user
                )

            # Handle subtasks
            subtasks = request.POST.getlist('subtasks[]')
            for subtask_title in subtasks:
                if subtask_title.strip():  # Only create if not empty
                    SubTask.objects.create(
                        parent_task=task,
                        title=subtask_title.strip()
                    )

            return redirect("employee_dashboard")
    else:
        form = TaskForm()

    return render(request, "dashboard.html", {
        "tasks_pending": tasks_pending,
        "tasks_completed": tasks_completed,
        "tasks_in_progress": tasks_in_progress,
        "tasks_today":tasks_today,
        "tasks_overdue":tasks_overdue,
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "due_today": due_today,
        "past_due": past_due,
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
    tasks_assigned=Task.objects.filter(assigned_by=request.user,project__isnull=True ).exclude(assigned_to=request.user)
    projects = Project.objects.filter(manager=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.status = "pending"
            task.assigned_by = request.user
            task.save()

            # Handle attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                TaskAttachment.objects.create(
                    task=task,
                    file=file,
                    uploaded_by=request.user
                )

            # Handle subtasks
            subtasks = request.POST.getlist('subtasks[]')
            for subtask_title in subtasks:
                if subtask_title.strip():  # Only create if not empty
                    SubTask.objects.create(
                        parent_task=task,
                        title=subtask_title.strip()
                    )
            return redirect("manager_dashboard")

            
    else:
        form = TaskForm()
    return render(request, "projects.html", {"projects": projects, "form": form,"tasks_assigned": tasks_assigned, })

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    objectives = project.project_objectives.all()
    stakeholders = project.project_stakeholders.all()
    tasks = project.tasks.all().order_by("due_date")
    form = TaskForm(request.POST)

    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.status = "pending"
        task.assigned_by = request.user
        task.save()

        # Handle attachments
        files = request.FILES.getlist('attachments')
        for file in files:
            TaskAttachment.objects.create(
                task=task,
                file=file,
                uploaded_by=request.user
            )

        # Handle subtasks
        subtasks = request.POST.getlist('subtasks[]')
        for subtask_title in subtasks:
            if subtask_title.strip():  # Only create if not empty
                SubTask.objects.create(
                    parent_task=task,
                    title=subtask_title.strip()
                )

        return redirect("project_detail", project_id=project.id)
    else:
        print(form.errors)

    return render(request, "projectdetail.html", {
        "project": project,
        "tasks": tasks,
        "progress": project.progress(),
        "form": form
    })

@login_required
def assign_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == "POST":
        # Handle attachment upload
        if "attachment_form" in request.POST:
            files = request.FILES.getlist("attachments")
            for file in files:
                TaskAttachment.objects.create(task=task, file=file, uploaded_by=request.user)
            return redirect('assign_task', task_id=task.id)
            
        # Handle subtask creation
        elif "subtask_form" in request.POST:
            subtasks = request.POST.getlist("subtasks[]")
            for subtask_title in subtasks:
                if subtask_title.strip():
                    SubTask.objects.create(parent_task=task, title=subtask_title.strip())
            return redirect('assign_task', task_id=task.id)
            
        # Handle task reassignment
        elif "reassign_form" in request.POST:
            form = AssignTaskForm(request.POST, instance=task)
            if form.is_valid():
                form.save()
                return redirect('assign_task', task_id=task.id)

        locals()["message"] = "Task successfully updated!"


    form = AssignTaskForm(instance=task)
    return render(request, "assigntask.html", {"form": form, "task": task,})


@login_required
def reassign_task(request, task_id ):
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task.assigned_to = form.cleaned_data["assigned_to"]  # Only update assigned_to
            task.save()
            print(f"Redirecting to project_detail with project_id={task.project.id}")  # Debug print
            return redirect("project_detail" ,project_id=task.project.id)
        else:
            print(form.errors)  # Debug form errors

    else:
        form = TaskForm(instance=task)

    form.fields.pop("title", None)
    form.fields.pop("description", None)
    form.fields.pop("due_date", None)

    return render(request, "assigntask.html", {"form": form, "task": task })

@login_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.manager = request.user
            project.save()

            # Handle objectives
            objectives = request.POST.getlist('objectives[]')
            for objective in objectives:
                if objective.strip():  # Only create if not empty
                    ProjectObjective.objects.create(
                        project=project,
                        description=objective.strip()
                    )

            # Handle stakeholders
            stakeholders = request.POST.getlist('stakeholders[]')
            stakeholder_emails = request.POST.getlist('stakeholder_emails[]')
            
            for name, email in zip(stakeholders, stakeholder_emails):
                if name.strip() and email.strip():  # Only create if both fields are filled
                    ProjectStakeholder.objects.create(
                        project=project,
                        name=name.strip(),
                        email=email.strip()
                    )

            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'createproject.html', {'form': form})

@login_required
def create_project_task(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == "POST":
        milestone_id = request.POST.get('milestone_id')
        
        # Create the task
        task = Task.objects.create(
            project=project,
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            due_date=request.POST.get('due_date'),
            priority=request.POST.get('priority'),
            assigned_by=request.user,
            status='pending'
        )

        # Set milestone if provided
        if milestone_id:
            milestone = get_object_or_404(ProjectMilestone, id=milestone_id)
            task.milestone = milestone
            task.save()

        # Set assigned_to if provided
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            task.assigned_to = get_user_model().objects.get(id=assigned_to_id)
            task.save()

        # Handle attachments
        files = request.FILES.getlist('attachments')
        for file in files:
            TaskAttachment.objects.create(
                task=task,
                file=file,
                uploaded_by=request.user
            )

        # Handle subtasks
        subtasks = request.POST.getlist('subtasks[]')
        for subtask_title in subtasks:
            if subtask_title.strip():
                SubTask.objects.create(
                    parent_task=task,
                    title=subtask_title.strip()
                )

        messages.success(request, 'Task created successfully')
        return redirect('project_details', project_id=project.id)

    return redirect('project_details', project_id=project.id)

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
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Ensure only the assigned user or manager can delete
    if request.user.role == "manager":
        project.delete()
        return redirect("manager_dashboard")  # Redirect after deletion
    else:
        return redirect("manager_dashboard")  # Prevent unauthorized deletion

@login_required
def create_task(request):
    form = TaskForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            #form.save()
            task = form.save(commit=False)
            task.assigned_by = request.user  # Set the user who assigned the task
            task.save()
            return redirect("tasklist")
        else:
            form = TaskForm()        
    return render(request, "createtask.html", {"form": form})


@login_required
def request_update(request, task_id):
    """Manager requests an update from the assigned user."""
    task = get_object_or_404(Task, id=task_id)

    if request.user != task.assigned_by:
        return redirect("employee_dashboard")  # Only the manager can request updates

    task.update_requested = True
    task.save()
    
    return redirect(reverse("taskdetail", kwargs={"task_id": task_id}))



@login_required
def provide_update(request, task_id):
    """User provides an update for the requested task."""
    task = get_object_or_404(Task, id=task_id)

    if request.user != task.assigned_to:
        return redirect("employee_dashboard")  # Only the assigned user can respond

    if request.method == "POST":
        form = ProvideUpdateForm(request.POST, instance=task)
        if form.is_valid():
            task.update_requested = False  # Reset request after response
            form.save()
            return redirect("task_detail", task_id=task_id)
    else:
        form = ProvideUpdateForm(instance=task)

    return render(request, "provide_update.html", {"task": task, "form": form})

def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    assign_form = ProvideUpdateForm(request.POST or None, instance=task)  

    if request.method == "POST" and assign_form.is_valid():
        assign_form.save()
        return redirect("employee_dashboard")  

    return render(request, "task_detail.html", {"task": task, "assign_form": assign_form})
    
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

@login_required
def project_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Calculate project progress
    total_tasks = project.tasks.count()
    completed_tasks = project.tasks.filter(status='completed').count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get all available users except the project manager
    available_users = User.objects.exclude(id=project.manager.id)
    
    context = {
        'project': project,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress': round(progress, 1),
        'available_users': available_users,
    }
    
    return render(request, 'project_details.html', context)

@login_required
def update_project_milestones(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.manager:
        return HttpResponseForbidden()

    if request.method == "POST":
        milestone_ids = request.POST.getlist('milestone_ids[]')
        milestone_titles = request.POST.getlist('milestone_titles[]')
        milestone_dates = request.POST.getlist('milestone_dates[]')
        milestone_descriptions = request.POST.getlist('milestone_descriptions[]')
        milestone_statuses = request.POST.getlist('milestone_status[]')

        # Remove deleted milestones
        project.project_milestones.exclude(id__in=[id for id in milestone_ids if id]).delete()

        # Update or create milestones
        for i, title in enumerate(milestone_titles):
            if not title.strip():  # Skip empty titles
                continue

            try:
                # Convert string to date object
                due_date = datetime.strptime(milestone_dates[i], '%Y-%m-%d').date()
                
                # Compare dates (now all are date objects)
                if due_date < project.start_date.date() or due_date > project.due_date.date():
                    messages.error(request, f'Milestone "{title}" due date must be between project start and end dates')
                    continue

                if milestone_ids[i]:  # Existing milestone
                    milestone = project.project_milestones.get(id=milestone_ids[i])
                    milestone.title = title
                    milestone.due_date = due_date
                    milestone.description = milestone_descriptions[i]
                    milestone.completed = milestone_statuses[i] == 'completed'
                    milestone.save()
                else:  # New milestone
                    ProjectMilestone.objects.create(
                        project=project,
                        title=title,
                        due_date=due_date,
                        description=milestone_descriptions[i],
                        completed=milestone_statuses[i] == 'completed'
                    )
            except ValueError as e:
                messages.error(request, f'Invalid date format for milestone "{title}"')
                continue

        messages.success(request, 'Milestones updated successfully')
        return redirect('project_details', project_id=project.id)

    return redirect('project_details', project_id=project.id)

@login_required
def update_project_members(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.manager:
        return HttpResponseForbidden()

    if request.method == "POST":
        member_ids = request.POST.getlist('member_ids[]')
        member_roles = request.POST.getlist('member_roles[]')

        # Remove all current members
        project.project_members.all().delete()

        # Add new/updated members
        for user_id, role in zip(member_ids, member_roles):
            if user_id:
                try:
                    ProjectMember.objects.create(
                        project=project,
                        user_id=user_id,
                        role=role
                    )
                except IntegrityError:
                    messages.error(request, f'User is already a member of the project')
                    continue

        messages.success(request, 'Team members updated successfully')
        return redirect('project_details', project_id=project.id)

    return redirect('project_details', project_id=project.id)

@login_required
def update_project_status(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.manager:
        return redirect('project_details', project_id=project_id)

    if request.method == "POST":
        project.status = request.POST.get('status')
        project.priority = request.POST.get('priority')
        project.save()

    return redirect('project_details', project_id=project_id)