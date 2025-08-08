import os
import json
from uuid import uuid4
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
from django.db.models import Q
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from student_management_app.forms import EditResultForm
from .models import Notification
from django.db import IntegrityError

from student_management_app.models import Subjects,AdminHOD,Notification,Staffs, SessionYearModel, Students, Attendance, AttendanceReport, \
    LeaveReportStaff, Staffs, FeedBackStaffs, CustomUser, Courses, NotificationStaffs, StudentResult


def staff_home(request):
    #For Fetch All Student Under Staff
    subjects=Subjects.objects.filter(staff_id=request.user.id)
    course_id_list=[]
    for subject in subjects:
        course=Courses.objects.get(id=subject.course_id.id)
        course_id_list.append(course.id)

    final_course=[]
    #removing Duplicate Course ID
    for course_id in course_id_list:
        if course_id not in final_course:
            final_course.append(course_id)

    students_count=Students.objects.filter(course_id__in=final_course).count()

    #Fetch All Attendance Count
    attendance_count=Attendance.objects.filter(subject_id__in=subjects).count()

    #Fetch All Approve Leave
    staff=Staffs.objects.get(admin=request.user.id)
    leave_count=LeaveReportStaff.objects.filter(staff_id=staff.id,leave_status=1).count()
    subject_count=subjects.count()

    #Fetch Attendance Data by Subject
    subject_list=[]
    attendance_list=[]
    for subject in subjects:
        attendance_count1=Attendance.objects.filter(subject_id=subject.id).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count1)

    students_attendance=Students.objects.filter(course_id__in=final_course)
    student_list=[]
    student_list_attendance_present=[]
    student_list_attendance_absent=[]
    for student in students_attendance:
        attendance_present_count=AttendanceReport.objects.filter(status=True,student_id=student.id).count()
        attendance_absent_count=AttendanceReport.objects.filter(status=False,student_id=student.id).count()
        student_list.append(student.admin.username)
        student_list_attendance_present.append(attendance_present_count)
        student_list_attendance_absent.append(attendance_absent_count)

    return render(request,"staff_template/staff_home_template.html",{"students_count":students_count,"attendance_count":attendance_count,"leave_count":leave_count,"subject_count":subject_count,"subject_list":subject_list,"attendance_list":attendance_list,"student_list":student_list,"present_list":student_list_attendance_present,"absent_list":student_list_attendance_absent})


def view_student_attendance(request, student_id, subject_id):
    try:
        student = Students.objects.get(admin=student_id)
        subject = Subjects.objects.get(id=subject_id)
        
        # Get attendance records for this student and subject
        attendance_reports = AttendanceReport.objects.filter(
            student_id=student,
            attendance_id__subject_id=subject
        ).select_related('attendance_id')
        
        return render(request, "staff_template/student_attendance_template.html", {
            "student": student,
            "subject": subject,
            "attendance_reports": attendance_reports
        })
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('subject_students', subject_id=subject_id)

def view_student_result(request, student_id, subject_id):
    try:
        student = Students.objects.get(admin=student_id)
        subject = Subjects.objects.get(id=subject_id)
        
        # Check if result exists
        if StudentResult.objects.filter(student_id=student, subject_id=subject).exists():
            result = StudentResult.objects.get(student_id=student, subject_id=subject)
            return render(request, "staff_template/student_result_template.html", {
                "student": student,
                "subject": subject,
                "result": result,
                "has_result": True
            })
        else:
            messages.warning(request, "Result not yet assigned for this student")
            return render(request, "staff_template/student_result_template.html", {
                "student": student,
                "subject": subject,
                "has_result": False
            })
            
    except Students.DoesNotExist:
        messages.error(request, "Student not found")
        return redirect('subject_students', subject_id=subject_id)
    except Subjects.DoesNotExist:
        messages.error(request, "Subject not found")
        return redirect('total_subject')
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('subject_students', subject_id=subject_id)
    
    
from django.shortcuts import render
from django.utils import timezone
from student_management_app.models import Subjects, SessionYearModel

def staff_take_attendance(request):
    # Get subjects taught by this staff member
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    
    # Get current date in Nepal Timezone
    nepali_tz = pytz.timezone('Asia/Kathmandu')
    current_date_npt = timezone.now().astimezone(nepali_tz).date()
    
    # Get all available session years
    session_years = SessionYearModel.objects.all()
    
    # Format the time for display in the template
    current_time_npt = timezone.now().astimezone(nepali_tz)
    
    context = {
        "subjects": subjects,
        "session_years": session_years,
        'current_date': current_date_npt,  # Pass today's date to template
        'current_time': current_time_npt.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "NPT"
    }
    
    return render(request, "staff_template/staff_take_attendance.html", context)

@csrf_exempt
def get_students(request):
    subject_id=request.POST.get("subject")
    session_year=request.POST.get("session_year")

    subject=Subjects.objects.get(id=subject_id)
    session_model=SessionYearModel.objects.get(id=session_year)
    students=Students.objects.filter(course_id=subject.course_id,session_year_id=session_model)
    list_data=[]

    for student in students:
        data_small={"id":student.admin.id,"name":student.admin.first_name+" "+student.admin.last_name}
        list_data.append(data_small)
    return JsonResponse(json.dumps(list_data),content_type="application/json",safe=False)

from django.utils import timezone
import pytz
from datetime import datetime
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from student_management_app.models import Subjects, SessionYearModel, Students, Attendance, AttendanceReport

@csrf_exempt
def save_attendance_data(request):
    try:
        nepali_tz = pytz.timezone('Asia/Kathmandu')
        today = timezone.now().astimezone(nepali_tz).date()
        
        student_ids = request.POST.get("student_ids")
        subject_id = request.POST.get("subject_id")
        attendance_date_str = request.POST.get("attendance_date")
        session_year_id = request.POST.get("session_year_id")

        # Validate inputs
        if not all([student_ids, subject_id, attendance_date_str, session_year_id]):
            return JsonResponse({
                "status": "error",
                "message": "All fields are required"
            }, status=400)

        # Parse and validate date
        try:
            input_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
            if input_date != today:
                return JsonResponse({
                    "status": "error",
                    "message": f"Attendance can only be taken for today's date ({today})"
                }, status=400)
                
            # Create timezone-aware datetime at midnight Nepal time
            attendance_date = nepali_tz.localize(
                datetime.combine(input_date, datetime.min.time())
            )
        except ValueError:
            return JsonResponse({
                "status": "error",
                "message": "Invalid date format"
            }, status=400)

        subject = Subjects.objects.get(id=subject_id)
        session_year = SessionYearModel.objects.get(id=session_year_id)

        # Check for existing attendance
        existing_attendance = Attendance.objects.filter(
            subject_id=subject,
            attendance_date__date=today,
            session_year_id=session_year
        ).first()
        
        if existing_attendance:
            return JsonResponse({
                "status": "error",
                "message": f"Attendance for {subject.subject_name} is already taken for today"
            }, status=400)

        # Create attendance record
        attendance = Attendance(
            subject_id=subject,
            attendance_date=attendance_date,
            session_year_id=session_year
        )
        
        try:
            attendance.save()
        except IntegrityError as e:
            if 'duplicate' in str(e).lower():
                return JsonResponse({
                    "status": "error",
                    "message": f"Attendance for {subject.subject_name} is already taken for today"
                }, status=400)
            raise

        # Process student attendance
        saved_count = 0
        for student_data in json.loads(student_ids):
            student = Students.objects.get(admin=student_data['id'])
            AttendanceReport.objects.create(
                student_id=student,
                attendance_id=attendance,
                status=student_data['status']
            )
            saved_count += 1

        return JsonResponse({
            "status": "success",
            "message": f"Attendance saved for {saved_count} students",
            "date": str(today)
        })

    except Subjects.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Subject not found"}, status=404)
    except SessionYearModel.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Session year not found"}, status=404)
    except Students.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Student not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
    
def staff_update_attendance(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    return render(request, "staff_template/staff_update_attendance.html", {
        "subjects": subjects,
        "session_years": session_years
    })
    
@csrf_exempt
def get_attendance_history(request):
    if request.method == 'GET':
        try:
            subject_id = request.GET.get('subject_id')
            session_year_id = request.GET.get('session_year_id')
            
            print(f"DEBUG: Fetching history for subject_id={subject_id}, session_year_id={session_year_id}")
            
            # Get the staff user
            staff = Staffs.objects.get(admin=request.user)
            print(f"DEBUG: Staff ID: {staff.id}")
            
            # Get attendance records
            attendance_records = Attendance.objects.filter(
                subject_id=subject_id,
                session_year_id=session_year_id,
                subject_id__staff_id=staff.id
            ).select_related('subject_id', 'session_year_id').prefetch_related(
                'attendancereport_set__student_id__admin'
            )
            
            print(f"DEBUG: Found {attendance_records.count()} attendance records")
            
            data = []
            for record in attendance_records:
                reports = record.attendancereport_set.all()
                print(f"DEBUG: Record {record.id} has {reports.count()} reports")
                
                for report in reports:
                    data.append({
                        'date': record.attendance_date.strftime('%Y-%m-%d'),
                        'subject_name': record.subject_id.subject_name,
                        'student_name': report.student_id.admin.get_full_name(),
                        'roll_number': report.student_id.roll_number,
                        'status': report.status
                    })
            
            print(f"DEBUG: Returning {len(data)} records")
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
@csrf_exempt
def get_attendance_dates(request):
    subject=request.POST.get("subject")
    session_year_id=request.POST.get("session_year_id")
    subject_obj=Subjects.objects.get(id=subject)
    session_year_obj=SessionYearModel.objects.get(id=session_year_id)
    attendance=Attendance.objects.filter(subject_id=subject_obj,session_year_id=session_year_obj)
    attendance_obj=[]
    for attendance_single in attendance:
        data={"id":attendance_single.id,"attendance_date":str(attendance_single.attendance_date),"session_year_id":attendance_single.session_year_id.id}
        attendance_obj.append(data)

    return JsonResponse(json.dumps(attendance_obj),safe=False)

@csrf_exempt
def get_attendance_student(request):
    try:
        attendance_date_id = request.POST.get("attendance_date")
        if not attendance_date_id:
            return JsonResponse({'error': 'Attendance date ID is required'}, status=400)
        
        # Get the attendance record
        attendance = Attendance.objects.get(id=attendance_date_id)
        
        # Get all attendance reports for this attendance record
        attendance_reports = AttendanceReport.objects.filter(
            attendance_id=attendance
        ).select_related(
            'student_id__admin'
        )
        
        # Prepare the student data
        student_data = []
        for report in attendance_reports:
            student_data.append({
                "id": report.student_id.admin.id,
                "name": f"{report.student_id.admin.first_name} {report.student_id.admin.last_name}",
                "status": report.status,
                "roll_number": report.student_id.roll_number  # Add roll number if needed
            })
        
        return JsonResponse(student_data, safe=False)
        
    except Attendance.DoesNotExist:
        return JsonResponse({'error': 'Attendance record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def save_updateattendance_data(request):
    try:
        student_ids = request.POST.get("student_ids")
        attendance_date= request.POST.get("attendance_date")
        
        if not student_ids or not attendance_date:
            return JsonResponse({"status": "error", "message": "Missing required data"}, status=400)

        attendance = Attendance.objects.get(id=attendance_date)
        student_data = json.loads(student_ids)

        updated_count = 0
        for student in student_data:
            student_obj = Students.objects.get(admin=student['id'])
            report, created = AttendanceReport.objects.update_or_create(
                student_id=student_obj,
                attendance_id=attendance,
                defaults={'status': student['status'], 'updated_at': timezone.now()}
            )
            if not created:
                updated_count += 1

        return JsonResponse({
            "status": "success",
            "message": f"Updated {updated_count} attendance records",
            "updated_count": updated_count
        })

    except Attendance.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Attendance record not found"}, status=404)
    except Students.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Student not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    

def staff_apply_leave(request):
    staff_obj = Staffs.objects.get(admin=request.user.id)
    leave_data=LeaveReportStaff.objects.filter(staff_id=staff_obj)
    return render(request,"staff_template/staff_apply_leave.html",{"leave_data":leave_data})

def staff_apply_leave_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_apply_leave"))
    else:
        leave_date=request.POST.get("leave_date")
        leave_msg=request.POST.get("leave_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            leave_report=LeaveReportStaff(staff_id=staff_obj,leave_date=leave_date,leave_message=leave_msg,leave_status=0)
            leave_report.save()
            messages.success(request, "Successfully Applied for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))
        except:
            messages.error(request, "Failed To Apply for Leave")
            return HttpResponseRedirect(reverse("staff_apply_leave"))



    
def edit_student_result(request):
    if not request.user.is_authenticated:
        return redirect('login')

    staff_id = request.user.id
    
    if request.method == 'POST':
        form = EditResultForm(request.POST, staff_id=staff_id)
        if form.is_valid():
            try:
                student_id = form.cleaned_data['student_id']
                subject_id = form.cleaned_data['subject_id']
                
                # Debug print
                print(f"Attempting to save - Student: {student_id}, Subject: {subject_id}")
                print(f"Marks - Assignment: {form.cleaned_data['assignment_marks']}, Exam: {form.cleaned_data['exam_marks']}")
                
                student = Students.objects.get(admin=student_id)
                subject = Subjects.objects.get(id=subject_id)
                
                result, created = StudentResult.objects.update_or_create(
                    student_id=student,
                    subject_id=subject,
                    defaults={
                        'subject_assignment_marks': form.cleaned_data['assignment_marks'],
                        'subject_exam_marks': form.cleaned_data['exam_marks']
                    }
                )
                
                messages.success(request, "Result updated successfully!")
                return redirect('subject_wise_results')  # Ensure this redirect happens
                
            except Exception as e:
                print(f"Error saving result: {str(e)}")  # Debug print
                messages.error(request, f"Error saving result: {str(e)}")
        else:
            print("Form errors:", form.errors)  # Debug form validation errors
    else:
        form = EditResultForm(staff_id=staff_id)
    
    return render(request, "staff_template/edit_student_result.html", {'form': form})
        

def edit_student_result(request):
    if not request.user.is_authenticated:
        return redirect('login')

    staff_id = request.user.id
    
    if request.method == 'POST':
        form = EditResultForm(request.POST, staff_id=staff_id)
        if form.is_valid():
            try:
                student_id = form.cleaned_data['student_id']
                subject_id = form.cleaned_data['subject_id']
                
                student = Students.objects.get(admin=student_id)
                subject = Subjects.objects.get(id=subject_id)
                
                # Update or create result
                result, created = StudentResult.objects.update_or_create(
                    student_id=student,
                    subject_id=subject,
                    defaults={
                        'subject_assignment_marks': form.cleaned_data['assignment_marks'],
                        'subject_exam_marks': form.cleaned_data['exam_marks']
                    }
                )
                
                messages.success(request, "Result updated successfully!")
                return redirect('subject_wise_results')
                
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EditResultForm(staff_id=staff_id)
    
    return render(request, "staff_template/edit_student_result.html", {'form': form})
        
@csrf_exempt
def get_students_for_result(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        
        try:
            subject = Subjects.objects.get(id=subject_id)
            students = Students.objects.filter(course_id=subject.course_id)
            
            student_list = []
            for student in students:
                student_list.append({
                    'id': student.admin.id,
                    'name': f"{student.admin.first_name} {student.admin.last_name}"
                })
                
            return JsonResponse(json.dumps(student_list), safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({}, status=400)


@csrf_exempt
def fetch_student_result(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        
        try:
            student = Students.objects.get(admin=student_id)
            subject = Subjects.objects.get(id=subject_id)
            
            result_data = {'exists': False}
            if StudentResult.objects.filter(student_id=student, subject_id=subject).exists():
                result = StudentResult.objects.get(student_id=student, subject_id=subject)
                result_data = {
                    'exists': True,
                    'assignment_marks': result.subject_assignment_marks,
                    'exam_marks': result.subject_exam_marks
                }
                
            return JsonResponse(result_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({}, status=400)

def staff_feedback(request):
    staff_id=Staffs.objects.get(admin=request.user.id)
    feedback_data=FeedBackStaffs.objects.filter(staff_id=staff_id)
    return render(request,"staff_template/staff_feedback.html",{"feedback_data":feedback_data})

def staff_feedback_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("staff_feedback_save"))
    else:
        feedback_msg=request.POST.get("feedback_msg")

        staff_obj=Staffs.objects.get(admin=request.user.id)
        try:
            feedback=FeedBackStaffs(staff_id=staff_obj,feedback=feedback_msg,feedback_reply="")
            feedback.save()
            messages.success(request, "Successfully Sent Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        except:
            messages.error(request, "Failed To Send Feedback")
            return HttpResponseRedirect(reverse("staff_feedback"))
        

def total_subject(request):
    try:
        # Get the staff object for the current user
        staff = Staffs.objects.get(admin=request.user)
        
        # Filter subjects by staff's admin (CustomUser) field
        subjects = Subjects.objects.filter(staff_id=staff.admin)
        
        return render(request, "staff_template/total_subject_template.html", {
            "subjects": subjects,
            "staff": staff
        })
    except Staffs.DoesNotExist:
        messages.error(request, "Staff record not found")
        return redirect('staff_home')
    
    
def subject_students(request, subject_id):
    try:
        subject = Subjects.objects.get(id=subject_id)
        
        # Get students enrolled in the same course as the subject
        students = Students.objects.filter(course_id=subject.course_id)
        
        return render(request, "staff_template/subject_students_template.html", {
            "students": students,
            "subject": subject
        })
    except Subjects.DoesNotExist:
        messages.error(request, "Subject not found")
        return redirect('total_subject')
    
def staff_profile(request):
    user=CustomUser.objects.get(id=request.user.id)
    staff=Staffs.objects.get(admin=user)
    return render(request,"staff_template/staff_profile.html",{"user":user,"staff":staff})

def staff_profile_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("staff_profile"))
    
    try:
        # Get the current user and staff
        user = CustomUser.objects.get(id=request.user.id)
        staff = Staffs.objects.get(admin=user)
        
        # Update basic user info
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        
        # Handle password change if provided
        password = request.POST.get("password")
        if password and password.strip() != "":
            user.set_password(password)
        
        # Update staff-specific fields
        staff.address = request.POST.get("address", staff.address)
        staff.phone_number = request.POST.get("phone_number", staff.phone_number)
        staff.qualification = request.POST.get("qualification", staff.qualification)
        staff.specialization = request.POST.get("specialization", staff.specialization)
        staff.years_of_experience = request.POST.get("years_of_experience", staff.years_of_experience)
        
        # Handle profile picture upload
        if 'profile_pic' in request.FILES:
            # Delete old file if exists
            if staff.profile_pic:
                if os.path.exists(staff.profile_pic.path):
                    os.remove(staff.profile_pic.path)
            staff.profile_pic = request.FILES['profile_pic']
        
        # Handle profile picture removal
        if request.POST.get('remove_profile_pic') == 'true' and staff.profile_pic:
            if os.path.exists(staff.profile_pic.path):
                os.remove(staff.profile_pic.path)
            staff.profile_pic = None
        
        # Save both models
        user.save()
        staff.save()
        
        messages.success(request, "Profile Updated Successfully")
        return HttpResponseRedirect(reverse("staff_profile"))
        
    except Exception as e:
        messages.error(request, f"Failed to Update Profile: {str(e)}")
        return HttpResponseRedirect(reverse("staff_profile"))
    
    
    
@csrf_exempt
def staff_fcmtoken_save(request):
    token=request.POST.get("token")
    try:
        staff=Staffs.objects.get(admin=request.user.id)
        staff.fcm_token=token
        staff.save()
        return HttpResponse("True")
    except:
        return HttpResponse("False")

from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import NotificationStaffs

@login_required
def staff_all_notification(request):
    try:
        # Get staff profile
        staff = request.user.staff
        
        # Get base queryset
        notifications = NotificationStaffs.objects.filter(
            Q(staff=staff) | Q(created_by__isnull=False)
        ).order_by('-created_at')
        
        # Mark as read BEFORE pagination
        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)
        
        # Pagination (after marking as read)
        paginator = Paginator(notifications, 10)
        page_number = request.GET.get('page')
        try:
            notifications = paginator.page(page_number)
        except PageNotAnInteger:
            notifications = paginator.page(1)
        except EmptyPage:
            notifications = paginator.page(paginator.num_pages)
        
        return render(request, "staff_template/staff_all_notification.html", {
            "notifications": notifications
        })
        
    except Staffs.DoesNotExist:
        messages.error(request, "Staff profile not found")
        return redirect('staff_home')
    except Exception as e:
        messages.error(request, f"Error loading notifications: {str(e)}")
        return redirect('staff_home')
    
    
@csrf_exempt
def mark_staff_notifications_as_read(request):
    if request.method == 'POST':
        # Update all unread notifications for this staff member
        Notification.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def staff_add_result(request):
    subjects = Subjects.objects.filter(staff_id=request.user.id)
    session_years = SessionYearModel.objects.all()
    
    # Get student and subject  if they exist
    student_id = request.GET.get('student_id')
    subject_id = request.GET.get('subject_id')
    
    initial_data = {}
    if student_id and subject_id:
        try:
            initial_data = {
                'student_list': student_id,
                'subject': subject_id
            }
        except:
            pass
    
    return render(request, "staff_template/staff_add_result.html", {
        "subjects": subjects,
        "session_years": session_years,
        "initial_data": initial_data
    })
    

def save_student_result(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('staff_add_result'))
    
    try:
        # Get form data
        student_admin_id = request.POST.get('student_list')
        assignment_marks = request.POST.get('assignment_marks')
        exam_marks = request.POST.get('exam_marks')
        subject_id = request.POST.get('subject')
        
        # Convert marks to float
        assignment_marks = float(assignment_marks) if assignment_marks else 0
        exam_marks = float(exam_marks) if exam_marks else 0
        
        # Get objects
        student_obj = Students.objects.get(admin=student_admin_id)
        subject_obj = Subjects.objects.get(id=subject_id)
        
        # Validate marks
        if assignment_marks > subject_obj.internal_full_marks:
            messages.error(request, f"Assignment marks cannot exceed full marks ({subject_obj.internal_full_marks})")
            return HttpResponseRedirect(reverse("staff_add_result"))
            
        if exam_marks > subject_obj.exam_full_marks:
            messages.error(request, f"Exam marks cannot exceed full marks ({subject_obj.exam_full_marks})")
            return HttpResponseRedirect(reverse("staff_add_result"))
        
        # Check if result exists
        result, created = StudentResult.objects.get_or_create(
            subject_id=subject_obj,
            student_id=student_obj,
            defaults={
                'subject_assignment_marks': assignment_marks,
                'subject_exam_marks': exam_marks,
                'subject_internal_full_marks': subject_obj.internal_full_marks,
                'subject_exam_full_marks': subject_obj.exam_full_marks
            }   
        )
        
        if not created:
            result.subject_assignment_marks = assignment_marks
            result.subject_exam_marks = exam_marks
            result.save()
        
        messages.success(request, "Successfully Updated Result" if not created else "Successfully Added Result")
        return HttpResponseRedirect(reverse("staff_add_result"))
        
    except ValueError:
        messages.error(request, "Please enter valid numeric marks")
        return HttpResponseRedirect(reverse("staff_add_result"))
    except Students.DoesNotExist:
        messages.error(request, "Student not found")
        return HttpResponseRedirect(reverse("staff_add_result"))
    except Subjects.DoesNotExist:
        messages.error(request, "Subject not found")
        return HttpResponseRedirect(reverse("staff_add_result"))
    except Exception as e:
        messages.error(request, f"Failed to process result: {str(e)}")
        return HttpResponseRedirect(reverse("staff_add_result"))


@csrf_exempt
def get_students_for_result(request):
    print("get_students_for_result view called")  # Debug
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        print("Received subject_id:", subject_id)  # Debug
        
        try:
            subject = Subjects.objects.get(id=subject_id)
            print("Found subject:", subject.subject_name)  # Debug
            
            students = Students.objects.filter(course_id=subject.course_id)
            print("Found students count:", students.count())  # Debug
            
            student_list = []
            for student in students:
                student_list.append({
                    'id': student.admin.id,
                    'name': f"{student.admin.first_name} {student.admin.last_name}"
                })
                print(f"Added student: {student.admin.id}")  # Debug
                
            print("Returning student list:", student_list)  # Debug
            return JsonResponse(student_list, safe=False)
            
        except Subjects.DoesNotExist:
            print("Subject not found")  # Debug
            return JsonResponse([], safe=False)
        except Exception as e:
            print("Error:", str(e))  # Debug
            return JsonResponse({'error': str(e)}, status=400)
    
    print("Invalid request method")  # Debug
    return JsonResponse([], safe=False)

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse

def subject_wise_results(request):
    """
    View for displaying subject-wise results with filtering capability
    """
    try:
        staff_user = request.user
        subjects = Subjects.objects.filter(staff_id=staff_user).select_related('course_id')
        
        selected_subject_id = request.GET.get('subject')
        selected_subject = None
        results = []
        
        if selected_subject_id:
            try:
                selected_subject = Subjects.objects.get(id=selected_subject_id)
                results = StudentResult.objects.filter(
                    subject_id=selected_subject
                ).select_related(
                    'student_id__admin',
                    'subject_id',
                    'subject_id__course_id'
                ).order_by('student_id__admin__last_name', 'student_id__admin__first_name')
                
                # Calculate pass/fail status for each result
                for result in results:
                    result.total_marks = (result.subject_assignment_marks or 0) + (result.subject_exam_marks or 0)
                    result.status = 'Pass' if result.total_marks >= 40 else 'Fail'
                    result.grade= result.get_grade()
                
            except Subjects.DoesNotExist:
                messages.error(request, "Selected subject not found")
        
        context = {
            'subjects': subjects,
            'selected_subject': selected_subject,
            'selected_subject_id': int(selected_subject_id) if selected_subject_id else None,
            'results': results,
            'page_title': 'Subject Wise Results',
        }
        return render(request, "staff_template/subject_wise_results.html", context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while fetching results: {str(e)}")
        return redirect("staff_home")

def subject_wise_results_detail(request, subject_id):
    """
    Detailed view for a specific subject's results
    """
    try:
        subject = Subjects.objects.select_related('course_id').get(id=subject_id)
        results = StudentResult.objects.filter(
            subject_id=subject
        ).select_related(
            'student_id__admin',
            'subject_id'
        ).order_by('student_id__admin__last_name')
        
        # Add calculated fields
        for result in results:
            result.total_marks = (result.subject_assignment_marks or 0) + (result.subject_exam_marks or 0)
            result.grade = result.get_grade()
            result.status = 'Pass' if result.total_marks >= 40 else 'Fail'
        
        context = {
            'results': results,
            'subject': subject,
            'page_title': f'{subject.subject_name} - Detailed Results',
        }
        return render(request, "staff_template/subject_wise_results_detail.html", context)
    
    except Subjects.DoesNotExist:
        messages.error(request, "Requested subject not found")
        return redirect('subject_wise_results')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('staff_home')

@csrf_exempt
def fetch_result_student(request):
    """
    AJAX endpoint to fetch result data for a specific student and subject
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        subject_id = request.POST.get('subject_id')
        student_id = request.POST.get('student_id')
        
        if not subject_id or not student_id:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        student = Students.objects.get(admin=student_id)
        subject = Subjects.objects.get(id=subject_id)
        
        try:
            result = StudentResult.objects.get(
                student_id=student,
                subject_id=subject
            )
            
            response_data = {
                'success': True,
                'exam_marks': result.subject_exam_marks,
                'assign_marks': result.subject_assignment_marks,
                'internal_full_marks': getattr(subject, 'internal_full_marks', 20),  # Default to 20 if not set
                'exam_full_marks': getattr(subject, 'exam_full_marks', 80),        # Default to 80 if not set
                'total_marks': (result.subject_exam_marks or 0) + (result.subject_assignment_marks or 0),
                'grade': result.get_grade(),
                'status': 'Pass' if ((result.subject_exam_marks or 0) + (result.subject_assignment_marks or 0)) >= 40 else 'Fail'
            }
            return JsonResponse(response_data)
            
        except StudentResult.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Result not found for this student and subject'
            }, status=404)
            
    except Students.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Subjects.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def returnHtmlWidget(request):
    return render(request,"widget.html")


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
                'is_sender': notification.sender == user
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

def mark_notification_read(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            notification = Notification.objects.get(id=notification_id, receiver=request.user)
            notification.is_read = True
            notification.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def staff_send_reply(request):
    if request.method == 'POST':
        try:
            notification_id = request.POST.get('notification_id')
            recipient_id = request.POST.get('recipient_id')
            reply_message = request.POST.get('reply_message')
            
            # Get the original notification
            original_notification = Notification.objects.get(id=notification_id)
            
            # Create a new notification as a reply
            Notification.objects.create(
                admin_id=recipient_id,  # Send to admin
                staff_id=request.user.id,  # Sent by current staff
                message=f"Reply to your message '{original_notification.message[:30]}...': {reply_message}",
                created_at=timezone.now()
            )
            
            messages.success(request, "Reply sent successfully!")
            return redirect('staff_notifications')
            
        except Exception as e:
            messages.error(request, f"Failed to send reply: {str(e)}")
            return redirect('staff_notifications')
    
    return redirect('staff_notifications')


