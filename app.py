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
except Exception as e:
    print(f"[STARTUP ERROR] Error applying migrations: {e}")

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
