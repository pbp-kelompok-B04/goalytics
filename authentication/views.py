from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
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

@login_required
def get_user_info(request):
    user = request.user  # user yang sedang login (via session)
    
    return JsonResponse({
        "status": True,
        "username": user.username,
    }, status=200)
