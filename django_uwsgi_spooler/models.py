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
    STATUS_ERROR   = 4

    STATUS_CHOICES = (
        (STATUS_CREATED, _('Created')),
        (STATUS_SPOOLED, _('Spooled')),
        (STATUS_STARTED, _('Started')),
        (STATUS_SUCCESS, _('Success')),
        (STATUS_ERROR,   _('Error')),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_ip = models.GenericIPAddressField(null=True)
    created = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    spooled = models.DateTimeField(
        db_index=True,
        null=True,
    )
    started = models.DateTimeField(
        db_index=True,
        null=True,
    )
    ended = models.DateTimeField(
        db_index=True,
        null=True,
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
    )
    output = models.TextField()
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        db_index=True,
        default=0,
    )

    class Meta:
        ordering = ('created',)

    @property
    def python_callback(self):
        return import_string(self.callback)

    def set_status(self, status, commit=True):
        self.status = getattr(self, f'STATUS_{status}'.upper())

        if self.status in (self.STATUS_ERROR, self.STATUS_SUCCESS):
            self.ended = timezone.now()
        elif self.status == self.STATUS_STARTED:
            self.started = timezone.now()
        elif self.status == self.STATUS_SPOOLED:
            self.spooled = timezone.now()

        if commit:
            self.save()
            transaction.commit()

    def execute(self):
        self.set_status('started')

        try:
            self.python_callback(self)
        except Exception as e:
            tt, value, tb = sys.exc_info()
            self.output += '\n'
            self.output += '\n'.join(traceback.format_exception(tt, value, tb))
            self.set_status('error')
            raise
        else:
            self.set_status('success')
            return getattr(uwsgi, 'SPOOL_OK', True)

    def spool(self):
        self.set_status('spooled')
        transaction.commit()

        if uwsgi:
            print('SPOOL')
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
