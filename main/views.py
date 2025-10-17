from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            return redirect('main:dashboard')
        else:
            return redirect('users:login')

    return render(request, 'home.html')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, 'dashboard.html', context)
