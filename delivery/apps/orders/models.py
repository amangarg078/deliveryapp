# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid
import json
from channels import Group

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Max, Count, IntegerField, Case, When, Q, F, OuterRef, Subquery


from .managers import TaskManager
from .rabbitmq_publisher import Publisher


class AvailableUserTypes(object):
    store_manager = "SM"
    delivery_person = "DP"


CHOICES_USER_TYPE = (
    (AvailableUserTypes.store_manager, "Store Manager"),
    (AvailableUserTypes.delivery_person, "Delivery Person")
)


class AvailableTaskPriority(object):
    high = "high"
    medium = "medium"
    low = "low"


PRIORITY_MAPPING = {
    AvailableTaskPriority.high: 3,
    AvailableTaskPriority.medium: 2,
    AvailableTaskPriority.low: 1,
}


CHOICES_TASK_PRIORITY = (
    (AvailableTaskPriority.high, "High"),
    (AvailableTaskPriority.medium, "Medium"),
    (AvailableTaskPriority.low, "Low"),
)


class AvailableTaskStates(object):
    new = "new"
    accepted = "accepted"
    completed = "completed"
    declined = "declined"
    cancelled = "cancelled"


CHOICES_TASK_STATE = (
    (AvailableTaskStates.new, "New"),
    (AvailableTaskStates.accepted, "Accepted"),
    (AvailableTaskStates.completed, "Completed"),
    (AvailableTaskStates.declined, "Declined"),
    (AvailableTaskStates.cancelled, "Cancelled"),
)


class User(AbstractUser):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_type = models.CharField(max_length=2, null=True, blank=True, choices=CHOICES_USER_TYPE)

    def is_store_manager(self):
        if self.user_type == AvailableUserTypes.store_manager:
            return True
        return False

    @property
    def get_websocket_group(self):
        """
        Returns the Channels Group that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return Group("user-%s" % self.uid)


class BaseModel(models.Model):
    created_on = models.DateTimeField(null=True, default=timezone.now)
    last_modified_on = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        abstract = True


class Task(BaseModel):
    uid = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=512)
    priority = models.CharField(max_length=6, choices=CHOICES_TASK_PRIORITY, default=AvailableTaskPriority.high)
    state = models.CharField(max_length=10, choices=CHOICES_TASK_STATE, default=AvailableTaskStates.new)
    created_by = models.ForeignKey(User, related_name="created_by")
    assigned_to = models.ForeignKey(User, related_name="assigned_to", null=True, blank=True)

    objects = TaskManager()

    def __unicode__(self):
        return self.title

    def get_state_transitions(self):
        return self.taskstate_set.all().order_by('-created_on')

    def get_message_content(self):
        data = {}
        data['task_id'] = str(self.uid)
        data['title'] = self.title
        data['state'] = self.state
        data['assigned_to'] = self.assigned_to.username if self.assigned_to else "-"
        data['priority'] = self.priority
        return data


class TaskState(BaseModel):
    task = models.ForeignKey(Task)
    state = models.CharField(max_length=5, choices=CHOICES_TASK_STATE, default=AvailableTaskStates.new)
    delivery_person = models.ForeignKey(User, related_name="delivery_person", null=True, blank=True)

    def __unicode__(self):
        return self.task.title


def task_manager(body):
    body_dict = json.loads(body)
    try:
        task = Task.objects.get(uid=body_dict.get('task_id'))
        available_delivery_persons = User.objects.filter(user_type=AvailableUserTypes.delivery_person).annotate(assinged_count=Count(Case(When(assigned_to__state=AvailableTaskStates.accepted,then=1)))).filter(assinged_count__lte=3)
        assigned_to = available_delivery_persons.first()  #routing logic to come here
        if assigned_to:
            task.assigned_to = assigned_to
            task.save()
            return True
    except Task.DoesNotExist:
        pass
    return False


@receiver(post_save, sender=Task, dispatch_uid='task_post_save_handler')
def task_post_save_handler(sender, instance, created, using, **kwargs):
    if created:
        TaskState.objects.create(task=instance)
    else:
        last_task_state = TaskState.objects.filter(task=instance).order_by('-created_on').first()
        if last_task_state.state != instance.state or last_task_state.delivery_person != instance.assigned_to:
            TaskState.objects.create(task=instance, state=instance.state, delivery_person=instance.assigned_to)

    message_content_store_owner = instance.get_message_content()
    message_content_delivery_person = message_content_store_owner.copy()

    store_manager = instance.created_by
    message_content_store_owner['user_type'] = store_manager.user_type

    store_manager.get_websocket_group.send({
        'text': json.dumps(message_content_store_owner)
    })

    delivery_person = instance.assigned_to
    if delivery_person:
        message_content_delivery_person['user_type'] = delivery_person.user_type

        if instance.state in [AvailableTaskStates.declined, AvailableTaskStates.cancelled]:
            message_content_delivery_person['action'] = "remove"
        if instance.state == AvailableTaskStates.accepted:
            message_content_delivery_person['action'] = "accepted_links"
        delivery_person.get_websocket_group.send({
            'text': json.dumps(message_content_delivery_person)
        })

    if instance.state in [AvailableTaskStates.new, AvailableTaskStates.declined] and not instance.assigned_to:
        msg = json.dumps({'task_id': str(instance.uid)})
        Publisher().publish_message(msg, PRIORITY_MAPPING.get(instance.priority))

