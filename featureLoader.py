import logUtil
import config
import schedule
import threading
import numpy as np
import asyncio
import redis
import json
import traceback
from multiprocessing import Process
class GetPalmOutputList:
    USER_ID = 0
    PALM = 1
    GOLFCLUB_ID = 2

class GetGapOutputList:
    USER_ID = 0
    GAP_0 = 1
    GAP_1 = 2
    GAP_2 = 3
    GAP_3 = 4
    GOLFCLUB_ID = 5

class FeatureLoader:
    """Palm and gap feature handler


    """
    def __init__(self, sqlhandler, log_thread):
        self.sqlhandler = sqlhandler
        self.palm_data=[]
        self.log_thread = log_thread
        self.gap_data=[]
        self.user_data = {}
        self.regits_cnt = 0
        self.rd = redis.StrictRedis(host='10.12.200.127', port=6379, db=0)    
        self.logger = logUtil.get_new_logger(__name__)
        self.get_feature()
        Process(target=self.sub).start()

    def get_feature(self):
        """if booker: 
            get feature data from palm_feature_t and gap_feature_t and get golfclub_id

        """
        self.palm_data = self.sqlhandler.get_palm_feature()
        self.gap_data = self.sqlhandler.get_gap_feature()    
        print(len(self.palm_data), len(self.gap_data))
        #if len(self.palm_data) != len(self.gap_data):
        #self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='GET_FEATURE', full_message='get features matching error'))
        self.dict_maker()
    
    def dict_maker(self):
        """Super dict: {golfclub_id: sub_dict}
            Sub dict: {user_id_n_(palm or gap): (palm or gap) feature}
        """
        try:
            
            idx = 0
            for palm_feature, gap_feature in zip(self.palm_data, self.gap_data):
                if palm_feature['user_id']+ "_"+str(idx) + "_palm" in self.user_data or gap_feature['user_id']+ "_"+str(idx) + "_gap" in self.user_data:
                    idx += 1
                else:
                    idx = 0
                feature_temp = np.frombuffer(palm_feature['feature'], np.float32).tolist()
                
                self.user_data[palm_feature['user_id']+ "_"+str(idx) + "_palm"] = feature_temp
                
                user_gap_feature_list = []
                feature_temp = np.frombuffer(gap_feature['feature_0'], np.float32).tolist()
                user_gap_feature_list.append(feature_temp)
                feature_temp = np.frombuffer(gap_feature['feature_1'], np.float32).tolist()
                user_gap_feature_list.append(feature_temp)
                feature_temp = np.frombuffer(gap_feature['feature_2'], np.float32).tolist()
                user_gap_feature_list.append(feature_temp)
                feature_temp = np.frombuffer(gap_feature['feature_3'], np.float32).tolist()
                user_gap_feature_list.append(feature_temp)
                
                self.user_data[gap_feature['user_id']+ "_"+str(idx) + "_gap"] = user_gap_feature_list
            self.pub()
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DICT_MAKER', full_message='dict maker complete'))
        except Exception as E:
            traceback.print_exc()
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DICT_MAKER', full_message='dict maker error'))
    
    def get_user_feature(self):
        """Get today booker's feature by golfclub
        """
        #self.get_feature()
        #self.user_data = self.rd.get("user_data")
        return self.user_data
    
    def append_feature(self, user_id, palm_feature, gap_0, gap_1, gap_2, gap_3, idx):
        """If booker today regist then append feature space

        """
        try:
            #self.user_data = self.rd.get("user_data")
            self.user_data[user_id+ "_"+str(idx) + "_palm"] = palm_feature
            user_gap_feature_list = []
            
            user_gap_feature_list.append(gap_0)
            user_gap_feature_list.append(gap_1)
            user_gap_feature_list.append(gap_2)
            user_gap_feature_list.append(gap_3)
                
            self.user_data[user_id+ "_"+str(idx) + "_gap"] = user_gap_feature_list
            self.log_thread.queue_put( logUtil.get_graylog_dict_no_user(short_message='APPEND_FEATURE', full_message='append_feature complete'))
        except Exception as E:
            traceback.print_exc()
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='APPEND_FEATURE', full_message='append_feature error'))

    def delete_feature(self, user_id):

        logger = self.logger
        try:
            self.user_data = self.rd.get("user_data")
            for idx in range(5):
                del(self.user_data[user_id + "_" + str(idx) + "_palm"])
                del(self.user_data[user_id + "_" + str(idx) + "_gap"])
            #self.rd.set("user_data", self.user_data)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_FEATURE', full_message='delete_feature complete'))
        except:
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_FEATURE', full_message='delete_feature error'))

    def sub(self):
        p = self.rd.pubsub()
        p.subscribe('user_data')
        for message in p.listen():
            if message.get("type") == "message":
                data = json.loads(message.get("data"))
                print(data)

    def pub(self):
        p = self.rd.pubsub()
        
        res = {str(key).replace('\'','\"'):str(val).replace('\'','\"') for key, val in self.user_data.items()}
        res = json.dumps(res)
        self.rd.publish('user_data',res)

