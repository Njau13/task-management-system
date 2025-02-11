from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == "employee":
                return redirect("employee_dashboard")  # Redirect to your dashboard
            elif user.role == "manager":
                return redirect("manager_dashboard")
            else:
                return redirect("login")
        else:
            return render(request, "login.html", {"error": "Invalid username or password"})
    return render(request, "login.html")

def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            #login(request, user)  # Auto login after registration
            return redirect("login") 
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def logout_user(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
   return render(request, "tasklist")