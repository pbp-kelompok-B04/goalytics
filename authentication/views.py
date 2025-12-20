from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from users.models import Profile 

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": False, "message": "Invalid method"},
            status=405,
        )

    username = request.POST.get("username")
    password = request.POST.get("password")

    user = authenticate(username=username, password=password)

    if user is not None:
        if user.is_active:
            auth_login(request, user)   # <-- ini yang bikin session + cookie

            return JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!",
            }, status=200)

        return JsonResponse({
            "status": False,
            "message": "Account disabled.",
        }, status=403)

    return JsonResponse({
        "status": False,
        "message": "Invalid username or password.",
    }, status=401)
    
@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data['username']
        password1 = data['password1']
        password2 = data['password2']

        if password1 != password2:
            return JsonResponse({"status": False, "message": "Passwords do not match."}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": False, "message": "Username already exists."}, status=400)

        user = User.objects.create_user(username=username, password=password1)

        Profile.objects.create(user=user)

        return JsonResponse({
            "username": user.username,
            "status": True,
            "message": "User created successfully!"
        }, status=200)

    return JsonResponse({"status": False, "message": "Invalid request method."}, status=400)

@csrf_exempt
def get_user_info(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            "status": False,
            "message": "Not authenticated"
        }, status=401)

    return JsonResponse({
        "status": True,
        "username": request.user.username,
    }, status=200)

@csrf_exempt
def logout(request):
    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logged out successfully!"
        }, status=200)
    except:
        return JsonResponse({
            "status": False,
            "message": "Logout failed."
        }, status=401)