from flask import Flask
from flask import request
import json, time
from rabbitmq_sender import rabbitmq_sender
from rabbitmq_reciever import rabbitmq_reciver
import app_config
import uuid, string, random
from sleep_timeout import sleep_timeout 

app = Flask(__name__)

@app.route('/serverdetect/', methods=['POST'])
def serverdetect():
    if request.is_json:
        content = request.get_json()
        if 'server_type' in content:
            server_type = content['server_type']
            # desired server type to check
            if 'hosts' in content:
                requestid = uuid.uuid4().hex
                # requests uuid, used to create unique rabbitmq queues for each request
                sender = rabbitmq_sender(app_config.network, app_config.queue_name_to_detect)
                # message sender for workers with job queue key
                sender.purge_queue()
                # Purges messages in the queue so that 
                # job messages from different requests do not get mixed,
                # purge is used for development purposes, 
                # when there are messages in the job queue from different requests
                # workers hang when they send old request's results and does not get acknowledge
                # Note that service only collects its current request's messages
                for host in content['hosts']:
                    # split host list so that multiple workers can pick one by one
                    try:
                        message = {'requestid': requestid, 
                                    'server_type': server_type, 
                                    'host':host}
                        # message object:
                        # requestid is going to be used to create a unique queue for worker responses
                        # server_type : sever type that is wanted to be detected
                        # host: host
                        sender.send_message(message)
                        # send message to job que so that workers can pick up
                    except:
                        return 'message broker is down'
                host_list = collect_messages(requestid, len(content['hosts']))
                return json.dumps(host_list)
            else:
                return "wrong input: \"hosts\" is missing"  
        else:
            return "wrong input: \" server_type\"  is missing"
    else:
        return "wrong input format"
    #create reciver connection and wait for messeges
    return ""

def collect_messages(requestid, no_messages):
    #gathers messages from workers and produces output

    m_collection = {}
    # collection object for selected messages
    m_counter = 0
    # collected message counter, is used to end message pull loop
    reciver = rabbitmq_reciver(app_config.network, requestid)
    # create rabbitmq reciever for request's queue
    timeout = sleep_timeout(30, 0.4, 'Timeout: no message in the queue:' + requestid)
    # timeout object for message check loop
    while m_counter != no_messages:
        # checks if we collected all reply messages for all hosts,
        # if ends the loop 
        method_frame, header_frame, body = reciver.get_message()
        if method_frame is None or method_frame.NAME == 'Basic.GetEmpty':
          timeout.sleep()
          #waits for worker/s to finish processing
        else:
            timeout.reset()
            try:
                r_message = json.loads(body)
                m_counter = m_counter + 1
                reciver.ack(method_frame.delivery_tag)
                if r_message['server_type'] != '':
                    # add messages ith server type assigned to output collector
                    # null server type means that server type is not 
                    # detected as desired server type
                    ip_a = [r_message['ip']]
                    m_collection[r_message['host']] = ip_a
            except Exception as err:
                print('message error: ' + err)
    reciver.close_channel(requestid)
    # close request channel after collection of all the messages
    return m_collection

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')