import os

from django.core.wsgi import get_wsgi_application

# Fix the string here:
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()