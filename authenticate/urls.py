from django.urls import path
from .views import register_user, login_user, logout_user
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/",  auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", logout_user, name="logout"),
]
    #path("login/", login_user, name="login"),
    #path("logout/",logout_user, name="logout"),
#auth_views.LogoutView.as_view()