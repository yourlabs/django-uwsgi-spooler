django-uwsgi-spooler
~~~~~~~~~~~~~~~~~~~~

A polyvalent Task model to get the most out of uWSGI's spooler with minimal effort.

Install
=======

Install django-threadlocals if you want automatic provisioning of Task.user and
Task.creation_ip.

This app works without uwsgi installed (ie. runserver), but you can test your
wsgi app with a command like::

    uwsgi --env DEBUG=1 --spooler=/tmp/spool --spooler-processes 16 --http-socket=0.0.0.0:8000 --plugin=python --module=mrs.wsgi:application --honour-stdin

Add ``django_uwsgi_spooler`` to ``INSTALLED_APPS`` and execute migrations with
the ``./manage.py migrate`` command.

``django_uwsgi_spooler.models`` will set uwsgi.spooler so you don't have any
extra setup to do to enjoy uWSGI spooler, besides have it enabled if you want
tasks to actually run in the background.

If you have CRUDLFA+ installed, it will register a CRUD for task, which will
gain a lot of features as we move forward to 1.0 release as you can imagine:
towards full control of the spooler as permited by uWSGI's API.

Usage
=====

Your callback is just a function that takes a task argument::

    def yourcallback(task):
        # do stuff ...

You can start a task as such::

    Task(callback_name='yourmodule.yourcallback').spool()

See a more elaborated example in django_uwsgi_spooler/example.py
