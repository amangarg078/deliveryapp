from django.db import models


class TaskManager(models.Manager):

    def get_tasks_for_user(self, user):
        from .models import AvailableUserTypes, AvailableTaskStates

        if user.user_type == AvailableUserTypes.store_manager:
            return self.filter(created_by=user).order_by('-last_modified_on', '-priority')

        elif user.user_type == AvailableUserTypes.delivery_person:
            return self.filter(assigned_to=user).exclude(state__in=[AvailableTaskStates.declined, AvailableTaskStates.cancelled]).order_by('-priority', '-last_modified_on')
        return self.all()

    def get_task_by_uid(self, user, task_id):
        return self.get_tasks_for_user(user).get(uid=task_id)
