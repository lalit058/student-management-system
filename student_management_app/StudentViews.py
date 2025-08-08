import datetime

from django.contrib import messages
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render,get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt

from student_management_app.forms import  EditStudentForm
from student_management_app.models import CustomUser, Courses, Subjects, Students, SessionYearModel, \
    FeedBackStudent, LeaveReportStudent, Attendance, AttendanceReport, \
    NotificationStudent
from student_management_app.models import Students,Notification, AdminHOD, Courses, Subjects, CustomUser, Attendance, AttendanceReport, \
    LeaveReportStudent, FeedBackStudent, NotificationStudent, StudentResult, SessionYearModel
from student_management_system import settings


def student_home(request):
    student_obj = Students.objects.get(admin=request.user.id)
    attendance_total = AttendanceReport.objects.filter(student_id=student_obj).count()
    attendance_present = AttendanceReport.objects.filter(student_id=student_obj, status=True).count()
    attendance_absent = AttendanceReport.objects.filter(student_id=student_obj, status=False).count()
    course = Courses.objects.get(id=student_obj.course_id.id)
    subjects = Subjects.objects.filter(course_id=course).count()
    subjects_data = Subjects.objects.filter(course_id=course)
    session_obj = SessionYearModel.objects.get(id=student_obj.session_year_id.id)

    subject_name = []
    data_present = []
    data_absent = []
    subject_data = Subjects.objects.filter(course_id=student_obj.course_id)
    for subject in subject_data:
        attendance = Attendance.objects.filter(subject_id=subject.id)
        attendance_present_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,  # Changed from attendence_id to attendance_id
            status=True,
            student_id=student_obj.id
        ).count()
        attendance_absent_count = AttendanceReport.objects.filter(
            attendance_id__in=attendance,  # Changed from attendence_id to attendance_id
            status=False,
            student_id=student_obj.id
        ).count()
        subject_name.append(subject.subject_name)
        data_present.append(attendance_present_count)
        data_absent.append(attendance_absent_count)

    return render(request, "student_template/student_home_template.html", {
        "total_attendance": attendance_total,
        "attendance_absent": attendance_absent,
        "attendance_present": attendance_present,
        "subjects": subjects,
        "data_name": subject_name,
        "data1": data_present,
        "data2": data_absent,
    })  
  
def student_view_subjects(request):
    try:
        # Get the logged-in student
        student_obj = Students.objects.get(admin=request.user.id)
        
        # Get all subjects for the student's course
        subjects = Subjects.objects.filter(course_id=student_obj.course_id).select_related('staff_id', 'course_id')
        
        return render(request, "student_template/student_view_subjects.html", {
            "subjects": subjects,
            "student": student_obj
        })
        
    except Exception as e:
        messages.error(request, f"Error loading subjects: {str(e)}")
        return redirect("student_home")
        
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
            email = form.cleaned_data["email"]
            address = form.cleaned_data["address"]
            phone_number = form.cleaned_data["phone_number"]
            session_year_id = form.cleaned_data["session_year_id"]
            course_id = form.cleaned_data["course"]
            sex = form.cleaned_data["sex"]

            if request.FILES.get('profile_pic', False):
                profile_pic = request.FILES['profile_pic']
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
                student.phone_number = phone_number
                session_year = SessionYearModel.objects.get(id=session_year_id)
                student.session_year_id = session_year
                student.gender = sex
                course = Courses.objects.get(id=course_id)
                student.course_id = course
                if profile_pic_url != None:
                    student.profile_pic = profile_pic_url
                student.save()
                del request.session['student_id']
                messages.success(request, "Successfully Edited Student")
                return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": student_id}))
            except Exception as e:
                messages.error(request, f"Failed to Edit Student: {str(e)}")
                return HttpResponseRedirect(reverse("edit_student", kwargs={"student_id": student_id}))
        else:
            form = EditStudentForm(request.POST)
            student = Students.objects.get(admin=student_id)
            return render(request, "hod_template/edit_student_template.html", 
                         {"form": form, "id": student_id, "username": student.admin.username})
            
            
@login_required
def student_view_attendance(request):
    try:
        # Get the student and their enrolled course
        student = Students.objects.get(admin=request.user)
        print(f"Student: {student}, Course: {student.course_id}")  # Debug print
        
        # Get subjects for the student's course
        subjects = Subjects.objects.filter(course_id=student.course_id)
        print(f"Subjects found: {subjects.count()}")  # Debug print
        
        return render(request, 'student_template/student_view_attendance.html', {
            'subjects': subjects,
            'student_course': student.course_id  # Pass course for debugging
        })
        
    except Students.DoesNotExist:
        print("No student record found")  # Debug print
        return render(request, 'student_template/student_view_attendance.html', {
            'subjects': None,
            'error': 'No student record found'
        })

def student_view_attendance_post(request):
    try:
        # Validate required POST parameters
        if not all(k in request.POST for k in ["subject", "start_date", "end_date"]):
            raise ValidationError("Missing required parameters")
            
        subject_id = request.POST.get("subject")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        
        # Parse dates with validation
        try:
            start_data_parse = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_data_parse = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")
            
        # Validate date range
        if start_data_parse > end_data_parse:
            raise ValidationError("Start date cannot be after end date")
            
        # Get database objects with 404 handling
        subject_obj = get_object_or_404(Subjects, id=subject_id)
        user_object = get_object_or_404(CustomUser, id=request.user.id)
        stud_obj = get_object_or_404(Students, admin=user_object)
        
        # Get attendance data
        attendance = Attendance.objects.filter(
            attendance_date__range=(start_data_parse, end_data_parse),
            subject_id=subject_obj
        )
        attendance_reports = AttendanceReport.objects.filter(
            attendance_id__in=attendance,
            student_id=stud_obj
        )
        
        return render(request, "student_template/student_attendance_data.html", {
            "attendance_reports": attendance_reports,
            "subject": subject_obj,
            "start_date": start_date,
            "end_date": end_date
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in student_view_attendance_post: {str(e)}")
        return render(request, "student_template/student_attendance_data.html", {
            "error_message": f"Failed to load attendance data: {str(e)}"
        })
def student_apply_leave(request):
    staff_obj = Students.objects.get(admin=request.user.id)
    leave_data=LeaveReportStudent.objects.filter(student_id=staff_obj)
    return render(request,"student_template/student_apply_leave.html",{"leave_data":leave_data})

def student_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        student_obj=Students.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStudent(student_id=student_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("student_apply_leave"))


def student_feedback(request):
    staff_id=Students.objects.get(admin=request.user.id)
    feedback_data=FeedBackStudent.objects.filter(student_id=staff_id)
    return render(request,"student_template/student_feedback.html",{"feedback_data":feedback_data})

def student_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_feedback"))
    else:
        feedback_msg=request.POST.get("feedback_msg")

        student_obj=Students.objects.get(admin=request.user.id)
        try:
            feedback=FeedBackStudent(student_id=student_obj,feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("student_feedback"))

def student_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    student=Students.objects.get(admin=user)
    return render(request,"student_template/student_profile.html",{"user":user,"student":student})

def student_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("student_profile"))
    else:
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        password=request.POST.get("password")
        address=request.POST.get("address")
        try:
            customuser=CustomUser.objects.get(id=request.user.id)
            customuser.first_name=first_name
            customuser.last_name=last_name
            if password!=None and password!="":
                customuser.set_password(password)
            customuser.save()

            student=Students.objects.get(admin=customuser)
            student.address=address
            student.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("student_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("student_profile"))

@csrf_exempt
def student_fcmtoken_save(request):
    token=request.POST.get("token")
    try:
        student=Students.objects.get(admin=request.user.id)
        student.fcm_token=token
        student.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

def student_all_notification(request):
    student = Students.objects.get(admin=request.user.id)
    
    # Get notifications and mark them as read
    notifications = NotificationStudent.objects.filter(
        student_id=student.id
    ).order_by('-created_at')
    
    # Mark as read
    notifications.update(read_status=True)
    
    # Get general notifications from Notification model
    general_notifications = Notification.objects.filter(
        receiver=request.user
    ).order_by('-created_at')
    
    # Mark general notifications as read
    general_notifications.update(is_read=True)
    
    # Combine both querysets
    all_notifications = list(notifications) + list(general_notifications)
    all_notifications.sort(key=lambda x: x.created_at, reverse=True)
    
    return render(request, "student_template/all_notification.html", {
        "notifications": all_notifications
    })

@login_required
def mark_student_notifications_as_read(request):
    if request.method == 'POST':
        try:
            student = Students.objects.get(admin=request.user)
            NotificationStudent.objects.filter(student_id=student, is_read=False).update(is_read=True)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid request'})

def student_view_result(request):
    student = Students.objects.get(admin=request.user.id)
    studentresult = StudentResult.objects.filter(student_id=student)
    
    # Calculate totals
    total_marks = 0
    for result in studentresult:
        total_marks += (result.subject_assignment_marks or 0) + (result.subject_exam_marks or 0)
    
    max_marks = studentresult.count() * 100  # Assuming each subject is out of 100
    percentage = (total_marks / max_marks) * 100 if max_marks > 0 else 0
    
    return render(request, "student_template/student_view_result.html", {
        'student': student,
        'studentresult': studentresult,
        'total_marks': total_marks,
        'max_marks': max_marks,
        'percentage': round(percentage, 2)
    })

@require_POST
@login_required
def send_notification_reply(request):
    try:
        # Get POST data
        original_id = request.POST.get('original_notification_id')
        message = request.POST.get('message')
        
        if not message:
            return JsonResponse({
                'success': False,
                'message': 'Message cannot be empty'
            }, status=400)

        try:
            # Get original notification
            original = Notification.objects.get(
                id=original_id,
                receiver=request.user  # Ensure current user is the receiver
            )
            
            # Create reply by swapping sender and receiver
            Notification.objects.create(
                sender=request.user,
                receiver=original.sender,
                message=message,
                notification_type=original.notification_type,
                is_read=False
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Reply sent successfully'
            })
            
        except Notification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notification not found or you are not the recipient'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=500)