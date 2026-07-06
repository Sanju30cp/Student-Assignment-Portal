from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.subject_name

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=100)
    semester = models.IntegerField()
    subjects = models.ManyToManyField(Subject, blank=True, related_name='enrolled_students')
    password = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.roll_no})"

class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile')
    branch = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='handled_faculty')
    password = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assignments')
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('MCQ', 'Multiple Choice Question'),
        ('TWO_MARK', '2-Mark Question'),
        ('FIVE_MARK', '5-Mark Question'),
    ]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)

    def __str__(self):
        return f"{self.question_type} - {self.question_text[:50]}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text

class Submission(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Submitted', 'Submitted'),
        ('Evaluated', 'Evaluated'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    submitted_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        unique_together = ('student', 'assignment')

    def __str__(self):
        return f"{self.student} - {self.assignment.title} ({self.status})"

class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Ans to Q: {self.question.id} for Submission: {self.submission.id}"

class Evaluation(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='evaluation')
    marks = models.IntegerField()  # 0 to 10
    review = models.TextField()

    def __str__(self):
        return f"Eval for {self.submission.student} ({self.marks}/10)"
