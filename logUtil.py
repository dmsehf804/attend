import logging
import config
import graypy
import json
import os
from subprocess import call
from queue import Queue
from threading import Thread
def get_new_logger(name='basic'):
    """logger instance maker
    
    Args:
        name(str): logger name
    
    Return:
        new_logger(logging): log instance
    """
    new_logger = logging.getLogger(name)
    new_logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    #file_handler = logging.FileHandler('./log.log')

    gelf_udp_handler = graypy.GELFUDPHandler(config.GRAYLOG_HTTP_ADDR, config.GRAYLOG_PORT)

    new_logger.addHandler(gelf_udp_handler)
    new_logger.addHandler(stream_handler)
    #new_logger.addHandler(file_handler)

    return new_logger

def get_graylog_dict(short_message, full_message, user_info):
    
    graylog_dict = {
        "facility": config.FACILITY_NAME,
        "version": config.VERSION,
        "service_type": config.DEV,
        "short_m": short_message,
        "message": full_message,
        "_user_id": str(user_info.get_user_id()),
        "server_os_info": config.HOST_OS,
        "server_addr_ip": config.HOST_IP_EXTERNAL,
        "server_host_name": config.HOST_NAME,
    }
    graylog_dict = json.dumps(graylog_dict)
    
    return graylog_dict

def get_graylog_dict_no_user(short_message, full_message):
    
    graylog_dict = {
        "facility": config.FACILITY_NAME,
        "version": config.VERSION,
        "service_type": config.DEV,
        "short_m": short_message,
        "message": full_message,
        "server_os_info": config.HOST_OS,
        "server_addr_ip": config.HOST_IP_EXTERNAL,
        "server_host_name": config.HOST_NAME,
    }
    graylog_dict = json.dumps(graylog_dict)
    
    return graylog_dict

def get_graylog_dict_no_user_acc(short_message, full_message, acc):

    graylog_dict = {
        "facility": config.FACILITY_NAME,
        "version": config.VERSION,
        "service_type": config.DEV,
        "short_m": short_message,
        "message": full_message,
        "server_os_info": config.HOST_OS,
        "server_addr_ip": config.HOST_IP_EXTERNAL,
        "server_host_name": config.HOST_NAME,
        "accuracy": acc
    }
    graylog_dict = json.dumps(graylog_dict)

    return graylog_dict

async def send_log(logger, log_dict):
    logger.debug(log_dict)

async def send_log_exc(logger, log_dict):
    logger.debug(log_dict, exc_info=1)

class logThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.log_queue = Queue()
        #self.log_thread = Thread(target=self.send_graylog)
        #self.log_thread.start()

    def run(self):
        new_logger = logging.getLogger('log')
        new_logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)

        gelf_udp_handler = graypy.GELFUDPHandler(config.GRAYLOG_HTTP_ADDR, config.GRAYLOG_PORT)

        new_logger.addHandler(gelf_udp_handler)
 

        while True:
            try:
                message = self.log_queue.get()
                if message is None:
                    continue
                #print(message)
                new_logger.debug(message) 
            except queue.Empty:
                pass
            except Exception as e:
                print(e)


    def queue_put(self, data):
        self.log_queue.put(data)
        

    def queue_get(self):
        return self.log_queue.get()

