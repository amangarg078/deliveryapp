# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import dateparse, timezone
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView, DetailView, RedirectView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from django.core.urlresolvers import reverse
from django.contrib import messages

from django.conf import settings

from .models import *


class GetTaskObjectMixin(object):
    def get_object(self, *args, **kwargs):
        self.object = None
        task_id = self.kwargs.get('uid', None)
        if task_id:
            try:
                task = Task.objects.get_task_by_uid(self.request.user, task_id)
            except Task.DoesNotExist:
                raise Http404('No Task matches the given query.')
            self.object = task
            return task
        else:
            return None


class Dashboard(ListView):
    model = Task
    template_name = 'index/dashboard.html'

    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return self.model.objects.get_tasks_for_user(user)


class TaskCreateView(CreateView):
    template_name = "index/task_create_view.html"
    model = Task
    fields = ['title', 'priority']

    def form_valid(self, form):
        obj = form.save(commit=False)
        # Task form is only available to store owner
        obj.created_by = self.request.user
        obj.save()
        self.object = obj
        return super(TaskCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('orders:dashboard')


class TaskDetailView(GetTaskObjectMixin, DetailView):
    model = Task
    template_name = "index/task_detail_view.html"

