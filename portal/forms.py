from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile, FacultyProfile

BRANCH_CHOICES = [
    ('', 'Select Department/Branch'),
    ('Core Engineering Branches', (
        ('Civil Engineering', 'Civil Engineering'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Electronics and Communication Engineering', 'Electronics and Communication Engineering'),
        ('Computer Science and Engineering', 'Computer Science and Engineering'),
        ('Chemical Engineering', 'Chemical Engineering'),
    )),
    ('Computer Science & IT Specializations', (
        ('Information Technology', 'Information Technology'),
        ('Artificial Intelligence and Machine Learning', 'Artificial Intelligence and Machine Learning'),
        ('Artificial Intelligence and Data Science', 'Artificial Intelligence and Data Science'),
        ('Data Science', 'Data Science'),
        ('Cybersecurity Engineering', 'Cybersecurity Engineering'),
        ('Software Engineering', 'Software Engineering'),
        ('Cloud Computing', 'Cloud Computing'),
        ('Internet of Things (IoT) Engineering', 'Internet of Things (IoT) Engineering'),
    )),
    ('Electrical, Electronics & Robotics', (
        ('Electronics Engineering', 'Electronics Engineering'),
        ('Electrical and Electronics Engineering', 'Electrical and Electronics Engineering'),
        ('Instrumentation Engineering', 'Instrumentation Engineering'),
        ('Biomedical Engineering', 'Biomedical Engineering'),
        ('Robotics Engineering', 'Robotics Engineering'),
        ('Automation Engineering', 'Automation Engineering'),
    )),
    ('Mechanical, Aerospace & Production', (
        ('Automobile Engineering', 'Automobile Engineering'),
        ('Industrial Engineering', 'Industrial Engineering'),
        ('Production Engineering', 'Production Engineering'),
        ('Manufacturing Engineering', 'Manufacturing Engineering'),
        ('Mechatronics Engineering', 'Mechatronics Engineering'),
        ('Aerospace Engineering', 'Aerospace Engineering'),
        ('Aeronautical Engineering', 'Aeronautical Engineering'),
        ('Marine Engineering', 'Marine Engineering'),
    )),
    ('Civil & Infrastructure Specializations', (
        ('Structural Engineering', 'Structural Engineering'),
        ('Environmental Engineering', 'Environmental Engineering'),
        ('Transportation Engineering', 'Transportation Engineering'),
        ('Construction Engineering', 'Construction Engineering'),
        ('Geotechnical Engineering', 'Geotechnical Engineering'),
        ('Water Resources Engineering', 'Water Resources Engineering'),
    )),
    ('Chemical, Materials & Process Engineering', (
        ('Petroleum Engineering', 'Petroleum Engineering'),
        ('Materials Engineering', 'Materials Engineering'),
        ('Metallurgical Engineering', 'Metallurgical Engineering'),
        ('Polymer Engineering', 'Polymer Engineering'),
        ('Ceramic Engineering', 'Ceramic Engineering'),
        ('Food Engineering', 'Food Engineering'),
        ('Biochemical Engineering', 'Biochemical Engineering'),
    )),
    ('Energy & Environmental Engineering', (
        ('Energy Engineering', 'Energy Engineering'),
        ('Renewable Energy Engineering', 'Renewable Energy Engineering'),
        ('Nuclear Engineering', 'Nuclear Engineering'),
        ('Mining Engineering', 'Mining Engineering'),
    )),
    ('Agriculture & Biotechnology', (
        ('Agricultural Engineering', 'Agricultural Engineering'),
        ('Biotechnology Engineering', 'Biotechnology Engineering'),
        ('Genetic Engineering', 'Genetic Engineering'),
    )),
    ('Other Specialized Technologies', (
        ('Textile Engineering', 'Textile Engineering'),
        ('Leather Technology', 'Leather Technology'),
        ('Printing Technology', 'Printing Technology'),
        ('Packaging Technology', 'Packaging Technology'),
        ('Naval Architecture', 'Naval Architecture'),
        ('Railway Engineering', 'Railway Engineering'),
        ('Fire Engineering', 'Fire Engineering'),
    ))
]

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}), required=True)
    
    roll_no = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'placeholder': 'Roll Number (e.g. 22CSE101)'}))
    branch = forms.ChoiceField(choices=BRANCH_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    semester = forms.IntegerField(min_value=1, max_value=8, required=True, widget=forms.NumberInput(attrs={'placeholder': 'Semester (1-8)'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get('roll_no')
        if StudentProfile.objects.filter(roll_no=roll_no).exists():
            raise forms.ValidationError("Roll number already registered.")
        return roll_no

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data["password"]
        user.set_password(raw_password)
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                roll_no=self.cleaned_data['roll_no'],
                branch=self.cleaned_data['branch'],
                semester=self.cleaned_data['semester'],
                password=raw_password
            )
        return user


class FacultyRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}), required=True)
    
    branch = forms.ChoiceField(choices=BRANCH_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data["password"]
        user.set_password(raw_password)
        if commit:
            user.save()
            FacultyProfile.objects.create(
                user=user,
                branch=self.cleaned_data['branch'],
                password=raw_password
            )
        return user
