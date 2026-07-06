from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.db import IntegrityError
from django.contrib import messages

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .models import (
    Subject, StudentProfile, FacultyProfile, Assignment,
    Question, Choice, Submission, Answer, Evaluation
)
from .forms import StudentRegistrationForm, FacultyRegistrationForm

from django.contrib.auth.forms import AuthenticationForm

# Helper decorators
def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "Access denied. Student account required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def faculty_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'faculty_profile'):
            messages.error(request, "Access denied. Faculty account required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@never_cache
@ensure_csrf_cookie
def home_view(request):
    return render(request, 'portal/home.html')

# Auth views
@never_cache
@ensure_csrf_cookie
def login_view(request):
    # We no longer serve a separate login page. GET requests should show the
    # embedded login forms on the home page. If the user is already
    # authenticated, send them to their dashboard.
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('dashboard_redirect')
        return redirect('home')

    # Handle POST login submissions coming from the home page forms
    if request.method == 'POST':
        login_role = request.POST.get('login_role')
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Check user role based on the submission form (skip check for superusers)
            if not user.is_superuser:
                if login_role == 'student' and not hasattr(user, 'student_profile'):
                    messages.error(request, "Access denied. Student portal is only for student accounts.")
                    return redirect(request.META.get('HTTP_REFERER', 'home'))
                elif login_role == 'faculty' and not hasattr(user, 'faculty_profile'):
                    messages.error(request, "Access denied. Faculty portal is only for faculty accounts.")
                    return redirect(request.META.get('HTTP_REFERER', 'home'))
            
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
            # Redirect back to referring page (usually home)
            return redirect(request.META.get('HTTP_REFERER', 'home'))

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

@never_cache
def register_student(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to your dashboard.")
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'portal/register_student.html', {'form': form})

@never_cache
def register_faculty(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        form = FacultyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome to your dashboard.")
            return redirect('faculty_dashboard')
    else:
        form = FacultyRegistrationForm()
    return render(request, 'portal/register_faculty.html', {'form': form})

@login_required
def dashboard_redirect(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    if hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    elif hasattr(request.user, 'faculty_profile'):
        return redirect('faculty_dashboard')
    else:
        # Fallback if somehow a user has no profile
        return redirect('/admin/')


# Student Views
import json

@student_required
def student_dashboard(request):
    profile = request.user.student_profile
    my_subjects = profile.subjects.all()
    # Available subjects are subjects the student hasn't enrolled in yet
    available_subjects = Subject.objects.exclude(id__in=my_subjects.values_list('id', flat=True))
    
    # If no subjects exist in DB, create some defaults for testing convenience
    if not Subject.objects.exists():
        for name in ['Database Management System', 'Operating Systems', 'Computer Networks', 'Software Engineering', 'Machine Learning', 'Data Structures']:
            Subject.objects.create(subject_name=name)
        available_subjects = Subject.objects.all()

    # Calculate student dashboard analytics
    assignments = Assignment.objects.filter(subject__in=my_subjects, is_published=True)
    status_counts = {
        'Pending': 0,
        'In Progress': 0,
        'Submitted': 0,
        'Evaluated': 0
    }
    
    evaluated_marks_sum = 0
    evaluated_count = 0
    
    my_submissions = Submission.objects.filter(student=profile, assignment__in=assignments).select_related('evaluation', 'assignment')
    submissions_by_assignment = {sub.assignment_id: sub for sub in my_submissions}
    
    for ass in assignments:
        sub = submissions_by_assignment.get(ass.id)
        if sub:
            status_counts[sub.status] += 1
            if sub.status == 'Evaluated' and hasattr(sub, 'evaluation'):
                evaluated_marks_sum += sub.evaluation.marks
                evaluated_count += 1
        else:
            status_counts['Pending'] += 1
            
    average_score = round(evaluated_marks_sum / evaluated_count, 2) if evaluated_count > 0 else 0
    
    # Subject wise average grades for charts
    subject_chart_labels = []
    subject_chart_data = []
    for sub_obj in my_subjects:
        sub_assignments = assignments.filter(subject=sub_obj)
        sub_subs = [submissions_by_assignment.get(a.id) for a in sub_assignments if submissions_by_assignment.get(a.id)]
        sub_evals = [s.evaluation.marks for s in sub_subs if s and s.status == 'Evaluated' and hasattr(s, 'evaluation')]
        
        avg_sub_mark = round(sum(sub_evals) / len(sub_evals), 2) if len(sub_evals) > 0 else 0
        subject_chart_labels.append(sub_obj.subject_name)
        subject_chart_data.append(avg_sub_mark)

    return render(request, 'portal/student/dashboard.html', {
        'profile': profile,
        'my_subjects': my_subjects,
        'available_subjects': available_subjects,
        'total_assignments': assignments.count(),
        'pending_assignments': status_counts['Pending'] + status_counts['In Progress'],
        'completed_assignments': status_counts['Submitted'] + status_counts['Evaluated'],
        'average_score': average_score,
        'status_counts_json': json.dumps(status_counts),
        'subject_chart_labels_json': json.dumps(subject_chart_labels),
        'subject_chart_data_json': json.dumps(subject_chart_data),
    })

@student_required
def enroll_subject(request, subject_id):
    profile = request.user.student_profile
    subject = get_object_or_404(Subject, id=subject_id)
    profile.subjects.add(subject)
    messages.success(request, f"Enrolled in {subject.subject_name} successfully!")
    return redirect('student_dashboard')

@student_required
def student_assignments(request):
    profile = request.user.student_profile
    enrolled_subjects = profile.subjects.all()
    
    # Get all published assignments for enrolled subjects
    assignments = Assignment.objects.filter(subject__in=enrolled_subjects, is_published=True)
    
    # Map submissions to get status
    assignment_list = []
    for ass in assignments:
        submission = Submission.objects.filter(student=profile, assignment=ass).first()
        status = 'Pending'
        submission_id = None
        if submission:
            status = submission.status
            submission_id = submission.id
            
        assignment_list.append({
            'assignment': ass,
            'status': status,
            'submission_id': submission_id,
        })
        
    return render(request, 'portal/student/assignments.html', {
        'assignments': assignment_list
    })

@student_required
def start_assignment(request, assignment_id):
    profile = request.user.student_profile
    assignment = get_object_or_404(Assignment, id=assignment_id, is_published=True)
    
    # Ensure subject is enrolled
    if assignment.subject not in profile.subjects.all():
        messages.error(request, "You must enroll in the subject first.")
        return redirect('student_dashboard')
        
    # Check if a submission already exists
    submission = Submission.objects.filter(student=profile, assignment=assignment).first()
    if submission:
        if submission.status in ['Submitted', 'Evaluated']:
            return redirect('view_submission', submission_id=submission.id)
        return redirect('do_assignment', submission_id=submission.id)
        
    if request.method == 'POST':
        submission = Submission.objects.create(
            student=profile,
            assignment=assignment,
            status='In Progress'
        )
        return redirect('do_assignment', submission_id=submission.id)
        
    # Render instructions screen for GET requests
    return render(request, 'portal/student/assignment_instructions.html', {
        'assignment': assignment,
        'question_count': assignment.questions.count(),
    })

@student_required
def do_assignment(request, submission_id):
    profile = request.user.student_profile
    submission = get_object_or_404(Submission, id=submission_id, student=profile)
    assignment = submission.assignment
    
    if submission.status in ['Submitted', 'Evaluated']:
        return redirect('view_submission', submission_id=submission.id)
        
    questions = assignment.questions.all()
    
    if request.method == 'POST':
        # Save answers
        for q in questions:
            ans_text = request.POST.get(f'question_{q.id}', '').strip()
            answer, created = Answer.objects.get_or_create(submission=submission, question=q)
            answer.answer_text = ans_text
            answer.save()
            
        action = request.POST.get('action')
        if action == 'submit':
            submission.status = 'Submitted'
            submission.submitted_date = timezone.now()
            submission.save()
            messages.success(request, f"Assignment '{assignment.title}' submitted successfully!")
            return redirect('student_assignments')
        else:
            submission.status = 'In Progress'
            submission.save()
            messages.success(request, "Progress saved as draft.")
            return redirect('student_assignments')
            
    # Load existing answers to populate form fields
    answers_dict = {ans.question_id: ans.answer_text for ans in submission.answers.all()}
    
    questions_data = []
    for q in questions:
        questions_data.append({
            'question': q,
            'saved_answer': answers_dict.get(q.id, ''),
            'choices': q.choices.all() if q.question_type == 'MCQ' else None
        })
        
    return render(request, 'portal/student/do_assignment.html', {
        'submission': submission,
        'assignment': assignment,
        'questions_data': questions_data
    })

@student_required
def view_submission(request, submission_id):
    profile = request.user.student_profile
    submission = get_object_or_404(Submission, id=submission_id, student=profile)
    assignment = submission.assignment
    
    answers = submission.answers.select_related('question').all()
    evaluation = getattr(submission, 'evaluation', None)
    
    return render(request, 'portal/student/view_submission.html', {
        'submission': submission,
        'assignment': assignment,
        'answers': answers,
        'evaluation': evaluation
    })

@student_required
def student_results(request):
    profile = request.user.student_profile
    # Get all submissions that are evaluated
    submissions = Submission.objects.filter(student=profile, status='Evaluated').select_related('assignment', 'assignment__subject', 'evaluation')
    return render(request, 'portal/student/results.html', {
        'submissions': submissions
    })

@student_required
def student_profile(request):
    profile = request.user.student_profile
    if request.method == 'POST':
        # Simple profile update logic
        profile.user.first_name = request.POST.get('first_name', profile.user.first_name)
        profile.user.last_name = request.POST.get('last_name', profile.user.last_name)
        profile.user.email = request.POST.get('email', profile.user.email)
        profile.user.save()
        
        profile.branch = request.POST.get('branch', profile.branch)
        profile.semester = int(request.POST.get('semester', profile.semester))
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('student_profile')
        
    return render(request, 'portal/student/profile.html', {
        'profile': profile
    })


# Faculty Views
@faculty_required
def faculty_dashboard(request):
    profile = request.user.faculty_profile
    my_subjects = profile.subjects.all()
    
    # Summary items for assignments created by this faculty
    my_assignments = Assignment.objects.filter(created_by=request.user)
    total_assignments = my_assignments.count()
    active_assignments = my_assignments.filter(is_published=True, due_date__gte=timezone.now().date()).count()
    
    # Submissions on assignments created by this faculty
    my_submissions = Submission.objects.filter(assignment__in=my_assignments)
    total_submissions = my_submissions.count()
    pending_evaluations = my_submissions.filter(status='Submitted').count()
    
    # Calculate average class grade across all graded evaluations
    from django.db.models import Avg
    avg_class_grade = Evaluation.objects.filter(submission__assignment__in=my_assignments).aggregate(Avg('marks'))['marks__avg']
    avg_class_grade = round(avg_class_grade, 2) if avg_class_grade is not None else 0
    
    # Submissions counts by status
    status_counts = {
        'Pending': my_submissions.filter(status='Pending').count(),
        'In Progress': my_submissions.filter(status='In Progress').count(),
        'Submitted': pending_evaluations,
        'Evaluated': my_submissions.filter(status='Evaluated').count(),
    }
    
    # Assignment-wise submissions chart details
    assignment_chart_labels = []
    assignment_chart_submissions = []
    assignment_chart_evaluations = []
    for ass in my_assignments:
        ass_subs = my_submissions.filter(assignment=ass)
        assignment_chart_labels.append(ass.title)
        assignment_chart_submissions.append(ass_subs.filter(status__in=['Submitted', 'Evaluated']).count())
        assignment_chart_evaluations.append(ass_subs.filter(status='Evaluated').count())

    return render(request, 'portal/faculty/dashboard.html', {
        'profile': profile,
        'my_subjects': my_subjects,
        'my_assignments': my_assignments,
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'total_submissions': total_submissions,
        'pending_evaluations': pending_evaluations,
        'avg_class_grade': avg_class_grade,
        'status_counts_json': json.dumps(status_counts),
        'assignment_chart_labels_json': json.dumps(assignment_chart_labels),
        'assignment_chart_submissions_json': json.dumps(assignment_chart_submissions),
        'assignment_chart_evaluations_json': json.dumps(assignment_chart_evaluations),
    })

@faculty_required
def new_assignment(request):
    profile = request.user.faculty_profile
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        due_date = request.POST.get('due_date')
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        assignment = Assignment.objects.create(
            title=title,
            subject=subject,
            due_date=due_date,
            created_by=request.user,
            is_published=False
        )
        messages.success(request, "Assignment setup completed. Now add questions.")
        return redirect('manage_questions', assignment_id=assignment.id)
        
    return render(request, 'portal/faculty/new_assignment.html', {
        'subjects': subjects
    })

@faculty_required
def manage_questions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    
    if request.method == 'POST':
        q_type = request.POST.get('question_type')
        q_text = request.POST.get('question_text')
        
        if q_type and q_text:
            question = Question.objects.create(
                assignment=assignment,
                question_text=q_text,
                question_type=q_type
            )
            
            if q_type == 'MCQ':
                choices = [
                    (request.POST.get('choice_a', ''), request.POST.get('correct_choice') == 'A'),
                    (request.POST.get('choice_b', ''), request.POST.get('correct_choice') == 'B'),
                    (request.POST.get('choice_c', ''), request.POST.get('correct_choice') == 'C'),
                    (request.POST.get('choice_d', ''), request.POST.get('correct_choice') == 'D'),
                ]
                for text, is_corr in choices:
                    if text.strip():
                        Choice.objects.create(
                            question=question,
                            choice_text=text.strip(),
                            is_correct=is_corr
                        )
            messages.success(request, "Question added successfully!")
            return redirect('manage_questions', assignment_id=assignment.id)
            
    questions = assignment.questions.all()
    questions_data = []
    for q in questions:
        questions_data.append({
            'question': q,
            'choices': q.choices.all() if q.question_type == 'MCQ' else None
        })
        
    return render(request, 'portal/faculty/manage_questions.html', {
        'assignment': assignment,
        'questions_data': questions_data
    })

@faculty_required
def publish_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    if assignment.questions.count() == 0:
        messages.error(request, "Cannot publish assignment with no questions.")
        return redirect('manage_questions', assignment_id=assignment.id)
        
    assignment.is_published = True
    assignment.save()
    
    messages.success(request, f"Assignment '{assignment.title}' published successfully!")
    return redirect('faculty_dashboard')

@faculty_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        messages.success(request, f"Assignment '{title}' deleted successfully.")
    return redirect('faculty_dashboard')

@faculty_required
def submitted_assignments(request):
    my_assignments = Assignment.objects.filter(created_by=request.user)
    submissions = Submission.objects.filter(assignment__in=my_assignments).select_related('student', 'assignment', 'assignment__subject').order_by('-submitted_date')
    return render(request, 'portal/faculty/submissions.html', {
        'submissions': submissions
    })

@faculty_required
def evaluate_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, assignment__created_by=request.user)
    assignment = submission.assignment
    
    if request.method == 'POST':
        marks = int(request.POST.get('marks', 0))
        review = request.POST.get('review', '')
        
        evaluation, created = Evaluation.objects.get_or_create(
            submission=submission,
            defaults={'marks': marks, 'review': review}
        )
        if not created:
            evaluation.marks = marks
            evaluation.review = review
            evaluation.save()
            
        submission.status = 'Evaluated'
        submission.save()
        messages.success(request, f"Submission evaluated successfully!")
        return redirect('submitted_assignments')
        
    answers = submission.answers.select_related('question').all()
    answers_data = []
    for ans in answers:
        answers_data.append({
            'question': ans.question,
            'answer': ans.answer_text,
            'choices': ans.question.choices.all() if ans.question.question_type == 'MCQ' else None
        })
        
    existing_eval = getattr(submission, 'evaluation', None)
    
    return render(request, 'portal/faculty/evaluate.html', {
        'submission': submission,
        'assignment': assignment,
        'answers_data': answers_data,
        'evaluation': existing_eval
    })

@faculty_required
def faculty_profile(request):
    profile = request.user.faculty_profile
    if request.method == 'POST':
        # Update details
        profile.user.first_name = request.POST.get('first_name', profile.user.first_name)
        profile.user.last_name = request.POST.get('last_name', profile.user.last_name)
        profile.user.email = request.POST.get('email', profile.user.email)
        profile.user.save()
        
        profile.branch = request.POST.get('branch', profile.branch)
        profile.save()
        
        # Enrolling/handling subjects updates
        subj_ids = request.POST.getlist('subjects')
        profile.subjects.set(Subject.objects.filter(id__in=subj_ids))
        
        messages.success(request, "Profile updated successfully!")
        return redirect('faculty_profile')
        
    all_subjects = Subject.objects.all()
    return render(request, 'portal/faculty/profile.html', {
        'profile': profile,
        'all_subjects': all_subjects
    })

import html

@login_required
def download_submission_pdf(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Ensure user is authorized: either the student who submitted it or the faculty who created the assignment
    is_authorized = False
    if hasattr(request.user, 'student_profile'):
        if submission.student == request.user.student_profile:
            is_authorized = True
    elif hasattr(request.user, 'faculty_profile'):
        if submission.assignment.created_by == request.user:
            is_authorized = True
            
    if not is_authorized:
        messages.error(request, "Access denied. You are not authorized to download this report.")
        return redirect('dashboard_redirect')
        
    assignment = submission.assignment
    student = submission.student
    
    # Setup document
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    primary_color = colors.HexColor("#1e3a8a")   # deep blue
    secondary_color = colors.HexColor("#475569") # slate gray
    text_color = colors.HexColor("#1e293b")      # dark slate text
    light_bg = colors.HexColor("#f8fafc")        # very light gray
    border_color = colors.HexColor("#e2e8f0")    # border gray
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color
    )
    
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    answer_label_style = ParagraphStyle(
        'AnswerLabel',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=secondary_color
    )
    
    answer_text_style = ParagraphStyle(
        'AnswerText',
        parent=body_style,
        fontName='Helvetica',
        spaceBefore=4,
        spaceAfter=8
    )

    story = []
    
    # Title
    story.append(Paragraph("Student Submission Report", title_style))
    story.append(Paragraph(f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Escape helpers
    def pdf_esc(text):
        return html.escape(str(text)) if text else ""
        
    def pdf_esc_multiline(text):
        if not text:
            return ""
        return html.escape(str(text)).replace('\n', '<br/>')
        
    student_name = student.user.get_full_name() or student.user.username
    
    # Student & Assignment Info Table
    info_data = [
        [
            Paragraph("Student Name:", body_bold),
            Paragraph(pdf_esc(student_name), body_style),
            Paragraph("Assignment:", body_bold),
            Paragraph(pdf_esc(assignment.title), body_style),
        ],
        [
            Paragraph("Roll Number:", body_bold),
            Paragraph(pdf_esc(student.roll_no), body_style),
            Paragraph("Subject:", body_bold),
            Paragraph(pdf_esc(assignment.subject.subject_name), body_style),
        ],
        [
            Paragraph("Branch:", body_bold),
            Paragraph(pdf_esc(student.branch), body_style),
            Paragraph("Submission Date:", body_bold),
            Paragraph(submission.submitted_date.strftime('%Y-%m-%d %H:%M') if submission.submitted_date else "N/A", body_style),
        ],
        [
            Paragraph("Status:", body_bold),
            Paragraph(pdf_esc(submission.status), body_bold if submission.status == 'Evaluated' else body_style),
            Paragraph("Marks Awarded:", body_bold),
            Paragraph(f"{submission.evaluation.marks}/10" if hasattr(submission, 'evaluation') else "Not Evaluated", body_bold if hasattr(submission, 'evaluation') else body_style),
        ]
    ]
    
    info_table = Table(info_data, colWidths=[100, 150, 100, 154])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.25, border_color),
        ('BOX', (0,0), (-1,-1), 1, primary_color),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Evaluation section if available
    evaluation = getattr(submission, 'evaluation', None)
    if evaluation:
        story.append(Paragraph("Faculty Evaluation & Review", h2_style))
        eval_data = [
            [Paragraph("Marks Awarded:", body_bold), Paragraph(f"{evaluation.marks} / 10", body_bold)],
            [Paragraph("Feedback / Review:", body_bold), Paragraph(pdf_esc_multiline(evaluation.review), body_style)]
        ]
        eval_table = Table(eval_data, colWidths=[120, 384])
        eval_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")), # light green
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#bbf7d0")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#22c55e")),
        ]))
        story.append(eval_table)
        story.append(Spacer(1, 20))
        
    # Answers section
    story.append(Paragraph("Submitted Answers", h2_style))
    
    answers = submission.answers.select_related('question').all()
    for idx, ans in enumerate(answers, 1):
        q = ans.question
        # Question Header
        q_type_str = "MCQ" if q.question_type == 'MCQ' else "2-Mark" if q.question_type == 'TWO_MARK' else "5-Mark"
        q_marks = "1 Mark" if q.question_type == 'MCQ' else "2 Marks" if q.question_type == 'TWO_MARK' else "5 Marks"
        
        q_text = f"Q{idx}. {pdf_esc(q.question_text)} ({q_type_str} - {q_marks})"
        story.append(Paragraph(q_text, question_style))
        
        if q.question_type == 'MCQ':
            # Choices list
            choices = q.choices.all()
            for choice in choices:
                is_correct = choice.is_correct
                is_selected = (choice.choice_text == ans.answer_text)
                
                # Format bullet points
                bullet = "[x]" if is_selected else "[ ]"
                choice_text_esc = pdf_esc(choice.choice_text)
                choice_line = f"{bullet} {choice_text_esc}"
                if is_correct:
                    choice_line += " <b>(Correct Answer)</b>"
                
                choice_style = ParagraphStyle(
                    f'ChoiceStyle_{q.id}_{choice.id}',
                    parent=body_style,
                    fontName='Helvetica-Bold' if is_selected else 'Helvetica',
                    textColor=colors.HexColor("#15803d") if is_correct else text_color if not is_selected else colors.HexColor("#1d4ed8")
                )
                story.append(Paragraph(choice_line, choice_style))
            
            story.append(Spacer(1, 10))
        else:
            # Short/Long Answers
            story.append(Paragraph("Submitted Answer:", answer_label_style))
            ans_text = ans.answer_text.strip() if ans.answer_text else "[Left Blank]"
            # Format multi-line answers
            ans_text_formatted = pdf_esc_multiline(ans_text)
            
            # Answer Box
            ans_box_data = [[Paragraph(ans_text_formatted, answer_text_style)]]
            ans_box_table = Table(ans_box_data, colWidths=[504])
            ans_box_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), light_bg),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 10),
                ('BOX', (0,0), (-1,-1), 1, border_color),
            ]))
            
            story.append(ans_box_table)
            story.append(Spacer(1, 10))
            
    # Build Document
    doc.build(story)
    
    # Return response
    buffer.seek(0)
    filename = f"Submission_Report_{student.roll_no}_{assignment.title.replace(' ', '_')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@faculty_required
def download_all_submissions_pdf(request):
    my_assignments = Assignment.objects.filter(created_by=request.user)
    submissions = Submission.objects.filter(assignment__in=my_assignments).select_related(
        'student', 'student__user', 'assignment', 'assignment__subject'
    ).order_by('-submitted_date')
    
    # Setup document
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    primary_color = colors.HexColor("#1e3a8a")   # deep blue
    secondary_color = colors.HexColor("#475569") # slate gray
    text_color = colors.HexColor("#1e293b")      # dark slate text
    light_bg = colors.HexColor("#f8fafc")        # very light gray
    border_color = colors.HexColor("#e2e8f0")    # border gray
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitleAll',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitleAll',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    th_style = ParagraphStyle(
        'TableHeaderAll',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    tb_style = ParagraphStyle(
        'TableBodyAll',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_color
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Student Submissions Report", title_style))
    faculty_name = request.user.get_full_name() or request.user.username
    story.append(Paragraph(f"Generated by Prof. {html.escape(faculty_name)} on {timezone.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Summary Info
    total_count = submissions.count()
    evaluated_count = submissions.filter(status='Evaluated').count()
    pending_count = submissions.filter(status='Submitted').count()
    
    summary_text = f"<b>Total Submissions:</b> {total_count} | <b>Evaluated:</b> {evaluated_count} | <b>Pending Review:</b> {pending_count}"
    story.append(Paragraph(summary_text, tb_style))
    story.append(Spacer(1, 15))
    
    # Escape helpers
    def pdf_esc(text):
        return html.escape(str(text)) if text else ""
        
    # Table Data construction
    table_data = [[
        Paragraph("S.No", th_style),
        Paragraph("Student Name (Roll No)", th_style),
        Paragraph("Subject", th_style),
        Paragraph("Assignment", th_style),
        Paragraph("Submitted Date", th_style),
        Paragraph("Status", th_style),
        Paragraph("Marks", th_style)
    ]]
    
    for idx, sub in enumerate(submissions, 1):
        stud_name = sub.student.user.get_full_name() or sub.student.user.username
        stud_info = f"<b>{pdf_esc(stud_name)}</b><br/><font color='#64748b' size='8'>Roll: {pdf_esc(sub.student.roll_no)}</font>"
        
        sub_date = sub.submitted_date.strftime('%Y-%m-%d %H:%M') if sub.submitted_date else "N/A"
        
        # Color coding status
        status_color = "#b91c1c" if sub.status == 'Pending' else "#d97706" if sub.status == 'In Progress' else "#2563eb" if sub.status == 'Submitted' else "#15803d"
        status_html = f"<font color='{status_color}'><b>{pdf_esc(sub.status)}</b></font>"
        
        marks_html = f"<b>{sub.evaluation.marks}/10</b>" if hasattr(sub, 'evaluation') else "N/A"
        
        table_data.append([
            Paragraph(str(idx), tb_style),
            Paragraph(stud_info, tb_style),
            Paragraph(pdf_esc(sub.assignment.subject.subject_name), tb_style),
            Paragraph(pdf_esc(sub.assignment.title), tb_style),
            Paragraph(sub_date, tb_style),
            Paragraph(status_html, tb_style),
            Paragraph(marks_html, tb_style)
        ])
        
    # Table configuration
    col_widths = [24, 120, 90, 90, 75, 65, 40] # Total = 504
    report_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Alternating row background
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,0), 1.5, primary_color),
        ('INNERGRID', (0,0), (-1,-1), 0.25, border_color),
        ('BOX', (0,0), (-1,-1), 1, border_color),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0,i), (-1,i), light_bg))
            
    report_table.setStyle(TableStyle(t_style))
    story.append(report_table)
    
    # Build
    doc.build(story)
    
    buffer.seek(0)
    filename = f"Submissions_Report_{timezone.now().strftime('%Y%m%d')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


