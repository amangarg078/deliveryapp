import pika

from django.core.management.base import BaseCommand
from ....orders.models import Task, User, task_manager
from django.utils import timezone
from django.conf import settings


# create a function which is called on incoming messages
def callback(ch, method, properties, body):
    print body
    ack = task_manager(body)
    if ack:
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        # if task not assigned to anyone
        ch.basic_reject(delivery_tag=method.delivery_tag, requeue=True)


class Command(BaseCommand):
    """consumer for rabbitmq"""

    def handle(self, *args, **options):
        url = settings.RABBITMQ_URL
        params = pika.URLParameters(url)

        while True:
            connection = pika.BlockingConnection(params)
            channel = connection.channel() # start a channel
            channel.queue_declare(queue=settings.RABBITMQ_QUEUE, arguments={"x-max-priority": 3})

            # set up subscription on the queue
            channel.basic_consume(callback, queue=settings.RABBITMQ_QUEUE, no_ack=False)

            # start consuming (blocks)
            channel.start_consuming()

