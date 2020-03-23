import pika
import json, time

class rabbitmq_client:
    """
    This class is a rabbitmq message reciever, 
    collects messages with a specific routing key
    :param int host_name: Rabbitmq host name
    :param str routing_key: Routing key for the messages
    """
    def __init__(self, host_name, routing_key=None):
        self.host_name = host_name
        self.routing_key = routing_key

    def __enter__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel = self.connection.channel()
        if self.routing_key is not None:
            self.channel.queue_declare(queue=self.routing_key, durable=True)
        return self

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

    def reconnect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel    = self.connection.channel()
        if self.routing_key is not None:
            self.channel.queue_declare(queue=self.routing_key, durable=True)

    def get_message(self):
        return self.channel.basic_get(queue = self.routing_key, auto_ack= False)
    
    def ack(self, m_delivery_tag):
        self.channel.basic_ack(delivery_tag=m_delivery_tag)

    def reject(self, delivery_tag):
        self.channel.basic_reject(delivery_tag)

    def close_channel(self, p_routing_key):
        self.channel.queue_delete(queue=p_routing_key)

    def __exit__(self ,type, value, traceback):
        self.connection.close()
        pass
