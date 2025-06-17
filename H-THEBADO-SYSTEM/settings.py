from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-temporary-secret-key' # Replace with a real secret key for production

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ROOT_URLCONF = 'H-THEBADO-SYSTEM.urls'

# Application definition

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'HTHEBADO',  # Your database name in pgAdmin
        'USER': 'postgres',  # Your PostgreSQL username
        'PASSWORD': 'admin',  # Your PostgreSQL password
        'HOST': 'localhost',  # Change if using a remote PostgreSQL server
        'PORT': '5432',  # Default PostgreSQL port
    }
}

INSTALLED_APPS = [
    "reconciliation",  # Your main reconciliation app
    "users.apps.UsersConfig",  # Authentication & permission management
    "attendance.apps.AttendanceConfig",
    "rest_framework",  # Enables Django REST framework (API integration)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5", # Added for Bootstrap 5 template pack
    "schema_graph",
    "formtools",
    "django.contrib.humanize",
    
    
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Login/Logout settings
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'reconciliation:main_dashboard_overview'
LOGOUT_REDIRECT_URL = 'users:login'
AUTH_USER_MODEL = 'users.User'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
