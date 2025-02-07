from django.urls import path
from .views import task_list, create_task

urlpatterns = [
    path("tasks/", task_list, name="tasklist"),
    path("tasks/create/", create_task, name="createtask"),
]
