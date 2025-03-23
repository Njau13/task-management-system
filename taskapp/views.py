from django.shortcuts import render, redirect, get_object_or_404
from .models import Project, Task ,TaskAttachment ,SubTask, ProjectObjective, ProjectStakeholder, ProjectMember, ProjectMilestone, Notification, TaskReview
from .forms import  ProjectForm, TaskForm, AssignTaskForm, TaskUpdateForm, SubTaskForm, RequestUpdateForm, ProvideUpdateForm, TaskReviewForm, TaskReviewResponseForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
#from django.views.generic import DetailView
from django.views import View
from django.db.models import Q, Count, Avg, F, ExpressionWrapper, fields, DurationField
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, localtime
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages
from django.db.utils import IntegrityError
from django.http import HttpResponseForbidden
from .utils import create_notification
from django.utils import timezone
from django.db.models.functions import ExtractDay
import json


User = get_user_model()

@login_required
def employee_dashboard(request):
    tasks_pending = Task.objects.filter(assigned_to=request.user, status="pending")
    tasks_completed = Task.objects.filter(assigned_to=request.user, status="completed")
    tasks_in_progress = Task.objects.filter(assigned_to=request.user, status="in_progress")
    today = localtime().date()
    tasks_review = Task.objects.filter(assigned_to=request.user, status="under_review")
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
        "tasks_review":tasks_review,
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
    tasks_assigned=Task.objects.filter(assigned_by=request.user,project__isnull=True, status__in=["pending", "in_progress"] ).exclude(assigned_to=request.user)
    tasks_review=Task.objects.filter(assigned_by=request.user,status__in=["submitforreview", "under_review"]).exclude(assigned_to=request.user)
    projects = Project.objects.filter(manager=request.user)

    for project in projects:
            project.total_tasks = project.tasks.count()
            project.completed_tasks = project.tasks.filter(status='completed').count()
            project.progress = (project.completed_tasks / project.total_tasks * 100) if project.total_tasks > 0 else 0
    
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
    return render(request, "projects.html", {"projects": projects, "form": form,"tasks_assigned": tasks_assigned,"tasks_review":tasks_review })

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    objectives = project.project_objectives.all()
    stakeholders = project.project_stakeholders.all()
    tasks = project.tasks.all().order_by("due_date")
    overdue = localtime().date()
    tasks_overdue= project.tasks.filter(due_date__date__lt=overdue).exclude(status="completed")
    form = TaskForm(request.POST)
    project_members = project.project_members.exclude(role="observer")

    project.is_leader = project.project_members.filter(user=request.user, role='leader').exists()

        # Calculate project progress
    total_tasks = project.tasks.count()
    completed_tasks = project.tasks.filter(status='completed').count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0


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
        form = TaskForm()
        

    return render(request, "projectdetail.html", {
        "project": project,
        "tasks": tasks,
        "progress": progress,
        "form": form,
        "tasks_overdue":tasks_overdue,
        "project_members":project_members
    })

@login_required
def user_projects(request):
    project_memberships = ProjectMember.objects.filter(user=request.user)
    projects = [membership.project for membership in project_memberships]  # Extract projects
    return render(request, "memberproject.html", {"projects": projects})

@login_required
def assign_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    review_response_form = TaskReviewResponseForm()
    

    if request.method == "POST":
        if "reassign_form" in request.POST:
            form = AssignTaskForm(request.POST, instance=task)
            task.status="pending"
            if form.is_valid():
                # Reset update-related fields
                task.update_requested = False  # Clear update request
                task.update_response = None  # Remove previous responses
                task = form.save()

                # Create notification for the newly assigned user
                create_notification(
                    user=task.assigned_to,
                    notification_type='task_assigned',
                    title='New Task Assignment',
                    message=f'You have been assigned the task: {task.title}',
                    project=task.project,
                    task=task
                )
                return redirect('assign_task', task_id=task.id)
            
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

        locals()["message"] = "Task successfully updated!"


    form = AssignTaskForm(instance=task)
    return render(request, "assigntask.html", {"form": form, "task": task, "review_response_form":review_response_form})


@login_required
def reassign_task(request, task_id ):
    task = get_object_or_404(Task, id=task_id)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)  # Don't save yet
            task.assigned_to = form.cleaned_data["assigned_to"]
            task.status = "pending"
            task.save()  # Now save changes
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
    
    # Check if user is manager or team leader
    is_authorized = (project.manager == request.user or project.project_members.filter(user=request.user, role='leader').exists())
    
    if not is_authorized:
        messages.error(request, "You don't have permission to create tasks.")
        return redirect('project_details', project_id=project.id)

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


    task.update_requested = True
    task.update_response = None

    task.save()
    
    create_notification(
        user=task.assigned_to,
        notification_type='update_requested',
        title='Update Requested',
        message=f'An update has been requested for task: {task.title}',
        project=task.project,
        task=task
    )
    
    return redirect(reverse("assign_task", kwargs={"task_id": task_id}))



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
            return redirect("taskdetail", task_id=task_id)
    else:
        form = ProvideUpdateForm(instance=task)
        

    return render(request, "taskdetail.html", {"task": task, "form": form})

def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Load forms
    assign_form = ProvideUpdateForm(request.POST or None, instance=task)
    review_form = TaskReviewForm()
    review_response_form = TaskReviewResponseForm()

    if request.method == "POST":
        # Check if updating the response field
        if 'status' in request.POST or 'update_response' in request.POST:
            if assign_form.is_valid():
                assign_form.save()
                task.update_requested = False

                create_notification(
                    user=task.assigned_by,
                    notification_type='update_provided',
                    title='Task Update Provided',
                    message=f"{request.user.get_full_name() or request.user.username} provided an update for task: {task.title}",
                    project=task.project,
                    task=task
                )
                messages.success(request, "Task updated successfully!")
                return redirect(request.path)  # Refresh page
            else:
                print(assign_form.errors)

        # Check if updating a subtask
        subtask_id = request.POST.get("subtask_id")
        if subtask_id:
            subtask = get_object_or_404(SubTask, id=subtask_id)
            subtask.completed = not subtask.completed  # Toggle completion
            subtask.save()
            

    context = {
        'task': task,
        'assign_form': assign_form,
        'review_form': review_form,
        'review_response_form': review_response_form,
    }

    return render(request, 'task_detail.html', context)
   #return render(request, "task_detail.html", {"task": task, "assign_form": assign_form})
    
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

    project_members = project.project_members.exclude(role="observer")
    project.is_leader = project.project_members.filter(user=request.user, role='leader').exists()
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
        'project_members': project_members
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
        for member_id, role in zip(member_ids, member_roles):
            if member_id:
                user = User.objects.get(id=member_id)
                ProjectMember.objects.create(
                    project=project,
                    user=user,
                    role=role
                )
                create_notification(
                    user=user,
                    notification_type='project_invite',
                    title=f'Added to Project: {project.name}',
                    message=f'You have been added as a {role} to the project {project.name}',
                    project=project
                )

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

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))

@login_required
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications')

@login_required
def some_view(request):
    print("Current user:", request.user)
    print("User notifications:", list(request.user.notifications.all()))
    # ... rest of the view code ...

@login_required
def submit_task_review(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == "POST" and request.user == task.assigned_to:
        form = TaskReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.task = task
            review.submitted_by = request.user
            review.save()

            # Update task status
            task.status = 'under_review'
            task.update_requested = False
            task.save()

            # Create notification for task assigner
            create_notification(
                user=task.assigned_by,
                notification_type='review_submitted',
                title='Task Submitted for Review',
                message=f'Task "{task.title}" has been submitted for review',
                task=task
            )

            messages.success(request, 'Task submitted for review successfully')
            return redirect("taskdetail", task_id=task_id)

    return redirect("taskdetail", task_id=task_id)

@login_required
def review_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == "POST" and request.user == task.assigned_by:
        form = TaskReviewResponseForm(request.POST)
        if form.is_valid():
            review = task.reviews.last()
            review.reviewed_by = request.user
            review.reviewed_at = timezone.now()
            review.reviewer_comment = form.cleaned_data['reviewer_comment']
            
            action = request.POST.get('action')
            if action == 'approve':
                review.status = 'approved'
                task.status = 'completed'
                notification_message = f'Task "{task.title}" has been approved and marked as completed'
            else:
                review.status = 'rejected'
                task.status = 'in_progress'
                notification_message = f'Task "{task.title}" needs some changes and has been returned. Comment:"{review.reviewer_comment}"'

            review.save()
            task.update_requested = False
            task.save()
            

            # Create notification for task assignee
            create_notification(
                user=task.assigned_to,
                notification_type='review_response',
                title='Task Review Response',
                message=notification_message,
                task=task
            )

            messages.success(request, 'Review submitted successfully')
        else:
            print(form.errors)  # Debug form errors

    return redirect('assign_task', task_id=task.id)


@login_required
def project_reports(request):
    projects = Project.objects.all()
    
    # Get date range from filters
    date_range = request.GET.get('date_range', '30')
    if date_range == 'custom':
        start_date = request.GET.get('date_from')
        due_date = request.GET.get('date_to')
    else:
        due_date = timezone.now()
        start_date = due_date - timedelta(days=int(date_range))

    # Get projects based on filters
    projects = Project.objects.filter(
        Q(start_date__gte=start_date) | Q(due_date__lte=due_date)
    )
    

    # Calculate statistics
    total_projects = projects.count()
    active_projects = projects.filter(status='in_progress').count()
    completed_projects = projects.filter(status='completed').count()
    overdue_projects = projects.filter(
        due_date__lt=timezone.now(),
        status__in=['in_progress', 'pending']
    ).count()

    # Enhance project data with additional metrics
    for project in projects:
        project.total_tasks = project.tasks.count()
        project.completed_tasks = project.tasks.filter(status='completed').count()
        project.progress = (project.completed_tasks / project.total_tasks * 100) if project.total_tasks > 0 else 0

        project.project_members_count = project.project_members.all().count()  # Store member count in the project object
        

        # Add status color for badges
        project.status_color = {
            'pending': 'warning',
            'in_progress': 'primary',
            'completed': 'success',
            'on_hold': 'secondary',
        }.get(project.status, 'info')

    context = {
        'report_type': 'projects',
        'report_title': 'Project Reports',
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'overdue_projects': overdue_projects,
        'projects': projects,
        
    }

    return render(request, 'reports/projectreports.html', context)

@login_required
def this_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    # Get project tasks with detailed metrics
    tasks = project.tasks.all().order_by("due_date")
    
    # Calculate task statistics
    task_stats = {
        'total': tasks.count(),
        'completed': tasks.filter(status='completed').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'pending': tasks.filter(status='pending').count(),
        'overdue': tasks.filter(due_date__lt=timezone.now()).exclude(status='completed').count()
    }
    
    # Calculate completion rate
    task_stats['completion_rate'] = (task_stats['completed'] / task_stats['total'] * 100) if task_stats['total'] > 0 else 0
    
    for task in tasks:
        # Add status color for badges
        task.status_color = {
            'pending': 'warning',
            'in_progress': 'primary',
            'completed': 'success',
            'under_review': 'secondary',
        }.get(task.status, 'info')

    # Get team members with their task statistics
    team_members = project.project_members.all()
    member_stats = []
    
    for member in team_members:
        member_tasks = tasks.filter(assigned_to=member.user)
        completed_tasks = member_tasks.filter(status='completed')
        
        stats = {
            'member': member,
            'total_tasks': member_tasks.count(),
            'completed_tasks': completed_tasks.count(),
            'completion_rate': (completed_tasks.count() / member_tasks.count() * 100) if member_tasks.count() > 0 else 0,
            'overdue_tasks': member_tasks.filter(due_date__lt=timezone.now()).exclude(status='completed').count()
        }
        member_stats.append(stats)
    
    # Get milestone progress
    milestones = project.project_milestones.all().order_by('due_date')
    
    context = {
        'project': project,
        'task_stats': task_stats,
        'member_stats': member_stats,
        'milestones': milestones,
        'tasks': tasks,
        'report_date': timezone.now()
    }
    
    return render(request, 'reports/thisproject.html', context)


@login_required
def team_reports(request):
    # Get date range from filters
    date_range = request.GET.get('date_range', '30')
    if date_range == 'custom':
        start_date = request.GET.get('date_from')
        due_date = request.GET.get('date_to')
    else:
        due_date = timezone.now()
        start_date = due_date - timedelta(days=int(date_range))

    # Get team members and their metrics
    team_members = User.objects.filter(
        Q(project_members__project__start_date__gte=start_date) |
        Q(project_members__project__due_date__lte=due_date)
    ).distinct()

    member_stats = []
    for member in team_members:
        # Calculate member statistics
        tasks = Task.objects.filter(assigned_to=member)
        completed_tasks = tasks.filter(status='completed')
        
        stats = {
            'user': member,
            'project_count': member.project_members.count(),
            'completed_tasks': completed_tasks.count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'total_tasks': tasks.count(),
            'on_time_tasks': completed_tasks.filter(
                completed_date__lte=F('due_date')
            ).count(),
        }
        
        # Calculate performance metrics
        if stats['total_tasks'] > 0:
            stats['completion_rate'] = (stats['completed_tasks'] / stats['total_tasks']) * 100
            stats['on_time_rate'] = (stats['on_time_tasks'] / stats['completed_tasks']) * 100 if stats['completed_tasks'] > 0 else 0
            stats['performance_score'] = (stats['completion_rate'] + stats['on_time_rate']) / 2
        else:
            stats['completion_rate'] = stats['on_time_rate'] = stats['performance_score'] = 0

        member_stats.append(stats)

    # Calculate overall team metrics
    total_tasks = Task.objects.filter(
        created_at__range=[start_date, due_date]
    ).count()
    
    completed_tasks = Task.objects.filter(
        status='completed',
        completed_date__range=[start_date, due_date]
    ).count()

    context = {
        'report_type': 'team',
        'report_title': 'Team Reports',
        'total_members': team_members.count(),
        'active_members': team_members.filter(is_active=True).count(),
        'avg_tasks_per_member': total_tasks / team_members.count() if team_members.count() > 0 else 0,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'team_members': member_stats,
        'chart_data': get_team_chart_data(team_members, start_date, due_date),
    }

    return render(request, 'reports/team_reports.html', context)

@login_required
def task_reports(request):
    # Get date range from filters
    date_range = request.GET.get('date_range', '30')
    if date_range == 'custom':
        start_date = request.GET.get('date_from')
        end_date = request.GET.get('date_to')
    else:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=int(date_range))

    # Get tasks within date range
    tasks = Task.objects.filter(
        created_at__range=[start_date, end_date]
    )

    # Calculate completion time for completed tasks
    completion_time = tasks.filter(status='completed').annotate(
        duration=ExpressionWrapper(
            F('completed_date') - F('created_at'),
            output_field=DurationField()
        )
    ).aggregate(avg_days=Avg(ExtractDay('duration')))

    context = {
        'report_type': 'tasks',
        'report_title': 'Task Reports',
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'overdue_tasks': tasks.filter(
            due_date__lt=timezone.now(),
            status__in=['pending', 'in_progress']
        ).count(),
        'avg_completion_time': completion_time['avg_days'] or 0,
        'tasks': tasks,
        'chart_data': get_task_chart_data(tasks),
    }

    return render(request, 'reports/task_reports.html', context)

@login_required
def performance_reports(request):
    # Get date range from filters
    date_range = request.GET.get('date_range', '30')
    if date_range == 'custom':
        start_date = request.GET.get('date_from')
        end_date = request.GET.get('date_to')
    else:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=int(date_range))

    # Get team members and calculate performance metrics
    team_members = User.objects.filter(is_active=True)
    performance_data = []

    for member in team_members:
        tasks = Task.objects.filter(
            assigned_to=member,
            created_at__range=[start_date, end_date]
        )
        completed_tasks = tasks.filter(status='completed')
        
        # Calculate various performance metrics
        data = {
            'name': member.get_full_name() or member.username,
            'tasks_completed': completed_tasks.count(),
            'total_tasks': tasks.count(),
            'on_time_tasks': completed_tasks.filter(
                completed_date__lte=F('due_date')
            ).count(),
        }
        
        # Calculate rates and scores
        if data['total_tasks'] > 0:
            data['completion_rate'] = (data['tasks_completed'] / data['total_tasks']) * 100
            data['on_time_rate'] = (data['on_time_tasks'] / data['tasks_completed'] * 100) if data['tasks_completed'] > 0 else 0
            
            # Quality score based on task reviews
            reviews = TaskReview.objects.filter(
                task__assigned_to=member,
                status='approved',
                submitted_at__range=[start_date, end_date]
            )
            data['quality_score'] = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            
            # Calculate efficiency score
            avg_completion_time = tasks.filter(status='completed').annotate(
                duration=ExpressionWrapper(
                    F('completed_date') - F('created_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg_days=Avg(ExtractDay('duration')))
            data['efficiency_score'] = 100 - (avg_completion_time['avg_days'] or 0) * 5  # Adjust formula as needed
            
            # Overall rating
            data['overall_rating'] = (
                data['completion_rate'] * 0.3 +
                data['on_time_rate'] * 0.3 +
                data['quality_score'] * 0.2 +
                data['efficiency_score'] * 0.2
            )
        else:
            data['completion_rate'] = data['on_time_rate'] = data['quality_score'] = \
            data['efficiency_score'] = data['overall_rating'] = 0

        performance_data.append(data)

    context = {
        'report_type': 'performance',
        "TaskReview": TaskReview,
        'report_title': 'Performance Reports',
        'performance_data': performance_data,
        'avg_task_completion_rate': sum(d['completion_rate'] for d in performance_data) / len(performance_data) if performance_data else 0,
        'avg_on_time_completion': sum(d['on_time_rate'] for d in performance_data) / len(performance_data) if performance_data else 0,
        'avg_task_quality': sum(d['quality_score'] for d in performance_data) / len(performance_data) if performance_data else 0,
        'productivity_score': sum(d['overall_rating'] for d in performance_data) / len(performance_data) if performance_data else 0,
        'chart_data': get_performance_chart_data(performance_data, start_date, end_date),
    }

    return render(request, 'reports/performance_reports.html', context)

# Helper functions for chart data
def get_team_chart_data(team_members, start_date, end_date):
    # Project distribution data
    project_data = ProjectMember.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')

    # Workload distribution data
    workload_data = []
    for member in team_members:
        workload_data.append({
            'name': member.get_full_name() or member.username,
            'tasks': Task.objects.filter(assigned_to=member).count()
        })

    return {
        'project_distribution': list(project_data),
        'workload_distribution': workload_data
    }

def get_task_chart_data(tasks):
    # Status distribution
    status_data = tasks.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    # Priority distribution
    priority_data = tasks.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')

    return {
        'status_distribution': list(status_data),
        'priority_distribution': list(priority_data)
    }

def get_performance_chart_data(performance_data, start_date, end_date):
    # Performance trends over time
    trend_data = []
    current_date = start_date
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        daily_stats = {
            'date': current_date.strftime('%Y-%m-%d'),
            'completion_rate': Task.objects.filter(
                completed_date__date=current_date,
                status='completed'
            ).count(),
        }
        trend_data.append(daily_stats)
        current_date = next_date

    # Workload vs Performance correlation
    workload_performance = [{
        'name': data['name'],
        'workload': data['total_tasks'],
        'performance': data['overall_rating']
    } for data in performance_data]

    return {
        'trend_data': trend_data,
        'workload_performance': workload_performance
    }

def export_report(request, report_type):
    """Handle report export to Excel/PDF"""
    pass