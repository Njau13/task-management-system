from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import task_list, create_task, testlist, manager_list,manager_dashboard,delete_project, takeon,assign_task, marketplace, delete_task, create_project, project_detail, create_projecttask, employee_dashboard
from .views import TaskDetailView 

urlpatterns = [
    path("tasks/", login_required(task_list), name="tasklist"),
    path("tasks/create/", login_required(create_task), name="createtask"),
    path("task/<int:pk>/", TaskDetailView.as_view(), name="taskdetail"),
    path("tests/", testlist, name="testlist"),
    path("dashboard/", employee_dashboard, name="employee_dashboard"),
    path("manager/", manager_list, name="managerlist"),
    path("managerboard/", manager_dashboard, name="manager_dashboard"),
    path("manager/project/<int:project_id>/", project_detail, name="project_detail"),
    path("manager/project/new/", create_project, name="create_project"),
    path("manager/project/<int:project_id>/assign-task/", create_projecttask, name="create_projecttask"),
    path("task/delete/<int:task_id>/", delete_task, name="delete_task"),
    path("project/delete/<int:project_id>/", delete_project, name="delete_project"),
    path("marketplace/", marketplace, name= "marketplace"),
    path("task/takeon/<int:task_id>/", takeon, name="takeon"),
    path("assigntask/<int:task_id>/", assign_task, name="assigntask"),
]
