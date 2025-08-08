from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Attendance, Courses, CustomUser,  Parents, SessionYearModel, Students, AttendanceReport, StudentResult, NotificationParents, Subjects, Parents, Subjects
from student_management_app.models import FeedBackParents, LeaveReportStudent
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def parent_home(request):   
        parent = Parents.objects.get(admin=request.user)
        student = parent.student_id
        
        # Attendance data
        attendance_total = AttendanceReport.objects.filter(student_id=student).count()
        attendance_present = AttendanceReport.objects.filter(student_id=student, status=True).count()
        attendance_absent = AttendanceReport.objects.filter(student_id=student, status=False).count()
        
        # Course and subjects data
        course = student.course_id  # Direct relation access
        subjects_count = Subjects.objects.filter(course_id=course).count()
        subjects_data = Subjects.objects.filter(course_id=course)
        session_obj = student.session_year_id
        
        
        # Attendance breakdown
        subject_stats = []
        for subject in subjects_data:
            attendance = Attendance.objects.filter(subject_id=subject.id)
            present = AttendanceReport.objects.filter(
                attendance_id__in=attendance,
                status=True,
                student_id=student.id
            ).count()
            absent = AttendanceReport.objects.filter(
                attendance_id__in=attendance,
                status=False,
                student_id=student.id
            ).count()
            
            subject_stats.append({
                'name': subject.subject_name,
                'present': present,
                'absent': absent
            })
        
        context = {
            'student': student,
            'total_attendance': attendance_total,
            'attendance_present': attendance_present,
            'attendance_absent': attendance_absent,
            'subjects_count': subjects_count,
            'subject_stats': subject_stats,
            'parent': parent,
            'results': StudentResult.objects.filter(student_id=student),
            'unread_notifications': NotificationParents.objects.filter(
                parent_id=parent,
                is_read=False
            ).count(),
        }

        return render(request, 'parent_template/parent_home_template.html', context)

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
        return render(request, 'parent_template/parent_profile.html', context)
        
    except Exception as e:
        messages.error(request, f"Error accessing parent profile: {str(e)}")
        return redirect('manage_parent')
    
def parent_profile(request):
    try:
        user = get_object_or_404(CustomUser, id=request.user.id)
        parent = get_object_or_404(Parents, admin=user)
        student = parent.student_id
        
        context = {
            'user': user,
            'parent': parent,
            'student': student
        }
        return render(request, "parent_template/parent_profile.html", context)
        
    except Exception as e:
        messages.error(request, f"Error accessing profile: {str(e)}")
        return redirect('parent_home')
    
def parent_all_notification(request):
    try:
        parent = Parents.objects.get(admin=request.user)
        notifications = NotificationParents.objects.filter(parent_id=parent).order_by('-created_at')
        return render(request, "parent_template/parent_all_notification.html", {
            "notifications": notifications
        })
    except Parents.DoesNotExist:
        messages.error(request, "Parent profile not found")
        return redirect('parent_home')
    
@login_required
def parent_view_result(request):
    # Get the parent and their associated student
    parent = Parents.objects.get(admin=request.user)
    student = parent.student_id
    
    # Get all results for the student
    student_results = StudentResult.objects.filter(student_id=student)
    
    # Calculate totals
    total_marks = 0
    total_assignment = 0
    total_exam = 0
    
    for result in student_results:
        total_assignment += result.subject_assignment_marks or 0
        total_exam += result.subject_exam_marks or 0
        total_marks += (result.subject_assignment_marks or 0) + (result.subject_exam_marks or 0)
    
    # Calculate performance metrics
    max_marks_per_subject = 100  # Assuming each subject is out of 100
    max_marks = student_results.count() * max_marks_per_subject if student_results.exists() else 0
    percentage = (total_marks / max_marks) * 100 if max_marks > 0 else 0
    
    # Determine overall grade based on percentage
    if percentage >= 90:
        overall_grade = 'A+'
    elif percentage >= 80:
        overall_grade = 'A'
    elif percentage >= 70:
        overall_grade = 'B+'
    elif percentage >= 60:
        overall_grade = 'B'
    elif percentage >= 50:
        overall_grade = 'C+'
    elif percentage >= 40:
        overall_grade = 'C'
    else:
        overall_grade = 'F'
    
    context = {
        'parent': parent,
        'student': student,
        'student_results': student_results,
        'total_assignment': total_assignment,
        'total_exam': total_exam,
        'total_marks': total_marks,
        'max_marks': max_marks,
        'percentage': round(percentage, 2),
        'overall_grade': overall_grade,
        'overall_performance': "Excellent" if overall_grade == 'A+' else
                              "Very Good" if overall_grade == 'A' else
                              "Good" if overall_grade == 'B+' else
                              "Average" if overall_grade == 'B' else
                              "Below Average" if overall_grade == 'C+' else
                              "Needs Improvement"
    }
    
    return render(request, "parent_template/parent_view_result.html", context)

def parent_feedback(request):
    parent_id=Parents.objects.get(admin=request.user.id)
    feedback_data=FeedBackParents.objects.filter(parent_id=parent_id)
    return render(request,"parent_template/parent_feedback.html",{"feedback_data":feedback_data})

def parent_feedback_save(request):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("parent_feedback"))
    
    feedback_msg = request.POST.get("feedback_msg")
    
    try:
        # Get the parent object for the current user
        parent = Parents.objects.get(admin=request.user)
        
        # Create feedback with the parent object
        feedback = FeedBackParents(
            parent_id=parent,
            feedback=feedback_msg,
            feedback_reply=""
        )
        feedback.save()
        
        messages.success(request, "Successfully Sent Feedback")
        return HttpResponseRedirect(reverse("parent_feedback"))
        
    except Parents.DoesNotExist:
        messages.error(request, "Parent profile not found")
        return HttpResponseRedirect(reverse("parent_feedback"))
    except Exception as e:
        messages.error(request, f"Failed To Send Feedback: {str(e)}")
        return HttpResponseRedirect(reverse("parent_feedback"))

def parent_view_result_post(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        parent = Parents.objects.get(admin=request.user)
        student = Students.objects.get(id=student_id, course_id=parent.student_id.course_id)
        results = StudentResult.objects.filter(student_id=student)
        
        context = {
            'results': results,
            'student': student
        }
        return render(request, 'parent_template/student_result.html')
    else:
        return redirect('parent_home')


    
@login_required
def manage_children(request):
    parent = Parents.objects.get(admin=request.user)
    children = Students.objects.filter(course_id=parent.student_id.course_id)
    
    context = {
        'children': children,
        'parent': parent
    }
    return render(request, 'parent_template/manage_children.html', context)
    
# @login_required
# def parent_feedback(request):
#     parent = Parents.objects.get(admin=request.user)
    
#     if request.method == 'POST':
#         feedback = request.POST.get('feedback')
#         try:
#             FeedBackParents.objects.create(
#                 parent_id=parent,
#                 feedback=feedback,
#                 feedback_reply=""
#             )
#             messages.success(request, "Feedback sent successfully!")
#             return redirect('parent_feedback')
#         except:
#             messages.error(request, "Failed to send feedback!")
    
#     feedbacks = FeedBackParents.objects.filter(parent_id=parent)
#     context = {
#         'feedbacks': feedbacks
#     }
#     return render(request, 'parent_template/parent_feedback.html', context)

@login_required
def parent_notification(request):
    parent = Parents.objects.get(admin=request.user)
    notifications = NotificationParents.objects.filter(parent_id=parent).order_by('-created_at')
    
    # Mark notifications as read when viewed
    notifications.update(is_read=True)
    
    context = {
        'notifications': notifications
    }
    return render(request, 'parent_template/parent_notification.html', context)

@login_required
def apply_student_leave(request):
    parent = Parents.objects.get(admin=request.user)
    student = parent.student_id
    
    if request.method == 'POST':
        leave_date = request.POST.get('leave_date')
        leave_message = request.POST.get('leave_message')
        
        try:
            LeaveReportStudent.objects.create(
                student_id=student,
                leave_date=leave_date,
                leave_message=leave_message,
                leave_status=0  # 0 for pending
            )
            messages.success(request, "Leave application submitted successfully!")
            return redirect('apply_student_leave')
        except:
            messages.error(request, "Failed to submit leave application!")
    
    leave_reports = LeaveReportStudent.objects.filter(student_id=student)
    context = {
        'leave_reports': leave_reports
    }
    return render(request, 'parent_template/apply_student_leave.html', context)

@login_required
def get_student_details(request):
    parent = Parents.objects.get(admin=request.user)
    student = parent.student_id
    
    data = {
        'full_name': student.admin.get_full_name(),
        'email': student.admin.email,
        'course': student.course_id.course_name,
        'session_year': f"{student.session_year_id.session_start_year.year}-{student.session_year_id.session_end_year.year}",
        'gender': student.gender,
        'address': student.address,
        'profile_pic_url': student.profile_pic.url if student.profile_pic else None
    }
    
    return JsonResponse(data)


def parent_profile_save(request):
    if request.method!="POST":
        return HttpResponseRedirect(reverse("parent_profile"))
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

            parent=Parents.objects.get(admin=customuser)
            parent.address=address
            parent.save()
            messages.success(request, "Successfully Updated Profile")
            return HttpResponseRedirect(reverse("parent_profile"))
        except:
            messages.error(request, "Failed to Update Profile")
            return HttpResponseRedirect(reverse("parent_profile"))
        
@login_required
def parent_manage_children(request):
    try:
        parent = Parents.objects.get(admin=request.user)
        child = parent.student_id
        
        # Get additional data for the single template
        attendance = AttendanceReport.objects.filter(
    student_id=child
).select_related('attendance_id').order_by('-attendance_id__attendance_date')[:5]
        
        results = StudentResult.objects.filter(
            student_id=child
        ).select_related('subject_id').order_by('-id')

        context = {
            'child': child,
            'attendance': attendance,
            'results': results,
            'children_count': 1 if child else 0
        }
        return render(request, 'parent_template/manage_children.html', context)
        
    except Parents.DoesNotExist:
        messages.error(request, "Parent profile not found")
        return redirect('parent_home')


@login_required
def parent_view_attendance_post(request):
    if request.method != 'POST':
        return redirect('parent_view_attendance')  # Redirect back if not POST
    
    try:
        parent = Parents.objects.get(admin=request.user)
        student = parent.student_id
        
        subject_id = request.POST.get('subject')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Parse dates and validate
        # ... (your existing date parsing logic)

        # Get filtered attendance
        attendance_reports = AttendanceReport.objects.filter(
            student_id=student
        ).select_related('attendance_id__subject_id')

        if subject_id:
            attendance_reports = attendance_reports.filter(
                attendance_id__subject_id=subject_id
            )

        if start_date:
            attendance_reports = attendance_reports.filter(
                attendance_id__attendance_date__gte=start_date
            )

        if end_date:
            attendance_reports = attendance_reports.filter(
                attendance_id__attendance_date__lte=end_date
            )

        present_count = attendance_reports.filter(status=True).count()
        absent_count = attendance_reports.filter(status=False).count()

        # RENDER THE TEMPLATE WITH DATA (DON'T REDIRECT)
        return render(request, 'parent_template/parent_view_attendance.html', {
            'attendance_reports': attendance_reports,
            'student': student,
            'subjects': Subjects.objects.filter(course_id=student.course_id),
            'selected_subject': int(subject_id) if subject_id else None,
            'start_date': start_date,
            'end_date': end_date,
            'present_count': present_count,
            'absent_count': absent_count,
        })

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('parent_view_attendance')
    

@login_required
def parent_view_attendance(request):
    try:
        parent = Parents.objects.get(admin=request.user)
        student = parent.student_id
        
        # Get last 15 attendance records
        attendance = AttendanceReport.objects.filter(
            student_id=student
        ).select_related('attendance_id__subject_id').order_by('-attendance_id__attendance_date')[:36]
        
        context = {
            'attendance': attendance,
            'student': student
        }
        return render(request, 'parent_template/parent_view_attendance.html', context)
        
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('parent_home')