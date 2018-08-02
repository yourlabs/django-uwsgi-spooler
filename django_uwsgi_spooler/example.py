import time

from django import http
from django.views import generic

from .models import Task


def example_subcallback(task):
    task.output += f'Sleeping {task.data} seconds !'
    time.sleep(task.data)
    task.output += f'\nSleept {task.data} seconds !'
    crash


def example_callback(task):
    for i in range(0, task.data):
        Task(
            callback='django_uwsgi_spooler.example.example_subcallback',
            data=i,
            parent=task,
        ).spool()


class Example(generic.View):
    def get(self, request, *args, **kwargs):
        task = Task(
            callback='django_uwsgi_spooler.example.example_callback',
            data=request.GET.get('count', 10),
        ).spool()

        if getattr(task, 'get_absolute_url', None):
            return http.HttpResponseRedirect(
                task.get_absolute_url()
            )
        else:
            return http.HttpResponse(f'Task spooled: {task.pk}')
