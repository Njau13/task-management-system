from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import task_list, create_task, user_projects, task_detail,testlist, manager_list,manager_dashboard,delete_project, takeon,assign_task, marketplace, delete_task, create_project, project_detail, employee_dashboard,request_update, provide_update
from .views import TaskDetailView 
from . import views

urlpatterns = [
    path("tasks/", login_required(task_list), name="tasklist"),
    path("tasks/create/", login_required(create_task), name="createtask"),
    #path("task/<int:pk>/", TaskDetailView.as_view(), name="taskdetail"),
    path("tests/", testlist, name="testlist"),
    path("dashboard/", employee_dashboard, name="employee_dashboard"),
    path("manager/", manager_list, name="managerlist"),
    path("managerboard/", manager_dashboard, name="manager_dashboard"),
    path("manager/project/<int:project_id>/", project_detail, name="project_detail"),
    path("manager/project/new/", create_project, name="create_project"),
    path("my-projects/", user_projects, name="user_projects"),
    #path("manager/project/<int:project_id>/assign-task/", create_projecttask, name="create_projecttask"),
    path("task/delete/<int:task_id>/", delete_task, name="delete_task"),
    path("project/delete/<int:project_id>/", delete_project, name="delete_project"),
    path("marketplace/", marketplace, name= "marketplace"),
    path("task/takeon/<int:task_id>/", takeon, name="takeon"),
    path("assigntask/<int:task_id>/", assign_task, name="assign_task"),
    path('task/<int:task_id>/assign/', views.assign_task, name='assign_task'),
    path('request_update/<int:task_id>/', request_update, name='request_update'),
    path('provide_update/<int:task_id>/', provide_update, name='provide_update'),
    path("task/<int:task_id>/", task_detail, name="taskdetail"),
    path('project/<int:project_id>/details/', views.project_details, name='project_details'),
    path('project/<int:project_id>/update-milestones/', views.update_project_milestones, name='update_project_milestones'),
    path('project/<int:project_id>/update-members/', views.update_project_members, name='update_project_members'),
    path('project/<int:project_id>/update-status/', views.update_project_status, name='update_project_status'),
    path('project/<int:project_id>/create-task/', views.create_project_task, name='create_project_task'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('task/<int:task_id>/submit-review/', views.submit_task_review, name='submit_task_review'),
    path('task/<int:task_id>/review/', views.review_task, name='review_task'),
    path('reports/projects/', views.project_reports, name='project_reports'),
    path('reports/team/', views.team_reports, name='team_reports'),
    path('reports/tasks/', views.task_reports, name='task_reports'),
    path('reports/performance/', views.performance_reports, name='performance_reports'),
    path('reports/export/<str:report_type>/', views.export_report, name='export_report'),
]
