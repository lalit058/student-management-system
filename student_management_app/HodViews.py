import datetime
import json
import os
from .models import CustomUser
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import JsonResponse
from django.db import transaction, IntegrityError
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import requests
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist   
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import transaction, IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Notification

from student_management_app.forms import (
    AddStudentForm,
    AddParentForm,
    EditStudentForm,
    CustomStaffCreationForm,
)
from student_management_app.models import (
    CustomUser,
    AdminHOD,
    Staffs,
    Courses,
    Subjects,
    Students,
    Parents,
    SessionYearModel,
    FeedBackStudent,
    StudentResult,
    FeedBackParents,
    FeedBackStaffs,
    LeaveReportStudent,
    LeaveReportStaff,
    Attendance,
    AttendanceReport,
    NotificationStudent,
    NotificationStaffs,
    NotificationParents,
)

import logging

logger = logging.getLogger(__name__)


def admin_home(request):
    student_count1 = Students.objects.all().count()
    staff_count = Staffs.objects.all().count()
    subject_count = Subjects.objects.all().count()
    course_count = Courses.objects.all().count()

    course_all = Courses.objects.all()
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []
    for course in course_all:
        subjects = Subjects.objects.filter(course_id=course.id).count()
        students = Students.objects.filter(course_id=course.id).count()
        course_name_list.append(course.course_name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)

    subjects_all = Subjects.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    for subject in subjects_all:
        course = Courses.objects.get(id=subject.course_id.id)
        student_count = Students.objects.filter(course_id=course.id).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_count)

    staffs = Staffs.objects.all()
    attendance_present_list_staff = []
    attendance_absent_list_staff = []
    staff_name_list = []
    for staff in staffs:
        subject_ids = Subjects.objects.filter(staff_id=staff.admin.id)
        attendance = Attendance.objects.filter(subject_id__in=subject_ids).count()
        leaves = LeaveReportStaff.objects.filter(
            staff_id=staff.id, leave_status=1
        ).count()
        attendance_present_list_staff.append(attendance)
        attendance_absent_list_staff.append(leaves)
        staff_name_list.append(staff.admin.username)

    students_all = Students.objects.all()
    attendance_present_list_student = []
    attendance_absent_list_student = []
    student_name_list = []
    for student in students_all:
        attendance = AttendanceReport.objects.filter(
            student_id=student.id, status=True
        ).count()
        absent = AttendanceReport.objects.filter(
            student_id=student.id, status=False
        ).count()
        leaves = LeaveReportStudent.objects.filter(
            student_id=student.id, leave_status=1
        ).count()
        attendance_present_list_student.append(attendance)
        attendance_absent_list_student.append(leaves + absent)
        student_name_list.append(student.admin.username)

    return render(
        request,
        "hod_template/home_content.html",
        {
            "student_count": student_count1,
            "staff_count": staff_count,
            "subject_count": subject_count,
            "course_count": course_count,
            "course_name_list": course_name_list,
            "subject_count_list": subject_count_list,
            "student_count_list_in_course": student_count_list_in_course,
            "student_count_list_in_subject": student_count_list_in_subject,
            "subject_list": subject_list,
            "staff_name_list": staff_name_list,
            "attendance_present_list_staff": attendance_present_list_staff,
            "attendance_absent_list_staff": attendance_absent_list_staff,
            "student_name_list": student_name_list,
            "attendance_present_list_student": attendance_present_list_student,
            "attendance_absent_list_student": attendance_absent_list_student,
        },
    )


def add_admin(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        address = request.POST.get("address")
        phone_number = request.POST.get("phone_number")
        gender = request.POST.get("gender")
        qualification = request.POST.get("qualification")
        profile_pic = request.FILES.get("profile_pic")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("add_admin")

        try:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                user_type=1,  # 1 for AdminHOD
            )

            if AdminHOD.objects.filter(admin=user).exists():
                messages.error(request, "This user is already an AdminHOD.")
                return redirect("add_admin")

            fs = FileSystemStorage()
            filename = fs.save(profile_pic.name, profile_pic)
            profile_pic_url = fs.url(filename)

            admin_hod = AdminHOD.objects.create(
                admin=user,
                address=address,
                phone_number=phone_number,
                gender=gender,
                qualification=qualification,
                profile_pic=profile_pic
            )

            messages.success(request, "Admin added successfully.")
            return redirect("manage_admin")  # Change as per your URL name

        except IntegrityError as e:
            messages.error(request, f"Database Integrity Error: {str(e)}")
            return redirect("add_admin")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("add_admin")

    return render(request, "hod_template/add_admin_template.html")


def manage_admin(request):
    admins = AdminHOD.objects.all().select_related("admin")
    return render(
        request, "hod_template/manage_admin_template.html", {"admins": admins}
    )


@login_required
def admin_profile_view(request, admin_id):
    try:
        admin = AdminHOD.objects.select_related("admin").get(admin_id=admin_id)
        return render(request, "hod_template/admin_profile.html", {"admin": admin})
    except AdminHOD.DoesNotExist:
        messages.error(request, "Admin profile not found")
        return redirect("manage_admin")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("manage_admin")


@login_required
def edit_admin(request, admin_id):
    try:
        admin = AdminHOD.objects.select_related("admin").get(admin_id=admin_id)

        if request.method == "POST":
            # Update User model fields
            admin.admin.email = request.POST.get("email")
            admin.admin.first_name = request.POST.get("first_name")
            admin.admin.last_name = request.POST.get("last_name")
            admin.admin.username = request.POST.get("username")
            admin.admin.save()

            # Update AdminHOD fields
            admin.gender = request.POST.get("gender")
            admin.qualification = request.POST.get("qualification")
            admin.address = request.POST.get("address")
            admin.phone_number = request.POST.get("phone_number")

            # Handle file upload
            if "profile_pic" in request.FILES:
                admin.profile_pic = request.FILES["profile_pic"]

            admin.save()

            messages.success(request, "Admin updated successfully")
            return redirect("admin_profile_view", admin_id=admin.admin.id)

        return render(
            request, "hod_template/edit_admin_template.html", {"admin": admin}
        )

    except Exception as e:
        messages.error(request, f"Error updating admin: {str(e)}")
        return redirect("manage_admin")


def delete_admin(request, admin_id):
    try:
        admin = AdminHOD.objects.get(admin_id=admin_id)
        user = admin.admin  # Get the associated user

        # Delete the AdminHOD record first
        admin.delete()

        # Then delete the user
        user.delete()

        messages.success(request, "Admin deleted successfully")
        return redirect("manage_admin")

    except AdminHOD.DoesNotExist:
        messages.error(request, "Admin not found")
        return redirect("manage_admin")
    except Exception as e:
        messages.error(request, f"Error deleting admin: {str(e)}")
        return redirect("manage_admin")


def add_staff(request):
    return render(request, "hod_template/add_staff_template.html")


def add_staff_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed", status=405)

    form = CustomStaffCreationForm(request.POST, request.FILES)

    if form.is_valid():
        try:
            with transaction.atomic():
                # Case-insensitive checks
                username = form.cleaned_data["username"].lower()
                email = form.cleaned_data["email"].lower()
                gender = request.POST.get("gender")  # Get gender from form

                if CustomUser.objects.filter(username__iexact=username).exists():
                    messages.error(request, "Username already exists")
                    return redirect("add_staff")

                if CustomUser.objects.filter(email__iexact=email).exists():
                    messages.error(request, "Email already exists")
                    return redirect("add_staff")

                # Handle profile picture first
                profile_pic_url = None
                if "profile_pic" in request.FILES:
                    fs = FileSystemStorage()
                    filename = fs.save(
                        f"staff_profile_pics/user_{username}_{request.FILES['profile_pic'].name}",
                        request.FILES["profile_pic"],
                    )
                    profile_pic_url = fs.url(filename)

                # Create user
                user = CustomUser.objects.create_user(
                    username=username,
                    password=form.cleaned_data["password"],
                    email=email,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    user_type=2,  # Staff type
                )

                # Get or create staff record
                staff, created = Staffs.objects.get_or_create(admin=user)
                staff.address = form.cleaned_data["address"]
                staff.qualification = form.cleaned_data["qualification"]
                staff.years_of_experience = form.cleaned_data["years_of_experience"]
                staff.joining_date = form.cleaned_data["joining_date"]
                staff.phone_number = form.cleaned_data["phone_number"]
                staff.gender = gender  # Add gender field
                if profile_pic_url:
                    staff.profile_pic = profile_pic_url
                staff.save()

                messages.success(request, "Staff created successfully!")
                return redirect("manage_staff")

        except IntegrityError as e:
            messages.error(request, "Database error occurred while creating staff")
            logger.error(f"IntegrityError in staff creation: {str(e)}")
            return redirect("add_staff")

        except Exception as e:
            messages.error(request, f"Error creating staff: {str(e)}")
            logger.error(f"Staff creation failed: {str(e)}")
            return redirect("add_staff")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field.title().replace('_', ' ')}: {error}")
        return redirect("add_staff")


def course_students_pdf(request, course_id):
    try:
        course = Courses.objects.get(id=course_id)
        students = Students.objects.filter(course_id=course_id).select_related(
            "admin", "course_id", "session_year_id"
        )

        context = {
            "students": students,
            "course_filter": course,
            "preview": "download"
            not in request.GET,  # Show preview unless download param exists
        }

        template = get_template("hod_template/print_student_records.html")
        html = template.render(context)

        if "download" not in request.GET:
            return HttpResponse(html)  # Return HTML for preview

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            'attachment; filename="students_{}.pdf"'.format(course.course_name)
        )

        # Create PDF
        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse("Error generating PDF: {}".format(pisa_status.err))
        return response

    except Exception as e:
        return HttpResponse("Error: {}".format(str(e)), status=500)


def secure_link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths safely
    """
    # Handle duplicate media paths
    if uri.startswith(settings.MEDIA_URL):
        # Remove any duplicate media segments
        clean_uri = uri.replace(settings.MEDIA_URL, "", 1)
        path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, clean_uri))
    elif uri.startswith(settings.STATIC_URL):
        clean_uri = uri.replace(settings.STATIC_URL, "", 1)
        path = os.path.normpath(os.path.join(settings.STATIC_ROOT, clean_uri))
    else:
        return uri  # handle absolute URIs

    # Security checks
    if settings.MEDIA_ROOT and not os.path.abspath(path).startswith(
        os.path.abspath(settings.MEDIA_ROOT)
    ):
        raise Exception(f"Security violation: Attempted to access {path}")
    if settings.STATIC_ROOT and not os.path.abspath(path).startswith(
        os.path.abspath(settings.STATIC_ROOT)
    ):
        raise Exception(f"Security violation: Attempted to access {path}")

    # Check if file exists
    if not os.path.isfile(path):
        # Try alternative paths for profile pictures
        if "profile_pic" in uri:
            default_path = os.path.join(
                settings.STATIC_ROOT, "img", "default_profile.png"
            )
            if os.path.isfile(default_path):
                return default_path
        raise Exception(f"File not found: {path}")

    return path


def staff_profile_view(request, staff_id):
    try:
        staff = Staffs.objects.get(admin=staff_id)
        context = {
            "staff": staff,
            "page_title": f"Staff Profile - {staff.admin.get_full_name()}",
        }
        return render(request, "hod_template/staff_profile.html", context)
    except Staffs.DoesNotExist:
        messages.error(request, "Staff member not found")
        return redirect("manage_staff")


def add_course(request):
    sessions = SessionYearModel.objects.all()
    return render(request, 'hod_template/add_course_template.html', {
        'sessions': sessions,
    })

def add_course_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    else:
        course_name = request.POST.get("course").strip()
        session_id = request.POST.get("session")  # Get the selected session ID
        
        try:
            # Check if course already exists (case-insensitive)
            if Courses.objects.filter(course_name__iexact=course_name).exists():
                messages.error(request, f"Course '{course_name}' already exists!")
                return HttpResponseRedirect(reverse("add_course"))
            
            # Get the session instance
            session = SessionYearModel.objects.get(id=session_id)
            
            # Create new course with session
            course_model = Courses(
                course_name=course_name,
                session=session  # Add the session relationship
            )
            course_model.save()
            
            messages.success(request, "Successfully Added Course")
            return HttpResponseRedirect(reverse("manage_course"))
            
        except SessionYearModel.DoesNotExist:
            messages.error(request, "Invalid Session Selected")
            return HttpResponseRedirect(reverse("add_course"))
        except Exception as e:
            print(f"Error: {e}")
            messages.error(request, f"Failed To Add Course: {str(e)}")
            return HttpResponseRedirect(reverse("add_course"))

def add_student(request):
    form = AddStudentForm()
    return render(request, "hod_template/add_student_template.html", {"form": form})


def add_student_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed")
    
    form = AddStudentForm(request.POST, request.FILES)
    if not form.is_valid():
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return render(request, "hod_template/add_student_template.html", {"form": form})
    
    try:
        # Get form data
        data = form.cleaned_data
        
        # Check if username already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            messages.error(request, f"Username {data['username']} already exists")
            return HttpResponseRedirect(reverse("add_student"))
        
        # Handle profile picture
        profile_pic_url = ""
        if 'profile_pic' in request.FILES:
            fs = FileSystemStorage()
            filename = fs.save(request.FILES['profile_pic'].name, request.FILES['profile_pic'])
            profile_pic_url = fs.url(filename)

        # Create user and student in a transaction
        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=data['username'],
                password=data['password'],
                email=data['email'],
                last_name=data['last_name'],
                first_name=data['first_name'],
                user_type=3,
            )

            course_obj = Courses.objects.get(id=data['course'])
            session_year = SessionYearModel.objects.get(id=data['session_year_id'])
            
            Students.objects.create(
                admin=user,
                address=data['address'],
                phone_number=data['phone_number'],
                roll_number=data['roll_number'],
                course_id=course_obj,
                session_year_id=session_year,
                gender=data['gender'],
                profile_pic=profile_pic_url
            )
        
        messages.success(request, "Successfully Added Student")
        return HttpResponseRedirect(reverse("manage_student"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # This will print the full traceback
        messages.error(request, f"Failed to Add Student: {str(e)}")
        return HttpResponseRedirect(reverse("add_student"))


@login_required
def parent_student_detail_view(request):
    try:
        parent = Parents.objects.get(admin=request.user)

        if not parent.student_id:
            messages.error(request, "No student is assigned to your account.")
            return redirect("parent_home")  # or render a template with error

        student = parent.student_id

        attendance_reports = AttendanceReport.objects.filter(student_id=student)
        results = StudentResult.objects.filter(student_id=student)
        leave_reports = LeaveReportStudent.objects.filter(student_id=student)
        notifications = NotificationStudent.objects.filter(student_id=student)

        context = {
            "student": student,
            "attendance_reports": attendance_reports,
            "results": results,
            "leave_reports": leave_reports,
            "notifications": notifications,
        }
        return render(request, "Parent_template/view_student_details.html", context)

    except Parents.DoesNotExist:
        messages.error(request, "Parent profile not found.")
        return redirect("parent_home")
    
def add_parent(request):
    students = Students.objects.all().select_related('admin')
    form = AddParentForm()
    return render(request, "hod_template/add_parent_template.html", {
        "form": form,
        "students": students
    })
    
@transaction.atomic
def add_parent_save(request):
    if request.method == "POST":
        form = AddParentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Get the student instance
                student_id = form.cleaned_data['student_id']
                relationship = form.cleaned_data['relationship']
                
                try:
                    student = Students.objects.get(id=student_id.id)
                except Students.DoesNotExist:
                    messages.error(request, "Selected student does not exist")
                    return redirect('add_parent')

                # Check if this relationship type already exists for the student
                if relationship in ['Father', 'Mother']:
                    existing_parent = Parents.objects.filter(
                        student_id=student, 
                        relationship=relationship
                    ).first()
                    
                    if existing_parent:
                        messages.error(
                            request, 
                            f"This student already has a {relationship.lower()}: {existing_parent.name}"
                        )
                        return redirect('add_parent')

                # Handle profile picture upload
                profile_pic = request.FILES.get('profile_pic')
                profile_pic_url = None
                if profile_pic:
                    fs = FileSystemStorage()
                    filename = fs.save(profile_pic.name, profile_pic)
                    profile_pic_url = fs.url(filename)

                # Create user and parent
                user = CustomUser.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    user_type=4  # Parent
                )

                Parents.objects.create(
                    admin=user,
                    name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                    email=form.cleaned_data['email'],
                    phone_number=form.cleaned_data['phone_number'],
                    address=form.cleaned_data['address'],
                    student_id=student,
                    relationship=relationship,
                    profile_pic=profile_pic_url
                )

                messages.success(request, "Parent added successfully!")
                return redirect('manage_parent')

            except IntegrityError as e:
                messages.error(request, f"Error creating parent: {str(e)}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        
        # If form is invalid
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return redirect('add_parent')
    
    return redirect('add_parent')

def manage_parent(request):
    parents = Parents.objects.all().select_related("admin", "student_id__admin")
    
    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        parents = parents.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__username__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(student_id__admin__first_name__icontains=search_query) |
            Q(student_id__admin__last_name__icontains=search_query)
        )
    
    # Pagination - 50 parents per page
    paginator = Paginator(parents, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "parents": page_obj,
        "page_title": "Manage Parents"
    }
    return render(request, "hod_template/manage_parent_template.html", context)


@login_required
def edit_parent(request, parent_id):
    try:
        parent = Parents.objects.get(id=parent_id)  # Get by parent's ID
        students = Students.objects.all()
        return render(request, "hod_template/edit_parent_template.html", {
            "parent": parent,
            "students": students,
            "id": parent_id
        })
    except Parents.DoesNotExist:
        messages.error(request, "Parent not found")
        return redirect('manage_parent')

@login_required
def edit_parent_save(request):
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('manage_parent')
    
    try:
        parent_id = request.POST.get('parent_id')
        if not parent_id:
            raise ValueError("Parent ID is required")
            
        # Get the parent instance
        parent = Parents.objects.get(id=parent_id)
        relationship = request.POST.get('relationship')
        
        # Get the student instance if student_id is provided
        student_id = request.POST.get('student_id')
        student = parent.student_id  # Default to current student
        if student_id:
            try:
                new_student = Students.objects.get(id=student_id)
                student = new_student
            except Students.DoesNotExist:
                messages.error(request, "Selected student does not exist")
                return redirect('edit_parent', parent_id=parent_id)

        # Check if this relationship type already exists for the student
        if relationship in ['Father', 'Mother']:
            existing_parent = Parents.objects.filter(
                student_id=student, 
                relationship=relationship
            ).exclude(id=parent_id).first()
            
            if existing_parent:
                messages.error(
                    request, 
                    f"This student already has a {relationship.lower()}: {existing_parent.name}"
                )
                return redirect('edit_parent', parent_id=parent_id)

        # Update CustomUser model
        user = parent.admin
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.save()

        # Update Parents model
        parent.address = request.POST.get('address')
        parent.phone_number = request.POST.get('phone_number')
        parent.relationship = relationship
        parent.student_id = student
            
        # Handle profile picture upload
        if 'profile_pic' in request.FILES:
            profile_pic = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(profile_pic.name, profile_pic)
            parent.profile_pic = fs.url(filename)
            
        parent.save()

        messages.success(request, "Parent Updated Successfully!")
        return redirect('manage_parent')
        
    except Parents.DoesNotExist:
        messages.error(request, "Parent not found")
        return redirect('manage_parent')
    except Exception as e:
        messages.error(request, f"Failed to Update Parent: {str(e)}")
        return redirect('edit_parent', parent_id=parent_id if 'parent_id' in locals() else '')


def delete_parent(request, parent_id):
    try:
        # Get the parent object using the parent_id
        parent = Parents.objects.get(id=parent_id)
        
        # Get the associated user object through the parent's admin field
        user = parent.admin
        
        # First delete the parent record
        parent.delete()
        
        # Then delete the user record
        user.delete()
        
        messages.success(request, "Parent Deleted Successfully.")
        return redirect('manage_parent')
        
    except Parents.DoesNotExist:
        messages.error(request, "Parent does not exist")
        return redirect('manage_parent')
        
    except Exception as e:
        messages.error(request, f"Failed to Delete Parent: {str(e)}")
        return redirect('manage_parent')


def delete_session(request, session_id):
    if request.method == 'POST':
        try:
            session = SessionYearModel.objects.get(id=session_id)
            
            # Check for related students
            student_count = Students.objects.filter(session_year_id=session).count()
            
            if student_count > 0:
                messages.error(
                    request,
                    f"Cannot delete session! {student_count} student(s) are enrolled."
                )
                return redirect('manage_session')
                
            session.delete()
            messages.success(request, "Session deleted successfully!")
            
        except SessionYearModel.DoesNotExist:
            messages.error(request, "Session not found!")
        except Exception as e:
            messages.error(request, f"Error deleting session: {str(e)}")
            
    return redirect('manage_session')


def add_subject(request):
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(
        request,
        "hod_template/add_subject_template.html",
        {"staffs": staffs, "courses": courses},
    )


def add_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>", status=405)
    
    subject_name = request.POST.get("subject_name")
    course_id = request.POST.get("course")
    staff_id = request.POST.get("staff")

    # Basic validation
    if not all([subject_name, course_id, staff_id]):
        messages.error(request, "All fields are required")
        return HttpResponseRedirect(reverse("add_subject"))

    try:
        course = Courses.objects.get(id=course_id)
        staff = CustomUser.objects.get(id=staff_id)

        # Check if subject already exists for this course
        if Subjects.objects.filter(subject_name=subject_name, course_id=course).exists():
            messages.error(request, f"Subject '{subject_name}' already exists for this course")
            return HttpResponseRedirect(reverse("add_subject"))

        # Check if staff is already assigned to this subject in any course
        if Subjects.objects.filter(subject_name=subject_name, staff_id=staff).exists():
            messages.error(request, f"This staff is already assigned to subject '{subject_name}'")
            return HttpResponseRedirect(reverse("add_subject"))

        # Create new subject
        subject = Subjects(
            subject_name=subject_name,
            course_id=course,
            staff_id=staff
        )
        subject.save()
        
        messages.success(request, "Successfully Added Subject")
        return HttpResponseRedirect(reverse("add_subject"))

    except Courses.DoesNotExist:
        messages.error(request, "Selected course does not exist")
    except CustomUser.DoesNotExist:
        messages.error(request, "Selected staff does not exist")
    except Exception as e:
        messages.error(request, f"Failed to Add Subject: {str(e)}")
    
    return HttpResponseRedirect(reverse("add_subject"))


def manage_staff(request):
    staffs = Staffs.objects.all().select_related("admin")
    
    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        staffs = staffs.filter(
            Q(admin__first_name__icontains=search_query) |
            Q(admin__last_name__icontains=search_query) |
            Q(admin__username__icontains=search_query) |
            Q(admin__email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Pagination - 50 staff per page (same as students)
    paginator = Paginator(staffs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "staffs": page_obj,
        "page_title": "Manage Staff"
    }
    return render(request, "hod_template/manage_staff_template.html", context)


def manage_student(request):
    students = Students.objects.all().select_related(
        "admin", "course_id", "session_year_id"
    )
    courses = Courses.objects.all()
    subjects = Subjects.objects.all()

    # Search and filter functionality (keep existing)
    search_query = request.GET.get("search")
    if search_query:
        students = students.filter(
            Q(admin__first_name__icontains=search_query)
            | Q(admin__last_name__icontains=search_query)
            | Q(admin__username__icontains=search_query)
            | Q(admin__email__icontains=search_query)
            | Q(phone_number__icontains=search_query)
        )

    course_filter = request.GET.get("course")
    if course_filter:
        students = students.filter(course_id=course_filter)

    subject_filter = request.GET.get("subject")
    if subject_filter:
        students = students.filter(
            enrolledsubject__subject_id=subject_filter
        ).distinct()

    # Updated pagination - 50 students per page
    paginator = Paginator(students, 50)  # Changed from 25 to 50
    page_number = request.GET.get("page")
    students = paginator.get_page(page_number)

    context = {
        "students": students,
        "courses": courses,
        "subjects": subjects,
    }
    return render(request, "hod_template/manage_student_template.html", context)


def get_subjects_for_course(request):
    course_id = request.GET.get("course_id")
    if course_id:
        subjects = Subjects.objects.filter(course_id=course_id)
        data = {
            "subjects": [{"id": s.id, "subject_name": s.subject_name} for s in subjects]
        }
    else:
        data = {"subjects": []}
    return JsonResponse(data)


def print_student_records(request):
    course_id = request.GET.get("course")
    subject_id = request.GET.get("subject")

    # Filter students based on parameters
    students = Students.objects.all()
    course_filter = None
    subject_filter = None

    if course_id:
        students = students.filter(course_id=course_id)
        course_filter = Courses.objects.get(id=course_id)

    if subject_id:
        students = students.filter(course__subjects__id=subject_id)
        subject_filter = Subjects.objects.get(id=subject_id)

    template = get_template("hod_template/print_student_records.html")
    context = {
        "students": students,
        "course_filter": course_filter,
        "subject_filter": subject_filter,
    }

    html = template.render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="student_records.pdf"'

    # Create PDF (requires reportlab or weasyprint)
    # For simplicity, you can return HTML first, then add PDF later
    return HttpResponse(html)


def manage_course(request):
    # Remove the trailing comma and fix select_related parameter
    courses = Courses.objects.select_related('session').order_by('course_name').all()
    
    sessions = SessionYearModel.objects.all()
    
    # Apply session filter if provided
    session_id = request.GET.get('session')
    if session_id:
        courses = courses.filter(session_id=session_id)
    
    # Apply search filter if provided
    search_term = request.GET.get('search')
    if search_term:
        courses = courses.filter(course_name__icontains=search_term)
    
    return render(
        request, 
        "hod_template/manage_course_template.html", 
        {
            "courses": courses,
            "sessions": sessions
        }
    )


def student_profile_view(request, student_id):
    try:
        # Get the student object or return 404 if not found
        student = Students.objects.get(admin=student_id)

        # Prepare context data
        context = {"student": student, "page_title": "Student Profile"}

        return render(request, "hod_template/student_profile.html", context)

    except Students.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect("manage_student")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("manage_student")

def parent_profile_view(request, parent_id):
    try:
        parent = get_object_or_404(Parents, id=parent_id)
        
        # Get student information if exists
        student_info = None
        if parent.student_id:
            student = parent.student_id
            student_info = {
                'name': f"{student.admin.first_name} {student.admin.last_name}",
                'id': student.admin.id,
                'course': student.course_id.course_name,
                'session': f"{student.session_year_id.session_start_year} - {student.session_year_id.session_end_year}"
            }
        
        context = {
            'parent': parent,
            'student_info': student_info,
            'page_title': 'Parent Profile'
        }
        return render(request, 'hod_template/parent_profile.html', context)
        
    except Exception as e:
        messages.error(request, f"Error accessing parent profile: {str(e)}")
        return redirect('manage_parent')


def manage_subject(request):
    # Corrected select_related based on your model structure
    subjects = Subjects.objects.all().select_related(
        'course_id',
        'staff_id'  # Assuming staff_id is the ForeignKey to Staffs model
    )
    
    # Get all courses and staff for filters
    courses = Courses.objects.all()
    staffs = Staffs.objects.select_related('adminhod')  # Adjust based on your Staff model
    
    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        subjects = subjects.filter(
            Q(subject_name__icontains=search_query) |
            Q(course_id__course_name__icontains=search_query) |
            Q(staff_id__adminhod__first_name__icontains=search_query) |  # Adjusted to adminhod
            Q(staff_id__adminhod__last_name__icontains=search_query)     # Adjusted to adminhod
        )
    
    # Filter by course
    course_filter = request.GET.get("course")
    if course_filter:
        subjects = subjects.filter(course_id=course_filter)
    
    # Filter by staff
    staff_filter = request.GET.get("staff")
    if staff_filter:
        subjects = subjects.filter(staff_id=staff_filter)
    
    # Pagination - 50 subjects per page
    paginator = Paginator(subjects, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "subjects": page_obj,
        "courses": courses,
        "staffs": staffs,
        "page_title": "Manage Subjects"
    }
    return render(request, "hod_template/manage_subject_template.html", context)


def edit_staff(request, staff_id):
    staff = Staffs.objects.get(admin=staff_id)
    return render(
        request,
        "hod_template/edit_staff_template.html",
        {"staff": staff, "id": staff_id},
    )

def edit_session(request, session_id):
    try:
        session = SessionYearModel.objects.get(id=session_id)
        
        if request.method == 'POST':
            session_start = request.POST.get('session_start')
            session_end = request.POST.get('session_end')
            
            try:
                # Convert strings to dates
                start_date = datetime.strptime(session_start, "%Y-%m-%d").date()
                end_date = datetime.strptime(session_end, "%Y-%m-%d").date()
                current_date = timezone.now().date()

                # Validate dates
                if start_date < current_date:
                    messages.error(request, "Session start date cannot be in the past")
                    return redirect('edit_session', session_id=session_id)
                
                if end_date < current_date:
                    messages.error(request, "Session end date cannot be in the past")
                    return redirect('edit_session', session_id=session_id)
                
                if end_date <= start_date:
                    messages.error(request, "Session end date must be after start date")
                    return redirect('edit_session', session_id=session_id)

                # Check if another session with same dates exists (excluding current)
                if SessionYearModel.objects.filter(
                    session_start_year=session_start,
                    session_end_year=session_end
                ).exclude(id=session_id).exists():
                    messages.error(request, "Session with these dates already exists")
                    return redirect('edit_session', session_id=session_id)

                # Check if any students are enrolled in this session
                student_count = Students.objects.filter(session_year_id=session).count()
                if student_count > 0:
                    messages.warning(
                        request,
                        f"Note: {student_count} student(s) are currently enrolled in this session"
                    )

                # Update session
                session.session_start_year = session_start
                session.session_end_year = session_end
                session.save()
                
                messages.success(request, "Session updated successfully")
                return redirect('manage_session')
            
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD")
                return redirect('edit_session', session_id=session_id)
            except Exception as e:
                messages.error(request, f"Error updating session: {str(e)}")
                return redirect('edit_session', session_id=session_id)
        
        # For GET request, show edit form
        context = {
            'session': session,
            'id': session_id,
            'student_count': Students.objects.filter(session_year_id=session).count()
        }
        return render(request, 'hod_template/edit_session_template.html', context)
        
    except SessionYearModel.DoesNotExist:
        messages.error(request, "Session not found")
        return redirect('manage_session')
    except Exception as e:
        messages.error(request, f"Error accessing session: {str(e)}")
        return redirect('manage_session')

def edit_staff_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    
    staff_id = request.POST.get("staff_id")
    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    email = request.POST.get("email")
    username = request.POST.get("username")
    address = request.POST.get("address")
    phone_number = request.POST.get("phone_number")
    qualification = request.POST.get("qualification")
    specialization = request.POST.get("specialization")
    years_of_experience = request.POST.get("years_of_experience")
    joining_date = request.POST.get("joining_date")
    gender = request.POST.get("gender")  # Get gender from form
    profile_pic = request.FILES.get("profile_pic")

    try:
        # Update User
        user = CustomUser.objects.get(id=staff_id)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username
        user.save()

        # Update Staff
        staff_model = Staffs.objects.get(admin=staff_id)
        staff_model.address = address
        staff_model.phone_number = phone_number
        staff_model.qualification = qualification
        staff_model.specialization = specialization
        staff_model.years_of_experience = years_of_experience
        staff_model.joining_date = joining_date
        staff_model.gender = gender  # Update gender field

        if profile_pic:
            # 1. Delete old file if it exists
            if staff_model.profile_pic:
                old_file_path = staff_model.profile_pic.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            # 2. Generate a clean filename (replace spaces and special chars)
            import re
            clean_filename = re.sub(r'[^\w.-]', '_', profile_pic.name)
            
            # 3. Define the upload path explicitly
            upload_path = f"staff_profile_pics/{clean_filename}"

            # 4. Save the file (Django handles MEDIA_ROOT automatically)
            staff_model.profile_pic.save(upload_path, profile_pic)

        staff_model.save()
        messages.success(request, "Successfully Updated Staff Details")
        return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": staff_id}))

    except Exception as e:
        messages.error(request, f"Failed to Update Staff: {str(e)}")
        return HttpResponseRedirect(reverse("edit_staff", kwargs={"staff_id": staff_id}))


def delete_staff(request, staff_id):
    try:
        with transaction.atomic():
            staff = Staffs.objects.get(admin=staff_id)
            user = staff.admin

            # Delete profile picture if exists
            if staff.profile_pic:
                try:
                    # Get the relative path (not the absolute path)
                    relative_path = (
                        staff.profile_pic.name
                    )  # e.g., 'staff_profile_pics/filename.jpg'
                    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

                    # Normalize the path to avoid path traversal issues
                    normalized_path = os.path.normpath(full_path)
                    media_root = os.path.normpath(settings.MEDIA_ROOT)

                    # Check if the file is inside MEDIA_ROOT
                    if normalized_path.startswith(media_root) and os.path.exists(
                        normalized_path
                    ):
                        os.remove(normalized_path)
                except Exception as e:
                    messages.error(
                        request, f"Failed to delete profile picture: {str(e)}"
                    )

            # Delete the staff record first
            staff.delete()

            # Then delete the associated user
            user.delete()

            messages.success(request, "Staff member deleted successfully.")
            return redirect("manage_staff")

    except Staffs.DoesNotExist:
        messages.error(request, "Staff member does not exist.")
    except CustomUser.DoesNotExist:
        messages.error(request, "User account does not exist.")
    except Exception as e:
        messages.error(request, f"Failed to delete staff member. Error: {str(e)}")

    return redirect("manage_staff")


def edit_student(request, student_id):
    request.session["student_id"] = student_id
    student = Students.objects.get(admin=student_id)
    form = EditStudentForm()
    form.fields["email"].initial = student.admin.email
    form.fields["first_name"].initial = student.admin.first_name
    form.fields["last_name"].initial = student.admin.last_name
    form.fields["username"].initial = student.admin.username
    form.fields["address"].initial = student.address
    form.fields["course"].initial = student.course_id.id
    form.fields["phone_number"].initial = student.phone_number
    if 'gender' in form.fields:
        form.fields["gender"].initial = student.gender
    else:
        # Fallback to 'sex' if 'gender' doesn't exist
        form.fields["sex"].initial = student.gender
    form.fields["session_year_id"].initial = student.session_year_id.id
    
    return render(
        request,
        "hod_template/edit_student_template.html",
        {
            "form": form,
            "id": student_id,
            "username": student.admin.username,
            "student": student  # Add this line to pass student object to template
        },
    )


def edit_student_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        student_id = request.session.get("student_id")
        if student_id == None:
            return HttpResponseRedirect(reverse("manage_student"))

        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            username = form.cleaned_data["username"]
            roll_number=form.cleaned_data["roll_number"]
            email = form.cleaned_data["email"]
            address = form.cleaned_data["address"]
            phone_number = form.cleaned_data["phone_number"]
            session_year_id = form.cleaned_data["session_year_id"]
            course_id = form.cleaned_data["course"]
            gender = form.cleaned_data["gender"]

            if request.FILES.get("profile_pic", False):
                profile_pic = request.FILES["profile_pic"]
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None

            try:
                user = CustomUser.objects.get(id=student_id)
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
                user.email = email
                user.save()

                student = Students.objects.get(admin=student_id)
                student.address = address
                student.roll_number=roll_number
                student.phone_number = phone_number
                session_year = SessionYearModel.objects.get(id=session_year_id)
                student.session_year_id = session_year
                student.gender = gender
                course = Courses.objects.get(id=course_id)
                student.course_id = course
                if profile_pic_url != None:
                    student.profile_pic = profile_pic_url
                student.save()
                del request.session["student_id"]
                messages.success(request, "Successfully Edited Student")
                return HttpResponseRedirect(
                    reverse("manage_student")
                )
            except Exception as e:
                messages.error(request, f"Failed to Edit Student: {str(e)}")
                return HttpResponseRedirect(
                    reverse("edit_student", kwargs={"student_id": student_id})
                )
        else:
            form = EditStudentForm(request.POST)
            student = Students.objects.get(admin=student_id)
            return render(
                request,
                "hod_template/edit_student_template.html",
                {"form": form, "id": student_id, "username": student.admin.username},
            )


def delete_student(request, student_id):
    try:
        with transaction.atomic():
            # Get the student and user objects
            student = Students.objects.get(admin=student_id)
            user = student.admin

            # Delete the student record first
            student.delete()

            # Then delete the associated user
            user.delete()

            messages.success(request, "Student deleted successfully.")
            return redirect("manage_student")

    except Students.DoesNotExist:
        messages.error(request, "Student does not exist.")
    except User.DoesNotExist:
        messages.error(request, "User account does not exist.")
    except Exception as e:
        messages.error(request, f"Failed to delete student. Error: {str(e)}")

    return redirect("manage_student")


def edit_subject(request, subject_id):
    subject = Subjects.objects.get(id=subject_id)
    courses = Courses.objects.all()
    staffs = CustomUser.objects.filter(user_type=2)
    return render(
        request,
        "hod_template/edit_subject_template.html",
        {"subject": subject, "staffs": staffs, "courses": courses, "id": subject_id},
    )


def edit_subject_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        subject_id = request.POST.get("subject_id")
        subject_name = request.POST.get("subject_name")
        staff_id = request.POST.get("staff")
        course_id = request.POST.get("course")

        try:
            subject = Subjects.objects.get(id=subject_id)
            subject.subject_name = subject_name
            staff = CustomUser.objects.get(id=staff_id)
            subject.staff_id = staff
            course = Courses.objects.get(id=course_id)
            subject.course_id = course
            subject.save()

            messages.success(request, "Successfully Edited Subject")
            return HttpResponseRedirect(
                reverse("manage_subject")
            )
        except:
            messages.error(request, "Failed to Edit Subject")
            return HttpResponseRedirect(
                reverse("edit_subject", kwargs={"subject_id": subject_id})
            )


def delete_subject(request, subject_id):
    try:
        with transaction.atomic():
            subject = Subjects.objects.get(id=subject_id)

            # Check for dependent records
            if subject.attendance_set.exists() or subject.studentresult_set.exists():
                messages.error(
                    request, "Cannot delete: Subject has attendance or result records"
                )
                return redirect("manage_subject")

            subject.delete()
            messages.success(request, "Subject deleted successfully")

    except Subjects.DoesNotExist:
        messages.error(request, "Subject not found")
    except Exception as e:
        messages.error(request, f"Deletion failed: {str(e)}")

    return redirect("manage_subject")


def edit_course(request, course_id):
    course = Courses.objects.get(id=course_id)
    return render(
        request,
        "hod_template/edit_course_template.html",
        {"course": course, "id": course_id},
    )


def edit_course_save(request):
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    
    course_id = request.POST.get("course_id")
    course_name = request.POST.get("course")

    try:
        # Check if another course with the same name exists (excluding current course)
        if Courses.objects.filter(course_name__iexact=course_name).exclude(id=course_id).exists():
            messages.error(request, f"Course '{course_name}' already exists!")
            return HttpResponseRedirect(reverse("edit_course", kwargs={"course_id": course_id}))
        
        course = Courses.objects.get(id=course_id)
        course.course_name = course_name
        course.save()
        messages.success(request, "Successfully Edited Course")
        return HttpResponseRedirect(reverse("manage_course"))
    
    except Exception as e:
        print(f"Error editing course: {str(e)}")
        messages.error(request, "Failed to Edit Course")
        return HttpResponseRedirect(reverse("manage_course"))
        
        
def delete_course(request, course_id):
    try:
        with transaction.atomic():
            course = Courses.objects.get(id=course_id)

            # Check for enrolled students
            if hasattr(course, "students") and course.students.exists():
                messages.error(request, "Cannot delete: Course has enrolled students")
                return redirect("manage_course")

            # Check for subjects with staff assignments
            subjects_with_staff = Subjects.objects.filter(
                course_id=course, staff_id__isnull=False
            )

            if subjects_with_staff.exists():
                # Get staff names for the error message
                staff_names = ", ".join(
                    f"{sub.staff_id.admin.first_name} {sub.staff_id.admin.last_name}"
                    for sub in subjects_with_staff
                )
                messages.error(
                    request, f"Cannot delete: Course has staff assigned ({staff_names})"
                )
                return redirect("manage_course")

            # If no dependencies, delete subjects then course
            Subjects.objects.filter(course_id=course).delete()
            course.delete()
            messages.success(
                request, "Course and related subjects deleted successfully"
            )

    except Courses.DoesNotExist:
        messages.error(request, "Course not found")
    except Exception as e:
        messages.error(request, f"Deletion failed: {str(e)}")

    return redirect("manage_course")


def manage_session(request):
    sessions = SessionYearModel.objects.all().order_by('-session_start_year')
    return render(request, 'hod_template/manage_session_template.html', {'sessions': sessions})

from django.utils import timezone

from datetime import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError

def add_session_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("manage_session"))
    
    session_start = request.POST.get("session_start")
    session_end = request.POST.get("session_end")

    if not session_start or not session_end:
        messages.error(request, "Both start and end dates are required")
        return HttpResponseRedirect(reverse("manage_session"))

    try:
        # Convert strings to dates
        start_date = datetime.strptime(session_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(session_end, "%Y-%m-%d").date()
        current_date = timezone.now().date()

        # Validate dates
        # if start_date < current_date:
        #     messages.error(request, "Session start date cannot be in the past")
        #     return HttpResponseRedirect(reverse("manage_session"))
        
        if end_date < current_date:
            messages.error(request, "Session end date cannot be in the past")
            return HttpResponseRedirect(reverse("manage_session"))
        
        if end_date <= start_date:
            messages.error(request, "Session end date must be after start date")
            return HttpResponseRedirect(reverse("manage_session"))

        # Create and save session
        sessionyear = SessionYearModel(
            session_start_year=session_start,
            session_end_year=session_end
        )
        sessionyear.full_clean()  # Validate model fields
        sessionyear.save()
        
        messages.success(request, "Successfully Added Session")
        return HttpResponseRedirect(reverse("manage_session"))
    
    except ValueError as e:
        messages.error(request, f"Invalid date format: {str(e)}. Please use YYYY-MM-DD")
        return HttpResponseRedirect(reverse("manage_session"))
    except ValidationError as e:
        messages.error(request, f"Validation error: {', '.join(e.messages)}")
        return HttpResponseRedirect(reverse("manage_session"))
    except Exception as e:
        messages.error(request, f"Failed to Add Session: {str(e)}")
        return HttpResponseRedirect(reverse("manage_session"))


@csrf_exempt
def check_email_exist(request):
    email = request.POST.get("email")
    user_obj = CustomUser.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
def check_username_exist(request):
    username = request.POST.get("username")
    user_obj = CustomUser.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


def staff_feedback_message(request):
    feedbacks = FeedBackStaffs.objects.all()
    return render(
        request, "hod_template/staff_feedback_template.html", {"feedbacks": feedbacks}
    )


def parent_feedback_message(request):
    feedbacks=FeedBackParents.objects.all()
    return render(request,"hod_template/parent_feedback_template.html",{"feedbacks":feedbacks})


def student_feedback_message(request):
    feedbacks = FeedBackStudent.objects.all()
    return render(
        request, "hod_template/student_feedback_template.html", {"feedbacks": feedbacks}
    )


@csrf_exempt
def student_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackStudent.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


@csrf_exempt
def parent_feedback_message_replied(request):
    feedback_id=request.POST.get("id")
    feedback_message=request.POST.get("message")

    try:
        feedback=FeedBackParents.objects.get(id=feedback_id)
        feedback.feedback_reply=feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

@csrf_exempt
@login_required
def send_parent_notification_save(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed", status=405)
    
    parent_id = request.POST.get("parent_id")
    message = request.POST.get("message", "").strip()

    if not message:
        return JsonResponse({"status": "error", "message": "Message cannot be empty"})

    try:
        parent = Parents.objects.get(id=parent_id)
        
        # Save notification to database
        notification = NotificationParents.objects.create(
            parent_id=parent,
            message=message
        )
        
        # Send push notification if FCM token exists
        if parent.fcm_token:
            url = "https://fcm.googleapis.com/fcm/send"
            body = {
                "notification": {
                    "title": "School Notification",
                    "body": message,
                    "icon": "/static/dist/img/user2-160x160.jpg"
                },
                "to": parent.fcm_token
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": "key=YOUR_SERVER_KEY_HERE"
            }
            response = requests.post(url, data=json.dumps(body), headers=headers)
            print("FCM Response:", response.text)
        
        return JsonResponse({"status": "success"})
    except Parents.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Parent not found"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
@login_required
def view_parent_feedback(request):
    feedbacks = FeedBackParents.objects.all().select_related('parent_id', 'parent_id__student_id')
    return render(request, "hod_template/view_parent_feedback.html", {
        "feedbacks": feedbacks
    })

@csrf_exempt
@login_required
def parent_feedback_reply(request):
    if request.method != "POST":
        return HttpResponse("Method Not Allowed", status=405)
    
    feedback_id = request.POST.get("feedback_id")
    reply = request.POST.get("reply", "").strip()

    try:
        feedback = FeedBackParents.objects.get(id=feedback_id)
        feedback.feedback_reply = reply
        feedback.save()
        return JsonResponse({"status": "success"})
    except FeedBackParents.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Feedback not found"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
    
@csrf_exempt
def staff_feedback_message_replied(request):
    feedback_id = request.POST.get("id")
    feedback_message = request.POST.get("message")

    try:
        feedback = FeedBackStaffs.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_message
        feedback.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")


def staff_leave_view(request):
    leaves = LeaveReportStaff.objects.all()
    return render(request, "hod_template/staff_leave_view.html", {"leaves": leaves})


def student_leave_view(request):
    leaves = LeaveReportStudent.objects.all()
    return render(request, "hod_template/student_leave_view.html", {"leaves": leaves})


def student_approve_leave(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))


def student_disapprove_leave(request, leave_id):
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("student_leave_view"))


def staff_approve_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def staff_disapprove_leave(request, leave_id):
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return HttpResponseRedirect(reverse("staff_leave_view"))


def admin_view_attendance(request):
    subjects = Subjects.objects.all()
    session_year_id = SessionYearModel.objects.all()
    return render(
        request,
        "hod_template/admin_view_attendance.html",
        {"subjects": subjects, "session_year_id": session_year_id},
    )


@csrf_exempt
def admin_get_attendance_dates(request):
    subject = request.POST.get("subject")
    session_year_id = request.POST.get("session_year_id")
    subject_obj = Subjects.objects.get(id=subject)
    session_year_obj = SessionYearModel.objects.get(id=session_year_id)
    attendance = Attendance.objects.filter(
        subject_id=subject_obj, session_year_id=session_year_obj
    )
    attendance_obj = []
    for attendance_single in attendance:
        data = {
            "id": attendance_single.id,
            "attendance_date": str(attendance_single.attendance_date),
            "session_year_id": attendance_single.session_year_id.id,
        }
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj), safe=False)


@csrf_exempt
def admin_get_attendance_student(request):
    attendance_date = request.POST.get("attendance_date")
    attendance = Attendance.objects.get(id=attendance_date)

    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    list_data = []

    for student in attendance_data:
        data_small = {
            "id": student.student_id.admin.id,
            "name": student.student_id.admin.first_name
            + " "
            + student.student_id.admin.last_name,
            "status": student.status,
        }
        list_data.append(data_small)
    return JsonResponse(
        json.dumps(list_data), content_type="application/json", safe=False
    )


@login_required
def admin_profile(request):
    # Check if user is an admin (user_type=1)
    if request.user.user_type != "1":
        messages.error(request, "Access Denied: You are not an admin!")
        return redirect("admin_home")

    try:
        # Get the AdminHOD profile (or return 404)
        admin = AdminHOD.objects.get(admin=request.user)
        return render(request, "hod_template/admin_profile.html", {"admin": admin})

    except AdminHOD.DoesNotExist:
        # Auto-create admin profile if missing (optional)
        admin = AdminHOD.objects.create(
            admin=request.user,
            address="Not Set",
            phone_number="Not Set",
            gender="Other"
        )
        messages.info(request, "Admin profile was auto-created.")
        return render(request, "hod_template/admin_profile.html", {"admin": admin})

    except Exception as e:
        messages.error(request, f"Error loading profile: {str(e)}")
        return redirect("admin_home")


def admin_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("admin_profile"))
    else:
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        password = request.POST.get("password")
        try:
            customuser = CustomUser.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            # if password!=None and password!="":
            #     customuser.set_password(password)
            customuser.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("admin_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("admin_profile"))


def admin_send_notification_student(request):
    students = Students.objects.all()
    return render(
        request, "hod_template/student_notification.html", {"students": students}
    )


def admin_send_notification_staff(request):
    staffs = Staffs.objects.all()
    return render(request, "hod_template/staff_notification.html", {"staffs": staffs})

def admin_send_notification_parent(request):
    parents = Parents.objects.all().select_related('admin', 'student_id__admin')
    return render(request, "hod_template/parent_notification.html", {"parents": parents})

def send_parent_notification(request):
    id=request.POST.get("id")
    message=request.POST.get("message")
    parent=Parents.objects.get(admin=id)
    token=parent.fcm_token
    url="https://fcm.googleapis.com/fcm/send"
    body={
        "notification":{
            "title":"Student Management System",
            "body":message,
            "click_action": "https://studentmanagementsystem22.herokuapp.com/parent_all_notification",
            "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg"
        },
        "to":token
    }
    headers={"Content-Type":"application/json","Authorization":"key=SERVER_KEY_HERE"}
    data=requests.post(url,data=json.dumps(body),headers=headers)
    notification=NotificationParents(parent_id=Parents,message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")


@csrf_exempt
def send_student_notification(request):
    id = request.POST.get("id")
    message = request.POST.get("message")
    student = Students.objects.get(admin=id)
    token = student.fcm_token
    url = "https://fcm.googleapis.com/fcm/send"
    body = {
        "notification": {
            "title": "Student Management System",
            "body": message,
            "click_action": "https://studentmanagementsystem22.herokuapp.com/student_all_notification",
            "icon": "http://studentmanagementsystem22.herokuapp.com/static/dist/img/user2-160x160.jpg",
        },
        "to": token,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=SERVER_KEY_HERE",
    }
    data = requests.post(url, data=json.dumps(body), headers=headers)
    notification = NotificationStudent(student_id=student, message=message)
    notification.save()
    print(data.text)
    return HttpResponse("True")


@require_POST
@login_required
def send_staff_notification(request):
    try:
        # Try to parse JSON data first
        try:
            data = json.loads(request.body)
            staff_id = data.get("staff_id")
            message = data.get("message", "").strip()
        except:
            # Fall back to form data
            staff_id = request.POST.get("staff_id")
            message = request.POST.get("message", "").strip()
        
        # Validate inputs
        if not staff_id:
            return JsonResponse({
                "status": "error", 
                "message": "Staff ID is required"
            }, status=400)
            
        if not message:
            return JsonResponse({
                "status": "error", 
                "message": "Message cannot be empty"
            }, status=400)
        
        # Get staff member (expecting staff's user ID)
        try:
            staff_user = Staffs.objects.get(admin_id=staff_id)
        except Staffs.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": "Staff member not found"
            }, status=404)
        
        # Save notification to database
        notification = NotificationStaffs.objects.create(
            staff_id=staff_user.id,  # Use the Staffs model ID
            message=message,
            created_by=request.user
        )
        
        return JsonResponse({
            "status": "success",
            "message": "Notification sent successfully",
            "notification_id": notification.id
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": f"An error occurred: {str(e)}"
        }, status=500)


def send_notification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receiver_id = data.get('receiver_id')
            message = data.get('message')
            notification_type = data.get('notification_type', 1)  # Default to student
            
            receiver = CustomUser.objects.get(id=receiver_id)
            
            notification = Notification(
                sender=request.user,
                receiver=receiver,
                message=message,
                notification_type=notification_type
            )
            notification.save()
            
            return JsonResponse({'status': 'success', 'message': 'Notification sent successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def send_parent_notification(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
    
    try:
        parent_id = request.POST.get("parent_id")
        message = request.POST.get("message", "").strip()
        
        if not parent_id:
            return JsonResponse({
                "status": "error", 
                "message": "Parent ID is required"
            }, status=400)
            
        if not message:
            return JsonResponse({
                "status": "error", 
                "message": "Message cannot be empty"
            }, status=400)
        
        # Get parent
        parent = Parents.objects.get(id=parent_id)
        
        # Save notification to database
        notification = NotificationParents.objects.create(
            parent_id=parent,
            message=message
        )
        
        # Optional: Send push notification if FCM token exists
        if hasattr(parent, 'fcm_token') and parent.fcm_token:
            try:
                url = "https://fcm.googleapis.com/fcm/send"
                body = {
                    "notification": {
                        "title": "New Notification",
                        "body": message,
                        "click_action": reverse('parent_all_notification'),
                        "icon": "/static/dist/img/user2-160x160.jpg"
                    },
                    "to": parent.fcm_token
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"key={settings.FCM_SERVER_KEY}"
                }
                requests.post(url, data=json.dumps(body), headers=headers)
            except Exception as e:
                logger.error(f"FCM notification failed for parent {parent_id}: {str(e)}")
        
        return JsonResponse({
            "status": "success",
            "message": "Notification saved successfully",
            "notification_id": notification.id
        })
        
    except Parents.DoesNotExist:
        return JsonResponse({
            "status": "error", 
            "message": "Parent not found"
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": str(e)
        }, status=500)

def get_notifications(request):
    try:
        user = request.user
        notifications = Notification.objects.filter(
            Q(receiver=user) | Q(sender=user)
        ).order_by('-created_at')[:20]  # Get last 20 notifications
        
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'sender': notification.sender.username,
                'receiver': notification.receiver.username,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'is_sender': notification.sender == user,
                'notification_type': notification.notification_type
            })
        
        # Mark unread notifications as read
        Notification.objects.filter(receiver=user, is_read=False).update(is_read=True)
        
        return JsonResponse({'status': 'success', 'notifications': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def get_unread_count(request):
    try:
        count = Notification.objects.filter(receiver=request.user, is_read=False).count()
        return JsonResponse({'status': 'success', 'count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)