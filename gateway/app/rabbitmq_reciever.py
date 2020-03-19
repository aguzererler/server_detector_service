import pika
import time

class rabbitmq_reciver:
    """
    This class is a rabbitmq message reciever, 
    collects messages with a specific routing key
    :param int host_name: Rabbitmq host name
    :param str routing_key: Routing key for the messages
    """
    def __init__(self, host_name, routing_key):
        self.host_name = host_name
        self.routing_key = routing_key
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.routing_key, durable=True)

    def get_message(self):
        return self.channel.basic_get(queue = self.routing_key, auto_ack= False)
    
    def ack(self, m_delivery_tag):
        self.channel.basic_ack(delivery_tag=m_delivery_tag)

    def reject(self, delivery_tag):
        self.channel.basic_reject(delivery_tag)

    def close_channel(self, p_routing_key):
        self.channel.queue_delete(queue=p_routing_key)

    def __del__(self):
        self.connection.close()
