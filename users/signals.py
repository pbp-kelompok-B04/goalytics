from django.contrib.auth.models import User
from django.db import OperationalError, ProgrammingError
from .models import Profile, ADMIN_USERNAMES


def create_default_admins(sender, **kwargs):
    try:
        for username in ADMIN_USERNAMES:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password="project-admin"
                )
                Profile.objects.create(user=user, role='admin')
                print(f"Created admin user: {username}")
    except (OperationalError, ProgrammingError):
        # Happens before first migration — safe to ignore
        pass
