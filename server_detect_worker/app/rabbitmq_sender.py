import pika
import json

class rabbitmq_sender:
    """
    This class is a rabbitmq message sender/publisher, 
    send messages with a specific routing key
    :param int host_name: Rabbitmq host name
    :param bool purge: Purge messages in the queue
    :param str routing_key: Routing key for the messages, if sets 
    declares the channel during initialization
    """
    def __init__(self, host_name, routing_key=None):
        self.host_name = host_name
        self.routing_key = routing_key

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel    = self.connection.channel()
        if routing_key is not None:
            self.channel.queue_declare(queue=self.routing_key, durable=True)

    def reconnect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel    = self.connection.channel()
        if self.routing_key is not None:
            self.channel.queue_declare(queue=self.routing_key, durable=True)

    def send_message(self, message):
        self.channel.basic_publish(exchange='',
                            routing_key=self.routing_key,
                            body=json.dumps(message),
                            properties=pika.BasicProperties(
                                delivery_mode = 2,
                            ))

    def send_messeage_channel(self, message, p_routing_key):
        # declares channel and send/publish messages on that queue
        self.channel.queue_declare(queue=p_routing_key, durable=True)
        self.channel.basic_publish(exchange='',
                            routing_key=p_routing_key,
                            body=json.dumps(message),
                            properties=pika.BasicProperties(
                                delivery_mode = 2,
                            ))

    def purge_queue(self):
        self.channel.queue_purge(queue=self.routing_key)

    def __del__(self):
        self.connection.close()