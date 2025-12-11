from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from users.models import Profile 

@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            # Login status successful.
            return JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!"
                # Add other data if you want to send data to Flutter.
            }, status=200)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login failed, account is disabled."
            }, status=401)

    else:
        return JsonResponse({
            "status": False,
            "message": "Login failed, please check your username or password."
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