import pika
from django.conf import settings


url = settings.RABBITMQ_URL
params = pika.URLParameters(url)


class Publisher:
    def __init__(self):
        self.connection = pika.BlockingConnection(params) # Connect to CloudAMQP
        self.channel = self.connection.channel() # start a channel
        self.channel.queue_declare(queue=settings.RABBITMQ_QUEUE, arguments={"x-max-priority": 3})

    def publish_message(self, message, priority):
        self.channel.basic_publish(exchange='', routing_key='qprocesstask-3', body=message, properties=pika.BasicProperties(delivery_mode=2, priority=priority))
        print "Message sent to consumer"
        self.connection.close()
