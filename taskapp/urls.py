from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import task_list, create_task

urlpatterns = [
    path("tasks/", login_required(task_list), name="tasklist"),
    path("tasks/create/", login_required(create_task), name="createtask"),
]
