import time

class sleep_timeout:
    """
    This class is designed to throw timeout exception for repeating processes
    with wait/sleep time. If execution of a looping process exceeds 
    assigned timeout duration(in seconds) throw error.
    :param int timeout_duration: Timeout duration in seconds
    :param str sleep_duration: Sleep duration  in seconds between iterations
    :param str timeout_message: Message for timeout exception
    """
    def __init__(self, timeout_duration, sleep_duration, timeout_message):
        self.counter = 0 #should be gone
        self.timeout_duration =  timeout_duration
        self.sleep_duration = sleep_duration
        self.timeout_time = time.time() + timeout_duration
        self.timeout_message = timeout_message
        self.check_constraints()

    def sleep(self):
        time.sleep(self.sleep_duration)
        if self.timeout_time < time.time():
            raise Exception(self.timeout_message)
    
    def reset(self):
        self.counter = 0 #should be gone 
        self.timeout_time = time.time() + timeout_duration
        
    def check_constraints(self):
        if self.timeout_duration < self.sleep_duration:
            raise Exception('timeout cannot be smaller than sleep time')
        if self.sleep_duration < 0.01:
            raise Exception('sleep time cannot be smaller than 0.01 sec')