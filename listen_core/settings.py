import os
from pathlib import Path
from decouple import config
#from dotenv import load_dotenv
import dj_database_url


#load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / 'static' ]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')   #添加一行以准备部署用
#STATIC_ROOT = BASE_DIR / 'staticfiles'

SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = False
#DEBUG = True
#DEBUG = config("DEBUG", default=False, cast=bool)  # 生产环境时设置为 False
#ALLOWED_HOSTS = config("ALLOWED_HOSTS").split(",")
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'listen-app-8hts.onrender.com', '.onrender.com']  # 生产环境时设置为具体的域名或 IP 地址
# （可选但推荐）用于本地调试时启用静态文件服务
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'practice',         # ← 注册我们的新应用
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← 加这行
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'listen_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #'DIRS': [],
        'DIRS': [BASE_DIR / 'templates'],   # ← 全局模板目录
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

WSGI_APPLICATION = 'listen_core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.parse(config("DATABASE_URL"))
}

#postgresql://postgres.fhuqwngqgqbjhwnlrtrq:Mydog8946@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-hans'  # 设置语言为中文

#TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Tokyo'  # 改为东京时区会更合适

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/practice/login/'         # 未登录时跳转地址
LOGIN_REDIRECT_URL = '/practice/'      # 登录后跳转地址（仅用于 Django auth 默认登录）

