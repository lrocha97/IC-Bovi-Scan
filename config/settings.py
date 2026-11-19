"""
Configurações principais do projeto Django (IC-Bovi-Scan).

Este arquivo define as variáveis de ambiente, aplicativos instalados,
banco de dados, rotas de arquivos estáticos/mídia e documentação OpenAPI/Swagger.
"""

from pathlib import Path
from decouple import config, Csv

# Diretório base do projeto (raiz do repositório)
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações de segurança via decouple (.env)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-umtuy^xf)th8#sj8+*2&2473n5ko!%+w@b(3+ic1$e-khej^$7')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Definição dos Aplicativos
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Configuração de Banco de Dados
# Padrão: SQLite local. Pode ser estendido para PostgreSQL/MySQL via DATABASE_URL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validadores de senha
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalização e Fuso Horário
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos (CSS, JS, Imagens de layout)
STATIC_URL = '/static/'
STATICFILES_DIRS = []

# Arquivos de Mídia (Uploads de usuários e Máscaras geradas pela IA)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuração padrão de chave primária para modelos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework & Documentação OpenAPI
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'BoviScan API',
    'DESCRIPTION': 'API para análise biométrica, segmentação e estimativa de peso corporal de bovinos via Deep Learning.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
