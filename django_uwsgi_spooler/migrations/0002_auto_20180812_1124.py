# Generated by Django 2.0.7 on 2018-08-12 09:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('django_uwsgi_spooler', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='execution',
            name='callback_code',
            field=models.TextField(default='', editable=False),
        ),
        migrations.AlterField(
            model_name='execution',
            name='created',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='execution',
            name='ended',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='execution',
            name='output',
            field=models.TextField(default='', editable=False),
        ),
        migrations.AlterField(
            model_name='execution',
            name='started',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='execution',
            name='task',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='django_uwsgi_spooler.Task'),
        ),
        migrations.AlterField(
            model_name='execution',
            name='traceback',
            field=models.TextField(default='', editable=False),
        ),
        migrations.AlterField(
            model_name='task',
            name='created',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='task',
            name='parent',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_uwsgi_spooler.Task'),
        ),
        migrations.AlterField(
            model_name='task',
            name='spooled',
            field=models.DateTimeField(db_index=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.IntegerField(choices=[(0, 'Created'), (1, 'Spooled'), (2, 'Started'), (3, 'Success'), (4, 'Retrying'), (5, 'Failure')], db_index=True, default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='task',
            name='user',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='user_ip',
            field=models.GenericIPAddressField(editable=False, null=True),
        ),
    ]
