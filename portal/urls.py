from django.urls import path
from . import views

urlpatterns = [
    # General urls
    path('', views.home_view, name='home'),
    
    # Auth urls
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/faculty/', views.register_faculty, name='register_faculty'),
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),

    # Student urls
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/subjects/enroll/<int:subject_id>/', views.enroll_subject, name='enroll_subject'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/start/', views.start_assignment, name='start_assignment'),
    path('student/submissions/<int:submission_id>/do/', views.do_assignment, name='do_assignment'),
    path('student/submissions/<int:submission_id>/view/', views.view_submission, name='view_submission'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # Faculty urls
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/assignments/new/', views.new_assignment, name='new_assignment'),
    path('faculty/assignments/<int:assignment_id>/questions/', views.manage_questions, name='manage_questions'),
    path('faculty/assignments/<int:assignment_id>/publish/', views.publish_assignment, name='publish_assignment'),
    path('faculty/assignments/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('faculty/submissions/', views.submitted_assignments, name='submitted_assignments'),
    path('faculty/submissions/<int:submission_id>/evaluate/', views.evaluate_submission, name='evaluate_submission'),
    path('faculty/submissions/<int:submission_id>/download-pdf/', views.download_submission_pdf, name='download_submission_pdf'),
    path('faculty/submissions/download-report-pdf/', views.download_all_submissions_pdf, name='download_all_submissions_pdf'),
    path('faculty/profile/', views.faculty_profile, name='faculty_profile'),
]
