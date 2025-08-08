from django.db.models import Value
Value(None)
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator


# Session year model
class SessionYearModel(models.Model):
    id = models.AutoField(primary_key=True)
    session_start_year = models.DateField()
    session_end_year = models.DateField()
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.session_start_year} to {self.session_end_year}"


# Custom user model
class CustomUser(AbstractUser):
    # your custom fields here
    user_type_data = ((1, "HOD"), (2, "Staff"), (3, "Student"), (4, "Parent"))
    user_type = models.CharField(default=1, choices=user_type_data, max_length=10)


class AdminHOD(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    gender=models.CharField(max_length=255, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    def _str_(self):
        return f"{self.admin.username} (Admin)"

class Staffs(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff')
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.FileField(upload_to='profile_pics/', blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    gender=models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fcm_token = models.TextField(null=True, blank=True)
    objects = models.Manager()

    @property
    def full_name(self):
        name_parts = []
        if self.admin.first_name:
            name_parts.append(self.admin.first_name)
        if self.admin.last_name:
            name_parts.append(self.admin.last_name)
        return ' '.join(name_parts)
    


class Courses(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255, default="Unknown Course")  # ✅ Default added
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    staff = models.ForeignKey(Staffs, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    objects = models.Manager()
    
    def __str__(self):
        return self.course_name


class Subjects(models.Model):
    id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=100, default="Unknown Subject")  # ✅ Default added
    course_id = models.ForeignKey(Courses, on_delete=models.CASCADE)
    internal_full_marks = models.FloatField(default=20)  # Default assignment marks
    exam_full_marks = models.FloatField(default=80)  
    staff_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class Students(models.Model):
    id=models.AutoField(primary_key=True)
    admin=models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    gender=models.CharField(max_length=255)
    profile_pic=models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number=models.BigIntegerField(null=True, blank=True, validators=[
            MinValueValidator(1000000000),  # Ensures minimum 10 digits
            MaxValueValidator(9999999999)   # Ensures maximum 10 digits
        ])
    roll_number=models.IntegerField(
        unique=True,
        help_text="Unique numeric roll number for the student")
    address=models.TextField()
    course_id=models.ForeignKey(Courses,on_delete=models.DO_NOTHING)
    session_year_id=models.ForeignKey(SessionYearModel,on_delete=models.CASCADE, related_name='students')
    created_at=models.DateTimeField(auto_now_add=True)
    
    updated_at=models.DateTimeField(auto_now_add=True)
    fcm_token=models.TextField(default="")
    objects = models.Manager()
    # In your Students model
def get_unread_notification_count(self):
    return NotificationStudent.objects.filter(student_id=self, is_read=False).count()
    def _str_(self):
        # Display student's full name from related CustomUser model
        return self.admin.get_full_name() or self.admin.username

class Parents(models.Model):
    id = models.AutoField(primary_key=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.BigIntegerField(  # Add this field
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000000000),
            MaxValueValidator(9999999999)
        ]
    )
    address = models.TextField()
    student_id = models.ForeignKey(
        Students, 
        on_delete=models.CASCADE,
        related_name='parents',
        null=True,
        blank=True
    )
    relationship = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    def _str_(self):
        return f"{self.name} ({self.relationship} of {self.student_id.admin.get_full_name()})"
    def get_unread_notification_count(self):
        return self.notificationparents_set.filter(is_read=False).count()
    

class Attendance(models.Model):
    id = models.AutoField(primary_key=True)
    subject_id = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    attendance_date = models.DateTimeField()  # Remove default, handle in save()
    session_year_id = models.ForeignKey(SessionYearModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    
    class Meta:
        unique_together = ('subject_id', 'attendance_date', 'session_year_id')
    
    def save(self, *args, **kwargs):
        # Ensure TIME_ZONE = 'Asia/Kathmandu' is set in settings.py
        if not self.attendance_date:
            self.attendance_date = timezone.now()
        elif not timezone.is_aware(self.attendance_date):
            self.attendance_date = timezone.make_aware(self.attendance_date)
        super().save(*args, **kwargs)


class AttendanceReport(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.DO_NOTHING, related_name='attendance_reports')
    attendance_id = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class LeaveReportStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=200)
    leave_message = models.TextField()
    leave_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class LeaveReportStaff(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    leave_date = models.CharField(max_length=200)
    leave_message = models.TextField()
    leave_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class FeedBackStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()


class FeedBackStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff_id = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

class FeedBackParents(models.Model):
    id = models.AutoField(primary_key=True)
    parent_id = models.ForeignKey(Parents, on_delete=models.CASCADE)
    feedback = models.TextField()
    feedback_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        (1, 'Student'),
        (2, 'Staff'),
        (3, 'Admin'),
        (4,'parent')
    )
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_notifications')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.IntegerField(choices=NOTIFICATION_TYPES)
    
    class Meta:
        ordering = ['-created_at']
    
    def _str_(self):
        return f"Notification from {self.sender.username} to {self.receiver.username}"
    

class NotificationStudent(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_status = models.BooleanField(default=False)
    admin_id = models.ForeignKey(AdminHOD, on_delete=models.CASCADE, null=True)
    objects = models.Manager()
    def __str__(self):
        return self.message
    def __str__(self):
        return f"Notification for {self.student_id.admin.username}"


class NotificationStaffs(models.Model):
    id = models.AutoField(primary_key=True)
    staff = models.ForeignKey(Staffs, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    is_read = models.BooleanField(default=False)
    objects = models.Manager()
    def __str__(self):
        return f"Notification for {self.staff.admin.username}"
    @property
    def sender(self):
        return self.admin or self.staff.admin if self.staff else None

class NotificationParents(models.Model):
    id = models.AutoField(primary_key=True)
    parent_id = models.ForeignKey(Parents, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # New field to track read status
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()
    @property
    def unread_notification_count(self):
        return self.notificationparents_set.filter(is_read=False).count()
    
class StudentResult(models.Model):
    student_id = models.ForeignKey(Students, on_delete=models.CASCADE)
    subject_id = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    subject_exam_marks = models.FloatField(default=0)
    subject_assignment_marks = models.FloatField(default=0)
    subject_internal_full_marks = models.FloatField(default=0)
    subject_exam_full_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add these methods inside the class
    def get_total_marks(self):
        """Calculate total marks by adding assignment and exam marks"""
        return (self.subject_assignment_marks or 0) + (self.subject_exam_marks or 0)

    def get_grade(self):
        """Calculate grade based on total marks"""
        total = self.get_total_marks()
        if total >= 90: return 'A'
        elif total >= 80: return 'B'
        elif total >= 70: return 'C'
        elif total >= 60: return 'D'
        else: return 'F'

    def _str_(self):
        return f"{self.student_id.admin.username} - {self.subject_id.subject_name}"

    class Meta:
        unique_together = ('student_id', 'subject_id')
        
def get_grade(self):
    total = self.get_total_marks()
    if total >= 90: return 'A'
    elif total >= 80: return 'B'
    elif total >= 70: return 'C'
    elif total >= 60: return 'D'
    else: return 'F'


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == '1':
            AdminHOD.objects.create(admin=instance)
        elif instance.user_type == '2':
            Staffs.objects.create(admin=instance, address="")
        elif instance.user_type == '3':
            Students.objects.create(
                admin=instance,
                course_id=Courses.objects.first(),  # Safely get first course
                session_year_id=SessionYearModel.objects.first(),  # Safely get first session
                address="",
                profile_pic=None,
                gender=""
            )
        elif instance.user_type == '4':
            Parents.objects.create(
                admin=instance,
                name=f"{instance.first_name} {instance.last_name}",
                email=instance.email,
                phone_number=None,
                address="",
                student_id=None,
                relationship="Parent",
                profile_pic=None  # fix: don't pass an invalid empty string
            )


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == '1' and hasattr(instance, 'adminhod'):
        instance.adminhod.save()
    elif instance.user_type == '2' and hasattr(instance, 'staffs'):
        instance.staffs.save()
    elif instance.user_type == '3' and hasattr(instance, 'students'):
        instance.students.save()
    elif instance.user_type == '4' and hasattr(instance, 'parents'):
        instance.parents.save()