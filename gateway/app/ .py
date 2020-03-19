import pika
import json

class rabbitmq_sender:
    def __init__(self, host_name, routing_key):
        self.host_name = host_name
        self.routing_key = routing_key

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host_name))
        self.channel    = self.connection.channel()

        self.channel.queue_declare(queue=self.routing_key, durable=True)
    
    def send_message(self, message):
        self.channel.basic_publish(exchange='',
                            routing_key=self.routing_key,
                            body=json.dumps(message),
                            properties=pika.BasicProperties(
                                delivery_mode = 2,
                            ))
    def __del__(self):
        self.connection.close()