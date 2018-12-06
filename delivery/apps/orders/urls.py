from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from .views import Dashboard, TaskCreateView, TaskDetailView

app_name = 'orders'

urlpatterns = [
    url(r'^$', login_required(Dashboard.as_view()), name='dashboard'),
    url(r'^tasks/create/$', login_required(TaskCreateView.as_view()), name='task-create-view'),
    url(r'^tasks/(?P<uid>[0-9A-Fa-f-]+)/$', login_required(TaskDetailView.as_view()), name='task-detail-view'),
]
