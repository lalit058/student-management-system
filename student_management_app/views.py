from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from student_management_app.models import CustomUser, Courses, SessionYearModel, Students, Staffs, Parents, AdminHOD
from student_management_system import settings
from django.http import JsonResponse
import re
from django.db.models import Q

def showDemoPage(request):
    return render(request,"demo.html")

def ShowLoginPage(request):
    return render(request,"login_page.html")

def doLogin(request):
    if request.method != "POST":
        return render(request, "login.html")
    
    username = request.POST.get("email")
    password = request.POST.get("password")

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        if user.user_type == "1":
            return HttpResponseRedirect(reverse("admin_home"))
        elif user.user_type == "2":
            return HttpResponseRedirect(reverse("staff_home"))
        elif user.user_type == "3":
            return HttpResponseRedirect(reverse("student_home"))
        elif user.user_type == "4":
            return HttpResponseRedirect(reverse("parent_home"))
        else:
            messages.error(request, "Invalid user type.")
            return HttpResponseRedirect("/")
    else:
        messages.error(request, "Invalid login details.")
        return HttpResponseRedirect("/")

def GetUserDetails(request):
    if request.user!=None:
        return HttpResponse("User : "+request.user.email+" usertype : "+str(request.user.user_type))
    else:
        return HttpResponse("Please Login First")

def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")

def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/7.14.6/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "YOUR_API_KEY",' \
         '        authDomain: "FIREBASE_AUTH_URL",' \
         '        databaseURL: "FIREBASE_DATABASE_URL",' \
         '        projectId: "FIREBASE_PROJECT_ID",' \
         '        storageBucket: "FIREBASE_STORAGE_BUCKET_URL",' \
         '        messagingSenderId: "FIREBASE_SENDER_ID",' \
         '        appId: "FIREBASE_APP_ID",' \
         '        measurementId: "FIREBASE_MEASUREMENT_ID"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'
    return HttpResponse(data,content_type="text/javascript")

def Testurl(request):
    return HttpResponse("Ok")

def signup_admin(request):
    return render(request,"signup_admin_page.html")

def signup_student(request):
    courses=Courses.objects.all()
    session_years=SessionYearModel.objects.all()
    return render(request,"signup_student_page.html",{"courses":courses,"session_years":session_years})

def signup_staff(request):
    return render(request,"signup_staff_page.html")

def do_admin_signup(request):
    username=request.POST.get("username")
    email=request.POST.get("email")
    password=request.POST.get("password")

    try:
        user=CustomUser.objects.create_user(username=username,password=password,email=email,user_type=1)
        user.save()
        messages.success(request,"Successfully Created Admin")
        return HttpResponseRedirect(reverse("show_login"))
    except:
        messages.error(request,"Failed to Create Admin")
        return HttpResponseRedirect(reverse("show_login"))

def do_staff_signup(request):
    username=request.POST.get("username")
    email=request.POST.get("email")
    password=request.POST.get("password")
    address=request.POST.get("address")

    try:
        user=CustomUser.objects.create_user(username=username,password=password,email=email,user_type=2)
        user.staffs.address=address
        user.save()
        messages.success(request,"Successfully Created Staff")
        return HttpResponseRedirect(reverse("show_login"))
    except:
        messages.error(request,"Failed to Create Staff")
        return HttpResponseRedirect(reverse("show_login"))

def do_signup_student(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("signup_student"))
    
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")
    address = request.POST.get("address")
    session_year_id = request.POST.get("session_year")
    course_id = request.POST.get("course")
    gender = request.POST.get("sex")

    try:
        # Handle file upload
        profile_pic = request.FILES.get('profile_pic')
        if not profile_pic:
            raise ValueError("Profile picture is required")

        # Create user first
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            email=email,
            last_name=last_name,
            first_name=first_name,
            user_type=3
        )

        # Get related objects
        course_obj = Courses.objects.get(id=course_id)
        session_year = SessionYearModel.objects.get(id=session_year_id)

        # Create student with the profile pic
        Students.objects.create(
            admin=user,
            address=address,
            course_id=course_obj,
            session_year_id=session_year,
            gender=gender,
            profile_pic=profile_pic  # Store the file directly
        )

        messages.success(request, "Successfully Added Student")
        return HttpResponseRedirect(reverse("show_login"))

    except Exception as e:
        messages.error(request, f"Failed to Add Student: {str(e)}")
        return HttpResponseRedirect(reverse("signup_student"))

def check_username(request):
    username = request.POST.get('username', '') or request.GET.get('username', '')
    username_taken = (
        CustomUser.objects.filter(username__iexact=username).exists() or
        Students.objects.filter(admin__username__iexact=username).exists() or
        Staffs.objects.filter(admin__username__iexact=username).exists() or
        Parents.objects.filter(admin__username__iexact=username).exists() or
        AdminHOD.objects.filter(admin__username__iexact=username).exists()
    )
    data = {
        'valid': bool(re.match(r'^[a-zA-Z0-9_]{4,20}$', username)),
        'is_taken': username_taken
    }
    return JsonResponse(data)


def check_phone(request):
    if request.method in ['POST', 'GET']:
        phone = request.POST.get('phone_number', '') or request.GET.get('phone_number', '')
        
        # Basic format validation
        is_valid_format = bool(re.match(r'^[0-9]{10}$', phone))
        
        # Check if phone exists in database (only if format is valid)
        is_taken = False
        if is_valid_format:
            try:
                from student_management_app.models import Students, Staffs, Parents
                is_taken = (
                    Students.objects.filter(phone_number=phone).exists() or
                    Staffs.objects.filter(phone_number=phone).exists() or
                    Parents.objects.filter(phone_number=phone).exists()
                )
            except Exception as e:
                return JsonResponse({
                    'is_taken': True,
                    'is_valid': False,
                    'message': 'Error checking phone number'
                }, status=500)
        
        return JsonResponse({
            'is_valid': is_valid_format,
            'is_taken': is_taken,
            'message': (
                "✓ Phone available" if is_valid_format and not is_taken else
                "✗ Phone already registered" if is_taken else
                "✗ Phone must be 10 digits"
            )
        })
    
    return JsonResponse({
        'is_valid': False,
        'is_taken': True,
        'message': 'Invalid request method'
    }, status=400)


def check_email(request):
    email = request.POST.get('email', '') or request.GET.get('email', '')
    email_taken = (
        CustomUser.objects.filter(email__iexact=email).exists() or
        Students.objects.filter(admin__email__iexact=email).exists() or
        Staffs.objects.filter(admin__email__iexact=email).exists() or
        Parents.objects.filter(admin__email__iexact=email).exists() or
        AdminHOD.objects.filter(admin__email__iexact=email).exists()
    )
    data = {
        'valid': bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email)),
        'is_taken': email_taken
    }
    return JsonResponse(data)

def validate_password(request):
    password = request.POST.get('password', '')
    data = {
        'length': len(password) >= 8,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'number': bool(re.search(r'[0-9]', password)),
        'special': bool(re.search(r'[@$!%*?&]', password)),
        'valid': bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))
    }
    return JsonResponse(data)

def check_parent_username(request):
    return check_username(request)

def check_parent_email(request):
    return check_email(request)

def check_parent_phone(request):
    phone = request.GET.get('phone_number', '')
    data = check_phone(phone)
    return JsonResponse(data)

def check_staff_username(request):
    return check_username(request)

def check_staff_email(request):
    return check_email(request)

def check_staff_phone(request):
    phone = request.GET.get('phone_number', '')
    data = check_phone(phone)
    return JsonResponse(data)