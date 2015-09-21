import os

SECRET_KEY = os.environ['OPENSHIFT_SECRET_TOKEN']

DEBUG = False


ALLOWED_HOSTS = ['*']


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'nthucourses',
        'USER': os.environ['OPENSHIFT_POSTGRESQL_DB_USERNAME'],
        'PASSWORD': os.environ['OPENSHIFT_POSTGRESQL_DB_PASSWORD'],
    }
}
