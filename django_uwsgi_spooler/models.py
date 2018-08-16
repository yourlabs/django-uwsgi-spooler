import inspect
import sys
import traceback
from uuid import uuid4, UUID

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import signals
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from ipware import get_client_ip
from picklefield.fields import PickledObjectField
from threadlocals.threadlocals import get_current_request


try:
    import uwsgi
except ImportError:
    uwsgi = None


def spooler(env):
    pk = UUID(env[b'uuid'].decode('ascii'))
    task = Task.objects.filter(pk=pk).first()
    if task:
        task.execute()
    return getattr(uwsgi, 'SPOOL_OK', True)


if uwsgi:
    uwsgi.spooler = spooler


class Task(models.Model):
    STATUS_CREATED = 0
    STATUS_SPOOLED = 1
    STATUS_STARTED = 2
    STATUS_SUCCESS = 3
    STATUS_RETRYING = 4
    STATUS_FAILURE = 5

    STATUS_CHOICES = (
        (STATUS_CREATED, _('Created')),
        (STATUS_SPOOLED, _('Spooled')),
        (STATUS_STARTED, _('Started')),
        (STATUS_SUCCESS, _('Success')),
        (STATUS_RETRYING, _('Retrying')),
        (STATUS_FAILURE, _('Failure')),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_ip = models.GenericIPAddressField(null=True, editable=False)
    created = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
    )
    spooled = models.DateTimeField(
        db_index=True,
        null=True,
        editable=False,
    )
    data = PickledObjectField(null=True)
    callback = models.CharField(
        max_length=255,
        db_index=True,
    )
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        on_delete=models.SET_NULL,
        null=True,
        editable=False,
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        editable=False,
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        db_index=True,
        default=0,
        editable=False,
    )
    max_executions = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ('-created',)

    @property
    def last_execution(self):
        return self.execution_set.order_by('-created').first()

    @property
    def python_callback(self):
        return import_string(self.callback)

    @property
    def callback_code(self):
        return inspect.getsource(self.python_callback)

    def save_status(self, status, commit=True):
        self.status = getattr(self, f'STATUS_{status}'.upper())

        if self.status in (self.STATUS_FAILURE, self.STATUS_SUCCESS):
            self.ended = timezone.now()
        elif (self.status == self.STATUS_STARTED and
                self.status == self.STATUS_FAILURE):
            self.status = self.STATUS_RETRYING

        elif self.status == self.STATUS_STARTED:
            self.started = timezone.now()
        elif self.status == self.STATUS_SPOOLED:
            self.spooled = timezone.now()

        if commit:
            self.save()
            transaction.commit()

    def execute(self):
        self.save_status('started')
        execution = self.execution_set.create(
            started=timezone.now(),
            callback_code=self.callback_code,
        )

        try:
            self.python_callback(execution)
        except Exception as e:
            tt, value, tb = sys.exc_info()
            execution.traceback += '\n'.join(
                traceback.format_exception(tt, value, tb)
            )
            execution.save_status('failure')
            executions = len(self.execution_set.all())
            if self.max_executions and self.max_executions > executions:
                # Stop the spooler from retrying
                return getattr(uwsgi, 'SPOOL_OK', True)
            raise
        else:
            execution.save_status('success')
            return getattr(uwsgi, 'SPOOL_OK', True)

    def spool(self):
        self.save_status('spooled')

        if uwsgi:
            uwsgi.spool({b'uuid': str(self.pk).encode('ascii')})
        else:
            self.execute()

        return self


def process_request(sender, instance, **kwargs):
    if instance.user or instance.user_ip:
        return

    try:
        request = get_current_request()
    except:
        request = None
    else:
        try:
            self.user_ip = get_client_ip(request)[0]
        except:
            pass

        user = getattr(request, 'user', None)
        if getattr(user, 'is_authenticated', False):
            self.user = user
signals.pre_save.connect(process_request, sender=Task)


class Execution(models.Model):
    STATUS_STARTED = Task.STATUS_STARTED
    STATUS_SUCCESS = Task.STATUS_SUCCESS
    STATUS_FAILURE = Task.STATUS_FAILURE

    STATUS_CHOICES = (
        (STATUS_STARTED, _('Started')),
        (STATUS_SUCCESS, _('Success')),
        (STATUS_FAILURE, _('Failure')),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, editable=False)
    created = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        editable=False,
    )
    started = models.DateTimeField(
        db_index=True,
        null=True,
        editable=False,
    )
    ended = models.DateTimeField(
        db_index=True,
        null=True,
        editable=False,
    )
    output = models.TextField(default='', editable=False)
    traceback = models.TextField(default='', editable=False)
    callback_code = models.TextField(
        editable=False,
        default='',
    )
    status = models.IntegerField(
        choices=Task.STATUS_CHOICES,
        db_index=True,
        default=0,
        editable=False,
    )

    class Meta:
        ordering = ('started',)

    def save_status(self, status, commit=True):
        self.status = getattr(self, f'STATUS_{status}'.upper())

        if self.status in (self.STATUS_FAILURE, self.STATUS_SUCCESS):
            self.ended = timezone.now()
        elif self.status == self.STATUS_STARTED:
            self.started = timezone.now()

        if commit:
            self.save()
            transaction.commit()

        self.task.save_status(status)

    def execute(self):
        self.save_status('started')

        try:
            self.python_callback(self)
        except Exception as e:
            tt, value, tb = sys.exc_info()
            self.exception = '\n'.join(traceback.format_exception(tt, value, tb))
            self.save_status('failure')
            raise
        else:
            self.save_status('success')
