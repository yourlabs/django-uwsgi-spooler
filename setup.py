import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='django-uwsgi-spooler',
    version='0.0.0',
    description='Persist uWSGI spooled tasks in uWSGI cache',
    author='James Pic',
    author_email='jpic@yourlabs.org',
    url='https://github.com/yourlabs/django-uwsgi-spooler',
    packages=find_packages('.'),
    include_package_data=True,
    long_description=read('README.rst'),
    keywords='django uwsgi cache spooler',
    extras_require=dict(
        django=[
            'django>=2.0',
            'django-picklefield',
            'django-threadlocals',
            'django-ipware',
        ],
    ),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
