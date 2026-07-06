import os
import django
from django.core.management import call_command

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assignment_portal.settings')
django.setup()

# Auto-run migrations on startup to create tables if they do not exist
try:
    print("\n[STARTUP] Running database migrations...")
    call_command('migrate', interactive=False)
    print("[STARTUP] Database migrations applied successfully.")

    # Create default subjects if none exist
    from portal.models import Subject
    default_subjects = [
        'Database Management System', 'Operating Systems', 'Computer Networks', 
        'Software Engineering', 'Machine Learning', 'Data Structures',
        'Deep Learning', 'Cloud Computing', 'Artificial Intelligence',
        'Cybersecurity', 'Web Technology', 'Data Science'
    ]
    for name in default_subjects:
        Subject.objects.get_or_create(subject_name=name)
    print("[STARTUP] Default subjects checked/created.")
except Exception as e:
    print(f"[STARTUP ERROR] Error applying migrations or creating subjects: {e}")

# Auto-collect static files on startup
try:
    print("\n[STARTUP] Collecting static files...")
    call_command('collectstatic', interactive=False)
    print("[STARTUP] Static files collected successfully.")
except Exception as e:
    print(f"[STARTUP ERROR] Error collecting static files: {e}")

# Expose the WSGI application callable for Gunicorn
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
