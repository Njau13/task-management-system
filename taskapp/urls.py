from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import task_list, create_task, testlist, manager_list,manager_dashboard, create_project, project_detail, create_projecttask
from .views import TaskDetailView

urlpatterns = [
    path("tasks/", login_required(task_list), name="tasklist"),
    path("tasks/create/", login_required(create_task), name="createtask"),
    path("task/<int:pk>/", TaskDetailView.as_view(), name="taskdetail"),
    path("tests/", testlist, name="testlist"),
    path("manager/", manager_list, name="managerlist"),
    path("managerboard/", manager_dashboard, name="manager_dashboard"),
    path("manager/project/<int:project_id>/", project_detail, name="project_detail"),
    path("manager/project/new/", create_project, name="create_project"),
    path("manager/project/<int:project_id>/assign-task/", create_projecttask, name="create_projecttask"),
]
