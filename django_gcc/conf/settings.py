from django.conf import settings


MEDIA_URL = getattr(settings, 'COMPRESS_URL', settings.MEDIA_URL)
MEDIA_ROOT = getattr(settings, 'COMPRESS_ROOT', settings.MEDIA_ROOT)
OUTPUT_DIR = getattr(settings, 'COMPRESS_OUTPUT_DIR', 'CACHE')

COMPRESS = getattr(settings, 'COMPRESS', not settings.DEBUG)
COMPRESS_JS_FILTERS = list(getattr(settings, 'COMPRESS_JS_FILTERS', ['django_gcc.filters.google_closure.GoogleClosureCompilerFilter']))