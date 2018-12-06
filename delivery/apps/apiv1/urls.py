from django.conf.urls import url

from .views import TaskStateUpdateView

app_name = 'apiv1'

urlpatterns = [
    url(r'^tasks/update/$', TaskStateUpdateView.as_view(), name='api-update-task'),
]
