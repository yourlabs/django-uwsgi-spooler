from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string

from ipware import get_client_ip
from picklefield.fields import PickledObjectField
from threadlocals.threadlocals import get_current_request


try:
    import uwsgi
except ImportError:
    uwsgi = None


if uwsgi:
    uwsgi.spooler = lambda env: Task.objects.get(
            pk=env[b'uuid'].decode('ascii')
        ).execute()


class Task(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('pending', 'Pending'),
        ('started', 'Started'),
        ('success', 'Success'),
        ('error', 'Error'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    creation_ip = models.GenericIPAddressField(null=True)
    creation_datetime = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    spool_datetime = models.DateTimeField(
        db_index=True,
        null=True,
    )
    start_datetime = models.DateTimeField(
        db_index=True,
        null=True,
    )
    end_datetime = models.DateTimeField(
        db_index=True,
        null=True,
    )
    env = PickledObjectField(null=True)
    callback_name = models.CharField(
        max_length=255,
        db_index=True,
    )
    user = models.ForeignKey(
        getattr(settings, 'AUTH_USER_MODEL', 'auth.User'),
        on_delete=models.SET_NULL,
        null=True,
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    progress = models.IntegerField(default=0)
    total = models.IntegerField(default=100)
    output = models.TextField()
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=15,
        db_index=True,
        default='created',
    )

    class Meta:
        ordering = ('creation_datetime',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_request()

    def parse_request(self):
        try:
            request = get_current_request()
        except:
            request = None
        else:
            try:
                self.creation_ip = get_client_ip(request)[0]
            except:
                pass

            user = getattr(request, 'user', None)
            if getattr(user, 'is_authenticated', False):
                self.user = user

    @property
    def callback(self):
        return import_string(self.callback_name)

    def execute(self):
        self.start_datetime = timezone.now()
        self.status = 'started'
        self.save()
        transaction.commit()

        try:
            self.callback(self)
        except Exception as e:
            self.output += e
            self.status = 'error'
        else:
            self.status = 'success'

        self.end_datetime = timezone.now()
        self.save()
        transaction.commit()

        return getattr(uwsgi, 'SPOOL_OK', True)

    def spool(self):
        self.spool_datetime = timezone.now()
        self.status = 'pending'
        self.save()
        transaction.commit()

        if uwsgi:
            uwsgi.spool({b'uuid': str(self.pk).encode('ascii')})
        else:
            return self.execute()
