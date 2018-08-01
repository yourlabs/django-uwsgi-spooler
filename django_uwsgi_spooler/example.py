import time

from django import http
from django.views import generic

from .models import Task


def example_callback(task):
    print(task)

    for i in range(0, 100):
        task.output += '\nlol'
        task.progress += 1
        task.save()
        print(f'{task.progress}/{task.total}')
        time.sleep(.1)


class Example(generic.View):
    def get(self, request, *args, **kwargs):
        task = Task(
            callback_name='django_uwsgi_spooler.example.example_callback',
            env=request.GET,
        )
        task.spool()
        return http.HttpResponse(f'Task spooled: {task.pk}')
