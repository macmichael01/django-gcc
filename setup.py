import os

from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

README = read('README')

setup(
    name = "django-gcc",
    version = "0.99",
    description='django-gcc (Django Google Closure Compiler) is an easy way to compress JavaScript files on the fly',
    url = 'http://github.com/macmichael01/django-gcc',
    license = 'BSD',
    long_description=README,

    author = 'Chris McMichael',
    author_email = 'macmichael01@gmail.com',
    packages = [
        'django_gcc',
        'django_gcc.conf',
        'django_gcc.filters',
        'django_gcc.templatetags',
    ],
    package_data = {'compressor': ['templates/django_gcc/*.html']},
    requires = [
        'BeautifulSoup',
    ],
    zip_safe = False,
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
