import os
from django.apps import AppConfig  # pyright: ignore[reportMissingImports]
from django.contrib.auth import get_user_model  # pyright: ignore[reportMissingImports]


class StudentManagementAppConfig(AppConfig):
  default_auto_field = "django.db.models.BigAutoField"
  name = "student_management_app"

  def ready(self):
    if os.environ.get("RUN_MAIN") or os.getenv("RENDER"):
      try:
        User = get_user_model()
        username = "superadmin"
        email = "admin@example.com"
        password = "Password123"

        if not User.objects.filter(username=username).exists():
          User.objects.create_superuser(
              username=username, email=email, password=password
          )
          print(f"--> Superuser '{username}' was successfully created!")
      except Exception:
        pass