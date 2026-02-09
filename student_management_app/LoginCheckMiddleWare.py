from django.http import HttpResponseRedirect
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin

class LoginCheckMiddleWare(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user
        
        # List of URLs that should be accessible without authentication
        open_urls = [
            reverse('show_login'),
            reverse('do_login'),
            '/accounts/password_reset/',
            '/accounts/reset/',
            '/accounts/login/',
            '/accounts/password_reset/done/',
            '/accounts/reset/done/',
        ]

        # Check if current path is in open_urls
        if request.path in open_urls or any(request.path.startswith(url) for url in open_urls):
            return None

        if user.is_authenticated:
            # Handle authenticated users (your existing logic)
            if user.user_type == "1":  # Admin
                if modulename not in ["student_management_app.HodViews", 
                                    "student_management_app.views", 
                                    "django.views.static"]:
                    return HttpResponseRedirect(reverse("admin_home"))
            elif user.user_type == "2":  # Staff
                if modulename not in ["student_management_app.StaffViews", 
                                     "student_management_app.views", 
                                     "django.views.static"]:
                    return HttpResponseRedirect(reverse("staff_home"))
            elif user.user_type == "3":  # Student
                if modulename not in ["student_management_app.StudentViews", 
                                    "student_management_app.views", 
                                    "django.views.static"]:
                    return HttpResponseRedirect(reverse("student_home"))
            elif user.user_type == "4":  # Parent
                if modulename not in ["student_management_app.ParentViews", 
                                    "student_management_app.views", 
                                    "django.views.static"]:
                    return HttpResponseRedirect(reverse("parent_home"))
            else:
                return HttpResponseRedirect(reverse("show_login"))
        else:
            # For unauthenticated users, redirect to login except for open URLs
            return HttpResponseRedirect(reverse("show_login"))