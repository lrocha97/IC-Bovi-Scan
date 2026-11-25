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
# Padrão seguro: DEBUG falso por padrão (habilitável explicitamente via DEBUG=True no .env)
DEBUG = config('DEBUG', default=False, cast=bool)

# Em produção, a ausência de SECRET_KEY gera erro crítico. Em desenvolvimento (DEBUG=True),
# permite uma chave de desenvolvimento caso o desenvolvedor ainda não tenha preenchido o .env.
if DEBUG:
    SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-do-not-use-in-production')
else:
    SECRET_KEY = config('SECRET_KEY')

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
def parse_database_url(url_string, base_dir=None):
    """
    Interpreta uma DATABASE_URL e retorna o dicionario de configuracao para o Django DATABASES.
    Valida esquemas suportados e preserva barras iniciais em caminhos absolutos SQLite.
    """
    import re
    from urllib.parse import urlparse

    engine_map = {
        'postgres': 'django.db.backends.postgresql',
        'postgresql': 'django.db.backends.postgresql',
        'mysql': 'django.db.backends.mysql',
        'sqlite': 'django.db.backends.sqlite3',
    }
    parsed = urlparse(url_string)
    scheme = (parsed.scheme or '').lower()
    if scheme not in engine_map:
        raise ValueError(
            f"Esquema de banco de dados não suportado na DATABASE_URL: '{scheme}'. "
            f"Esquemas válidos são: {', '.join(sorted(engine_map.keys()))}."
        )

    if scheme == 'sqlite':
        raw_path = parsed.path or ''
        if raw_path in ('/:memory:', ':memory:'):
            db_name = ':memory:'
        elif raw_path.startswith('//'):
            # Preserva a barra inicial para caminhos absolutos Unix (ex: sqlite:////tmp/boviscan.sqlite3 -> /tmp/boviscan.sqlite3)
            db_name = raw_path[1:]
        elif re.match(r'^/[a-zA-Z]:', raw_path):
            # Caminho absoluto Windows com letra de unidade (ex: sqlite:///C:/data/db.sqlite3 -> C:/data/db.sqlite3)
            db_name = raw_path[1:]
        elif raw_path:
            # Caminho relativo (ex: sqlite:///db.sqlite3 -> db.sqlite3)
            db_name = raw_path.lstrip('/')
        else:
            db_name = str((base_dir / 'db.sqlite3') if base_dir else 'db.sqlite3')
    else:
        db_name = parsed.path.lstrip('/') if parsed.path else ''

    return {
        'ENGINE': engine_map[scheme],
        'NAME': db_name,
        'USER': parsed.username or '',
        'PASSWORD': parsed.password or '',
        'HOST': parsed.hostname or '',
        'PORT': parsed.port or '',
    }


# Padrão: SQLite local. Suporta PostgreSQL ou MySQL se DATABASE_URL estiver presente no .env
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': parse_database_url(DATABASE_URL, base_dir=BASE_DIR)
    }
else:
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

# Redirecionamento de login para as páginas protegidas (histórico de análises)
LOGIN_URL = '/admin/login/'

# Configuração padrão de chave primária para modelos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework & Documentação OpenAPI
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '120/minute',
    },
}

# Políticas de Segurança e Limites de Recursos para Inferência
MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024  # Limite máximo de 10 MB por upload

# Autenticação no endpoint de inferência:
# Padrão seguro (production-ready): Autenticação obrigatória (REQUIRE_AUTH_FOR_INFERENCE = True).
# Em produção (DEBUG=False), a autenticação é estritamente obrigatória para proteger recursos de hardware e disco.
# Em desenvolvimento local (DEBUG=True), permite opt-out explícito definindo ALLOW_ANONYMOUS_INFERENCE=True no .env.
ALLOW_ANONYMOUS_INFERENCE = config('ALLOW_ANONYMOUS_INFERENCE', default=None)
if ALLOW_ANONYMOUS_INFERENCE is not None:
    opt_out_anonymous = config('ALLOW_ANONYMOUS_INFERENCE', cast=bool)
else:
    # Retrocompatibilidade caso o desenvolvedor utilize REQUIRE_AUTH_FOR_INFERENCE no .env
    req_auth_env = config('REQUIRE_AUTH_FOR_INFERENCE', default=None)
    opt_out_anonymous = (not config('REQUIRE_AUTH_FOR_INFERENCE', cast=bool)) if req_auth_env is not None else False

if not DEBUG:
    # Em produção, a autenticação é sempre obrigatória por padrão seguro
    REQUIRE_AUTH_FOR_INFERENCE = True
else:
    # Em desenvolvimento (DEBUG=True), respeita o opt-out explícito
    REQUIRE_AUTH_FOR_INFERENCE = not opt_out_anonymous

SPECTACULAR_SETTINGS = {
    'TITLE': 'BoviScan API',
    'DESCRIPTION': 'API para análise biométrica, segmentação e estimativa de peso corporal de bovinos via Deep Learning.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
