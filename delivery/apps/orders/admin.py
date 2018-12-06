# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.template.defaultfilters import truncatechars  # or truncatewords

from .models import User, Task

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ['short_title', 'created_by', 'state', 'priority']
    list_filter = ['created_by', 'assigned_to']
    search_fields = ['created_by__email', 'created_by__username', 'title', 'assigned_to__email', 'assigned_to__username']

    def short_title(self, obj):
        return truncatechars(obj.title, 100)


admin.site.register(Task, TaskAdmin)
admin.site.register(User)
