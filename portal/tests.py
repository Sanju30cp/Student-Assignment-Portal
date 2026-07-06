from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from portal.models import (
    Subject, StudentProfile, FacultyProfile, Assignment,
    Question, Choice, Submission, Answer, Evaluation
)
import datetime

class AssignmentPortalTests(TestCase):
    def setUp(self):
        # Create standard subject
        self.subject = Subject.objects.create(subject_name="Database Management System")
        
        # Create Faculty user and profile
        self.faculty_user = User.objects.create_user(
            username='faculty_user', password='password123',
            first_name='Amit', last_name='Kumar', email='amit@college.edu'
        )
        self.faculty_profile = FacultyProfile.objects.create(
            user=self.faculty_user, branch='Computer Science Engineering'
        )
        self.faculty_profile.subjects.add(self.subject)

        # Create Student user and profile
        self.student_user = User.objects.create_user(
            username='student_user', password='password123',
            first_name='Rahul', last_name='Sharma', email='rahul@student.edu'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user, roll_no='22CSE101',
            branch='Computer Science Engineering', semester=5
        )
        
        # Initialize standard client
        self.client = Client()

    def test_role_profile_creation(self):
        # Verify profiles created properly in setUp
        self.assertEqual(self.student_profile.user.username, 'student_user')
        self.assertEqual(self.faculty_profile.user.username, 'faculty_user')
        self.assertEqual(self.student_profile.roll_no, '22CSE101')
        self.assertEqual(self.faculty_profile.branch, 'Computer Science Engineering')

    def test_subject_enrollment(self):
        # Enroll student in subject
        self.student_profile.subjects.add(self.subject)
        self.assertIn(self.subject, self.student_profile.subjects.all())

    def test_assignment_and_question_flow(self):
        # Create assignment
        assignment = Assignment.objects.create(
            title="Assignment 1 - DBMS",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        # Create MCQ Question
        mcq_q = Question.objects.create(
            assignment=assignment,
            question_text="What is normalization?",
            question_type="MCQ"
        )
        choice1 = Choice.objects.create(question=mcq_q, choice_text="Data Redundancy", is_correct=False)
        choice2 = Choice.objects.create(question=mcq_q, choice_text="Database Optimization", is_correct=True)
        
        # Create 2 Mark Question
        two_mark_q = Question.objects.create(
            assignment=assignment,
            question_text="Define Primary Key.",
            question_type="TWO_MARK"
        )

        # Verify structures
        self.assertEqual(assignment.questions.count(), 2)
        self.assertEqual(mcq_q.choices.count(), 2)
        self.assertTrue(choice2.is_correct)
        self.assertFalse(choice1.is_correct)

    def test_student_submission_and_faculty_evaluation(self):
        # Setup student enrolling in subject
        self.student_profile.subjects.add(self.subject)

        # Setup assignment and questions
        assignment = Assignment.objects.create(
            title="Assignment 1 - DBMS",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        q1 = Question.objects.create(
            assignment=assignment,
            question_text="Define Primary Key.",
            question_type="TWO_MARK"
        )

        # Student starts assignment (creates Submission)
        submission = Submission.objects.create(
            student=self.student_profile,
            assignment=assignment,
            status='In Progress'
        )

        # Write answer draft
        answer = Answer.objects.create(
            submission=submission,
            question=q1,
            answer_text="A primary key uniquely identifies each record in a table."
        )

        # Student submits assignment
        submission.status = 'Submitted'
        submission.submitted_date = timezone.now()
        submission.save()

        self.assertEqual(submission.status, 'Submitted')
        self.assertEqual(Answer.objects.filter(submission=submission).count(), 1)

        # Faculty evaluates assignment
        eval_record = Evaluation.objects.create(
            submission=submission,
            marks=9,
            review="Excellent explanation."
        )
        submission.status = 'Evaluated'
        submission.save()

        self.assertEqual(submission.status, 'Evaluated')
        self.assertEqual(submission.evaluation.marks, 9)
        self.assertEqual(submission.evaluation.review, "Excellent explanation.")

    def test_home_page_rendering(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Assignment Portal")

    def test_student_registration_flow(self):
        response = self.client.post(reverse('register_student'), {
            'username': 'new_student_user',
            'email': 'new_student@college.edu',
            'first_name': 'New',
            'last_name': 'Student',
            'roll_no': '22CSE999',
            'branch': 'Computer Science and Engineering',
            'semester': 5,
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('student_dashboard'))
        self.assertTrue(User.objects.filter(username='new_student_user').exists())
        self.assertTrue(StudentProfile.objects.filter(roll_no='22CSE999').exists())

    def test_faculty_registration_flow(self):
        response = self.client.post(reverse('register_faculty'), {
            'username': 'new_faculty_user',
            'email': 'new_faculty@college.edu',
            'first_name': 'New',
            'last_name': 'Faculty',
            'branch': 'Computer Science and Engineering',
            'subjects': [self.subject.id],
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('faculty_dashboard'))
        self.assertTrue(User.objects.filter(username='new_faculty_user').exists())
        self.assertTrue(FacultyProfile.objects.filter(user__username='new_faculty_user').exists())

    def test_download_submission_pdf(self):
        # Setup student enrolling in subject
        self.student_profile.subjects.add(self.subject)

        # Setup assignment and questions
        assignment = Assignment.objects.create(
            title="Assignment 1 - DBMS",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        q1 = Question.objects.create(
            assignment=assignment,
            question_text="Define Primary Key.",
            question_type="TWO_MARK"
        )
        submission = Submission.objects.create(
            student=self.student_profile,
            assignment=assignment,
            status='Submitted',
            submitted_date=timezone.now()
        )
        Answer.objects.create(
            submission=submission,
            question=q1,
            answer_text="A primary key uniquely identifies each record in a table."
        )

        # Try downloading as a student (should succeed for their own submission)
        self.client.login(username='student_user', password='password123')
        response = self.client.get(reverse('download_submission_pdf', args=[submission.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Try downloading another student's submission (should redirect to dashboard_redirect)
        other_user = User.objects.create_user(
            username='other_student', password='password123',
            first_name='Other', last_name='Student', email='other@student.edu'
        )
        other_profile = StudentProfile.objects.create(
            user=other_user, roll_no='22CSE888',
            branch='Computer Science Engineering', semester=5
        )
        self.client.login(username='other_student', password='password123')
        response = self.client.get(reverse('download_submission_pdf', args=[submission.id]))
        self.assertEqual(response.status_code, 302)

        # Log in as faculty (should succeed)
        self.client.login(username='faculty_user', password='password123')
        response = self.client.get(reverse('download_submission_pdf', args=[submission.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 0)

    def test_download_all_submissions_pdf(self):
        # Setup student enrolling in subject
        self.student_profile.subjects.add(self.subject)

        # Setup assignment and questions
        assignment = Assignment.objects.create(
            title="Assignment 1 - DBMS",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        submission = Submission.objects.create(
            student=self.student_profile,
            assignment=assignment,
            status='Submitted',
            submitted_date=timezone.now()
        )

        # Try downloading as a student (should redirect)
        self.client.login(username='student_user', password='password123')
        response = self.client.get(reverse('download_all_submissions_pdf'))
        self.assertEqual(response.status_code, 302)

        # Log in as faculty
        self.client.login(username='faculty_user', password='password123')
        response = self.client.get(reverse('download_all_submissions_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(len(response.content) > 0)

    def test_student_dashboard_context(self):
        # Log in student
        self.client.login(username='student_user', password='password123')
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_assignments', response.context)
        self.assertIn('pending_assignments', response.context)
        self.assertIn('completed_assignments', response.context)
        self.assertIn('average_score', response.context)
        self.assertIn('status_counts_json', response.context)
        self.assertIn('subject_chart_labels_json', response.context)
        self.assertIn('subject_chart_data_json', response.context)

    def test_faculty_dashboard_context(self):
        # Log in faculty
        self.client.login(username='faculty_user', password='password123')
        response = self.client.get(reverse('faculty_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_assignments', response.context)
        self.assertIn('active_assignments', response.context)
        self.assertIn('pending_evaluations', response.context)
        self.assertIn('total_submissions', response.context)
        self.assertIn('avg_class_grade', response.context)
        self.assertIn('status_counts_json', response.context)
        self.assertIn('assignment_chart_labels_json', response.context)

    def test_publish_assignment(self):
        # Enroll student in the subject
        self.student_profile.subjects.add(self.subject)
        
        # Create assignment (unpublished)
        assignment = Assignment.objects.create(
            title="Notification Test Assignment",
            subject=self.subject,
            due_date=datetime.date(2026, 9, 30),
            created_by=self.faculty_user,
            is_published=False
        )
        
        # Create a question for the assignment
        Question.objects.create(
            assignment=assignment,
            question_text="Test question",
            question_type="TWO_MARK"
        )
        
        # Log in faculty
        self.client.login(username='faculty_user', password='password123')
        
        # Publish the assignment
        response = self.client.post(reverse('publish_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 302)
        
        # Refresh and verify it is published
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_published)


    def test_start_assignment_instructions_flow(self):
        # Enroll student
        self.student_profile.subjects.add(self.subject)
        
        # Create published assignment
        assignment = Assignment.objects.create(
            title="Instructions Test Assignment",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        
        self.client.login(username='student_user', password='password123')
        
        # 1. GET start_assignment without submission should render instructions template
        response = self.client.get(reverse('start_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portal/student/assignment_instructions.html')
        self.assertEqual(response.context['assignment'], assignment)
        self.assertEqual(response.context['question_count'], 0)
        
        # Check that no submission is created yet
        self.assertFalse(Submission.objects.filter(student=self.student_profile, assignment=assignment).exists())
        
        # 2. POST start_assignment should create submission and redirect to do_assignment
        response = self.client.post(reverse('start_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 302)
        
        # Check submission created
        submission = Submission.objects.filter(student=self.student_profile, assignment=assignment).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.status, 'In Progress')
        self.assertRedirects(response, reverse('do_assignment', args=[submission.id]))
        
        # 3. GET start_assignment again should redirect directly to do_assignment since submission exists
        response = self.client.get(reverse('start_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('do_assignment', args=[submission.id]))

    def test_delete_assignment(self):
        # Create an assignment for testing deletion
        assignment = Assignment.objects.create(
            title="Deletion Test Assignment",
            subject=self.subject,
            due_date=datetime.date(2026, 8, 25),
            created_by=self.faculty_user,
            is_published=True
        )
        
        # 1. Attempt delete as a student (should be blocked by @faculty_required, redirecting)
        self.client.login(username='student_user', password='password123')
        response = self.client.post(reverse('delete_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(id=assignment.id).exists())
        
        # 2. Attempt delete as another faculty member (should fail with 404)
        other_faculty_user = User.objects.create_user(
            username='other_faculty_user', password='password123',
            first_name='Other', last_name='Faculty'
        )
        FacultyProfile.objects.create(user=other_faculty_user, branch='Computer Science Engineering')
        self.client.login(username='other_faculty_user', password='password123')
        response = self.client.post(reverse('delete_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Assignment.objects.filter(id=assignment.id).exists())
        
        # 3. Attempt delete as the owner faculty (should succeed)
        self.client.login(username='faculty_user', password='password123')
        response = self.client.post(reverse('delete_assignment', args=[assignment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('faculty_dashboard'))
        self.assertFalse(Assignment.objects.filter(id=assignment.id).exists())

    def test_login_role_restrictions(self):
        # 1. Student trying to login via Faculty portal
        response = self.client.post(reverse('login'), {
            'username': 'student_user',
            'password': 'password123',
            'login_role': 'faculty'
        }, follow=True)
        self.assertContains(response, "Access denied. Faculty portal is only for faculty accounts.")
        self.assertNotIn('_auth_user_id', self.client.session)

        # 2. Faculty trying to login via Student portal
        response = self.client.post(reverse('login'), {
            'username': 'faculty_user',
            'password': 'password123',
            'login_role': 'student'
        }, follow=True)
        self.assertContains(response, "Access denied. Student portal is only for student accounts.")
        self.assertNotIn('_auth_user_id', self.client.session)

        # 3. Student logging in via Student portal (should succeed)
        response = self.client.post(reverse('login'), {
            'username': 'student_user',
            'password': 'password123',
            'login_role': 'student'
        }, follow=True)
        self.assertContains(response, "Welcome back, Rahul!")
        self.assertEqual(int(self.client.session['_auth_user_id']), self.student_user.id)
        
        # Logout
        self.client.logout()

        # 4. Faculty logging in via Faculty portal (should succeed)
        response = self.client.post(reverse('login'), {
            'username': 'faculty_user',
            'password': 'password123',
            'login_role': 'faculty'
        }, follow=True)
        self.assertContains(response, "Welcome back, Amit!")
        self.assertEqual(int(self.client.session['_auth_user_id']), self.faculty_user.id)





