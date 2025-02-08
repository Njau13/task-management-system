from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import task_list, create_task, testlist, manager_list
from .views import TaskDetailView

urlpatterns = [
    path("tasks/", login_required(task_list), name="tasklist"),
     path("manager/", login_required(manager_list), name="managerlist"),
    path("tasks/create/", login_required(create_task), name="createtask"),
    path("task/<int:pk>/", TaskDetailView.as_view(), name="taskdetail"),
    path("tests/", testlist, name="testlist"),
]
