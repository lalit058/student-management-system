from django import forms
from django.forms import ChoiceField, ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django import forms
from django.forms import ChoiceField
import re

from student_management_app.models import Courses, AdminHOD, SessionYearModel, Subjects
from .models import CustomUser, Parents, Staffs

from student_management_app.models import Courses, SessionYearModel, Subjects, Students, CustomUser

class ChoiceNoValidation(ChoiceField):
    def validate(self, value):
        pass

class DateInput(forms.DateInput):
    input_type = "date"

class AddStudentForm(forms.Form):
    first_name=forms.CharField(
        label="First Name",
        max_length=50,
        widget=forms.TextInput(attrs={
            "class":"form-control",
            "placeholder":"First Name",
            "required": "required"
            })
        )
    
    last_name=forms.CharField(
        label="Last Name",
        max_length=50,
        widget=forms.TextInput(attrs={
            "placeholder":"Last Name",
            "class":"form-control",
            "required": "required"
            })
        )
    
    username = forms.CharField(
        label="Username",
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder":"Username",
            "autocomplete": "off",
            "hx-post": "/check_username/",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#username-error",
            "required": "required",
            "pattern": "^[a-zA-Z0-9_]{4,20}$",
            "title": "Username must be 4-20 characters (letters, numbers, underscore)",
            "oninput": "validateUsername(this)"
        }),
        help_text="4-20 characters (letters, numbers, underscore)"
    )
    
    roll_number = forms.IntegerField(
        label="Roll Number",
        widget=forms.NumberInput(attrs={
            
            "class": "form-control",
            "autocomplete": "off",
            "placeholder": "Enter a student roll number",
            "min": "1"  # HTML5 validation
        }),
        required=True,  # Changed from False to True
        validators=[
            MinValueValidator(1)  # Django validation
        ],
        error_messages={
            'required': 'Roll number is required',
            'invalid': 'Enter a valid numeric roll number',
            'min_value': 'Roll number must be at least 1'
        }
    )
    
    address=forms.CharField(
        label="Address",
        max_length=50,
        widget=forms.TextInput(attrs={
            "class":"form-control"
            })
        )
    
    email = forms.EmailField(
        label="Email",
        max_length=50,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "autocomplete": "off",
            "placeholder": "Enter valid email address",
            "required": "required",
            "hx-post": "/check_email/",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#email-error",
            "oninput": "validateEmail(this)"
        }),
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Enter a valid email address'
        }
    )
    
    
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "98XXXXXXXX",
            "pattern": "[0-9]{10}",
            "title": "Numbers only 10 digits",
            "required": "required",
            "hx-post": "/check_phone/",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#phone-error",
            "oninput": "validatePhone(this)"
        }),
        error_messages={
            'required': 'Phone number is required',
        }
    )
    
    course_list=[]
    try:
        courses=Courses.objects.all()
        for course in courses:
            small_course=(course.id,course.course_name)
            course_list.append(small_course)
    except:
        course_list=[]
    #course_list=[]

    session_list = []
    try:
        sessions = SessionYearModel.objects.all()

        for ses in sessions:
            small_ses = (ses.id, str(ses.session_start_year)+"   TO  "+str(ses.session_end_year))
            session_list.append(small_ses)
    except:
        session_list=[]

    gender_choice=(
        ("select gender", "select gender"),
        ("Male","Male"),
        ("Female","Female"),
        ("Others", "Others")
    )

    course=forms.ChoiceField(
        label="Course",
        choices=course_list,
        widget=forms.Select(attrs={
            "class":"form-control",
            "required": "required"
            })
        )
    
    gender=forms.ChoiceField(
        label="Gender",
        choices=gender_choice,
        widget=forms.Select(attrs={
            "class":"form-control"
            })
        )
    session_year_id=forms.ChoiceField(
        label="Session Year",
        choices=session_list,
        widget=forms.Select(attrs={
            "class":"form-control"
            })
        )
    profile_pic=forms.FileField(
        label="Profile Pic",
        max_length=50,
        widget=forms.FileInput(attrs={
            "class":"form-control"
            }), 
        required=True
        )
    
    password = forms.CharField(
        label="Password",
        max_length=50,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "required": "required",
            "pattern": "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
            "title": "Password must contain: 8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 special character",
            "oninput": "validatePassword(this)",
            "hx-post": "/validate_password/",
            "hx-trigger": "keyup changed delay:500ms",
            "hx-target": "#password-strength"
        }),
        help_text="Must contain: 8+ chars, 1 uppercase, 1 lowercase, 1 number, 1 special character (@$!%*?&)"
    )
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
            raise forms.ValidationError("Username must be 4-20 characters (letters, numbers, underscore only)")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists. Please choose a different one.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            raise forms.ValidationError(
                "Password must contain at least 8 characters including: "
                "1 uppercase, 1 lowercase, 1 number, and 1 special character (@$!%*?&)"
            )
        return password

class EditResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.staff_id = kwargs.pop('staff_id', None)
        super(EditResultForm, self).__init__(*args, **kwargs)
        
        # Get subjects taught by this staff
        subject_list = []
        try:
            subjects = Subjects.objects.filter(staff_id=self.staff_id)
            subject_list = [(subject.id, subject.subject_name) for subject in subjects]
        except:
            subject_list = []
        
        self.fields['subject_id'] = forms.ChoiceField(
            label="Subject",
            choices=[('', 'Select Subject')] + subject_list,
            widget=forms.Select(attrs={"class": "form-control"})
        )
        
        # Visible student field - disable Django's choice validation
        self.fields['student_id'] = forms.CharField(
            label="Student",
            widget=forms.Select(attrs={"class": "form-control"}),
            required=True
        )
        
        self.fields['assignment_marks'] = forms.CharField(
            label="Assignment Marks",
            widget=forms.NumberInput(attrs={"class": "form-control"})
        )
        
        self.fields['exam_marks'] = forms.CharField(
            label="Exam Marks",
            widget=forms.NumberInput(attrs={"class": "form-control"})
        )

    def clean(self):
        cleaned_data = super().clean()
        # Manually validate student_id exists
        student_id = cleaned_data.get('student_id')
        if not student_id:
            raise forms.ValidationError("Please select a student")
        try:
            Students.objects.get(admin=student_id)
        except Students.DoesNotExist:
            raise forms.ValidationError("Selected student does not exist")
        return cleaned_data

class AddParentForm(forms.Form):
    # User Account Fields
    email = forms.EmailField(
        label="Email", 
        max_length=50, 
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "autocomplete": "off"
        }) 
    )
    password = forms.CharField(
        label="Password", 
        max_length=50, 
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )
    first_name = forms.CharField(
        label="First Name", 
        max_length=50, 
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )
    last_name = forms.CharField(
        label="Last Name", 
        max_length=50, 
        widget=forms.TextInput(attrs={
            "class": "form-control"
        })
    )
    username = forms.CharField(
        label="Username", 
        max_length=50, 
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "autocomplete": "off"
        })
    )
    
    profile_pic = forms.FileField(
        label="Profile Picture",
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": "image/*"
        })
    )

    # Parent Specific Fields
    phone_number = forms.IntegerField(
        label="Phone Number",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1000000000',
            'max': '9999999999',
            'oninput': "this.value=this.value.slice(0,10)"
        }),
        validators=[
            MinValueValidator(1000000000),
            MaxValueValidator(9999999999),
            RegexValidator(
                regex='^[0-9]{10}$',
                message='Phone number must be exactly 10 digits',
                code='invalid_phone'
            )
        ]
    )
    address = forms.CharField(
        label="Address",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3
        })
    )
    relationship = forms.ChoiceField(
        label="Relationship",
        choices=(
            ("Father", "Father"),
            ("Mother", "Mother"),
            ("Guardian", "Guardian"),
            ("Other", "Other")
        ),
        widget=forms.Select(attrs={
            "class": "form-control"
        })
    )
    # Student Selection
    student_id = forms.ModelChoiceField(
        queryset=Students.objects.all(),
        label="Student",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Parents.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and Parents.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Phone number already registered.")
        return phone_number
    
    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
    
        if phone_number and len(str(phone_number)) != 10:
         raise forms.ValidationError("Phone number must be 10 digits")
        # Add any additional cross-field validation here
        return cleaned_data
    
class EditStudentForm(forms.Form):
    email=forms.EmailField(label="Email",max_length=50,widget=forms.EmailInput(attrs={"class":"form-control"}))
    first_name=forms.CharField(label="First Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    last_name=forms.CharField(label="Last Name",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    username=forms.CharField(label="Username",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    address=forms.CharField(label="Address",max_length=50,widget=forms.TextInput(attrs={"class":"form-control"}))
    phone_number=forms.CharField(label ="phone_number", max_length=10,widget=forms.TextInput(attrs={"class":"form-control"}))
    course_list=[]
    try:
        courses = Courses.objects.all()
        for course in courses:
            small_course=(course.id,course.course_name)
            course_list.append(small_course)
    except:
        course_list=[]

    session_list = []
    try:
        sessions = SessionYearModel.objects.all()

        for ses in sessions:
            small_ses = (ses.id, str(ses.session_start_year)+"   TO  "+str(ses.session_end_year))
            session_list.append(small_ses)
    except:
        pass
        #session_list = []

    gender_choice=(
        ("select gender", "select gender"),
        ("Male","Male"),
        ("Female","Female"),
        ("Others", "Others")
    )
    
    gender=forms.ChoiceField(
        label="Gender",
        choices=gender_choice,
        widget=forms.Select(attrs={
            "class":"form-control"
            })
        )
    
    roll_number = forms.IntegerField(
        label="Roll Number",
        widget=forms.NumberInput(attrs={
            
            "class": "form-control",
            "autocomplete": "off",
            "placeholder": "Enter a student roll number",
            "min": "1"  # HTML5 validation
        }),
        required=True,  # Changed from False to True
        validators=[
            MinValueValidator(1)  # Django validation
        ],
        error_messages={
            'required': 'Roll number is required',
            'invalid': 'Enter a valid numeric roll number',
            'min_value': 'Roll number must be at least 1'
        }
    )

    course=forms.ChoiceField(label="Course",choices=course_list,widget=forms.Select(attrs={"class":"form-control"}))
    session_year_id=forms.ChoiceField(label="Session Year",choices=session_list,widget=forms.Select(attrs={"class":"form-control"}))
    profile_pic=forms.FileField(label="Profile Pic",max_length=50,widget=forms.FileInput(attrs={"class":"form-control"}),required=False)

class CustomStaffCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    profile_pic = forms.FileField(label="Profile Pic", max_length=50, widget=forms.FileInput(attrs={"class":"form-control"}))
    
    # New qualification fields
    qualification = forms.CharField(
        max_length=255, 
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Highest academic qualification (e.g., PhD, Masters, BSc)"
    )
    specialization = forms.CharField(
        max_length=255, 
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        help_text="Area of specialization"
    )
    years_of_experience = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        min_value=0,
        help_text="Total years of teaching experience"
    )
    joining_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Date of joining the institution"
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    # ... keep existing clean methods ...

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.user_type = 2  # Staff
        if commit:
            user.save()
            # Create staff profile with additional fields
            Staffs.objects.create(
                admin=user,
                address=self.cleaned_data['address'],
                phone_number=self.cleaned_data['phone_number'],
                profile_pic=self.cleaned_data['profile_pic'],
                qualification=self.cleaned_data['qualification'],
                specialization=self.cleaned_data['specialization'],
                years_of_experience=self.cleaned_data['years_of_experience'],
                joining_date=self.cleaned_data['joining_date']
            )
        return user