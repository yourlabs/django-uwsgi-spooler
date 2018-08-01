from crudlfap import crudlfap

from django_filters import filters

from .models import Task


crudlfap.Router(
    Task,
    material_icon='sync',
    views=[
        crudlfap.ListView.clone(
            filterset_extra_class_attributes=dict(
                status=filters.ChoiceFilter(choices=Task.STATUS_CHOICES)
            ),
            table_fields=[
                'id',
                'callback_name',
                'spool_datetime',
                'status',
            ],
            search_fields=[
                'callback_name',
                'output',
            ],
        ),
        crudlfap.DetailView,
        crudlfap.DeleteObjectsView,
        crudlfap.DeleteView,
    ]
).register()
