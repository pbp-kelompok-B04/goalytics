from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile

def login_user(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Django otomatis buat session ID + cookie
            messages.success(request, f"Welcome back, {username}!")
            return redirect('main:dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')

def register_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('users:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('users:register')

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user)

        messages.success(request, "Registration successful. Please log in.")
        return redirect('users:login')

    return render(request, 'register.html')

def logout_user(request):
    logout(request)  # hapus session dan cookie
    messages.info(request, "You have been logged out.")
    return redirect('main:home')

@login_required
def profile_view(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'user': request.user,
        'profile': profile,
        'form': form,
    }
    return render(request, 'profile.html', context)