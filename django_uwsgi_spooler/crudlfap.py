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
                'callback',
                'spooled',
                'status',
            ],
            search_fields=[
                'callback',
                'output',
            ],
        ),
        crudlfap.DetailView,
        crudlfap.DeleteObjectsView,
        crudlfap.DeleteView,
    ]
).register()
