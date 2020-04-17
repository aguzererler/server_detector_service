import pika
import pika.exceptions
import requests
from requests.exceptions import HTTPError
import sys, socket
import random, string, json
import app_config
from apscheduler.schedulers.background import BackgroundScheduler
from utils.sleep_timeout import sleep_timeout
from utils.rabbitmq_client import rabbitmq_client

def find_server_type_in_body(server_type, response):
    return (response.text.find(server_type) != -1)

def find_server_type_in_header(server_type ,response):
    return server_type in response.headers['Server']

def create_url(url):
    # handles host names with "https://" front
    return "https://" + url if (url.find("https://") == -1) else url

def create_bad_url(url, i):
    #single % generally returns bad request, initial 
    return  create_url(url) + "/" + generate_random_bad_word(i) + "%"

def generate_random_bad_word(length):
   puncs = string.punctuation
   return ''.join(random.choice(puncs) for i in range(length))

def generate_bad_reponse(host, no_tries):
    counter = 0
    while counter < no_tries:
        url_bad = create_bad_url(host, counter)
        counter += 1
        try:
            response = requests.get(url_bad)
            if response.status_code >= 400:
                return response
        except:
            return None

def check_server_type_from_response(response, server_type, host):
    # check server type in header attributes 
    # and also in the body of a response to bad request
    try:
        if find_server_type_in_header(server_type, response):
            # checks the server attribute of the header
            return True
        else:
            if response.status_code >= 400:
                return find_server_type_in_body(server_type, response)
                # check the body for server type since nginx server
                # indicates server type in the error page body 
                # unles developers specially remove it
            else:
                return False
        return None
        # returns null if check only made in good request,
        # bad request needs to be checked for better detection
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}') 
    except Exception as err:
        print(f'Other error occurred: {err}')  
    else:
        "error"

def check_server_type(server_type, host):
    url = create_url(host)
    # gererates url from host
    response = requests.get(url)
    env = {'host':host, 'ip': '', 'server_type':''}
    # creates return message object
    is_server_type = check_server_type_from_response(response, server_type, host)
    #checks the result of the normal url
    is_server = False
    if is_server_type == True:
        is_server = True
    elif is_server_type is None :
        # bad response needs to be checked
        bad_response = generate_bad_reponse(host, 3)
        if bad_response is not None:
            if check_server_type_from_response(bad_response, server_type, host):
                is_server = True
    if is_server:
        env['ip'] = socket.gethostbyname(host)
        env['server_type'] = server_type
    return env
    
def establish_connection(connection):
    try:
        connection.process_data_events(0)
        # connects with rabbitmq and keeps connection alive
    except pika.exceptions.AMQPConnectionError:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=app_config.network))
        # reconnects if there is a connection error
    except Exception as err:
        print("Error during mestablishing connection. " + err)

def main():
    try:
        with rabbitmq_client(app_config.network) as sender:
         #create publisher for processed jobs
        
            def callback(ch, method, properties, body):
            # call back function for job queue
                try:
                    print(" [x] Received %r" % body)
                    r_message = json.loads(body)
                    host_name = r_message['host']
                    server_type = r_message['server_type']
                    data = {'host':host_name, 'ip': '', 'server_type':''} #typo
                    try:
                        data = check_server_type(server_type, host_name)
                    except:
                        pass
                    #ignores bad urls, but sends result back to balance the message numbers
                    print(" [x] Done")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(" [x] Ack")
                    sender.send_messeage_channel(data, r_message['requestid'])
                except:
                    print('message error: expected field is not in the message')

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=app_config.network))
            channel = connection.channel()
            # job que listener
            channel.queue_declare(queue=app_config.queue_name_to_detect, durable=True)
            #attaches to job queue
            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.basic_qos(prefetch_count=1)
            # sets message consume limit for single transaction for workers
            # so that jobs can be pickedup by other workers while the initial
            # worker doing its job, then it can get more if there is any
            channel.basic_consume(queue=app_config.queue_name_to_detect, 
                            on_message_callback= callback)

            scheduler = BackgroundScheduler()
            # create schedular to check connection woth rabbitmq so that connection won't get closed
            # rabbitmq closes connection in 60 if there is not heartbeat
            scheduler.add_job(func=establish_connection, args=[connection], trigger='interval', seconds=58)
            scheduler.start()

            channel.start_consuming()
            # start consumption

            
    except Exception as err:
        sys.exit(err)
main()