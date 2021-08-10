import pymysql
import config
import logUtil

import pymysql
import config
import logUtil
import time
import traceback
from pymysqlpool.pool import Pool
class SQLHandler:
    def __init__(self, log_thread):
        self.pool = Pool(host=config.HOST,
                                    user=config.DB_USER,
                                    password=config.PW
                                    )
        self.log_thread = log_thread

    def pool_init(self):
        conn = None
        cursor = None
        try:
            conn = self.pool.get_conn()

            conn.ping(reconnect=True)
            cursor = conn.cursor()
            cursor.execute('use '+config.DB_NAME)
            conn.commit()

            print('use db')
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='USE_PALMDB', full_message='pool init use'+ config.DB_NAME+' complete'))
        except Exception as E:
            traceback.print_exc()
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='USE_PALMDB', full_message='pool init use'+ config.DB_NAME+' error'))
        return cursor, conn

    def __del__(self):
        self.cursor.close()
        self.conn.close()


    def insert_regist_feature(self, user_id, idx, palm_feature, index_feature, middle_feature, ring_feature, pinky_feature, model_version):
        """Insert regist user's feature data in feature(palm, gap) table

        Args:
            user_id         (str)           : user_id data
            idx             (int)           : index of feature
            palm_feature    (numpy array)   : palm feature data - vector
            finger_features (numpy array)   : fingers feature data - vector (index, midd$
            model_version   (str)           : model_version data 1.0 etc...

        Return:
            dict: result_code, result_message
        """
        cursor, conn = self.pool_init()
        insert_tuple_data_palm = (user_id, idx, palm_feature, index_feature, middle_feature, ring_feature, pinky_feature, model_version)

        try:
            cursor.execute('call insert_regist_feature(%s, %s, %s, %s, %s, %s, %s, %s)', insert_tuple_data_palm)
            result_code = config.CODE_0
            conn.commit()
            result_message = 'Insert regist feature table complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='INSERT_FEATURE', full_message=result_message))
        except Exception as E:
            result_code = config.CODE_1003
            result_message = 'Insert regist feature table error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='INSERT_FEATURE', full_message=result_message))

        return {'result_code': result_code,
                'result_message': str(result_message)}

    def delete_palm_feature_by_uid(self, user_id):
        """Delete palm feature data in palm_feature_t with user_id condition

        Args:
            user_id       (str)   : user_id of where condition

        Return:
            dict: result_code, result_message
        """

        try:

            cursor, conn = self.pool_init()
            cursor.execute('call delete_palm_feature_by_uid(%s)', (user_id))
            result_code = config.CODE_0
            conn.commit()
            result_message = 'Delete palm feature complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_PALM', full_message=result_message))
        except Exception as E:
            traceback.print_exc()
            result_message = 'Delete palm by user_id error'
            result_code = config.CODE_1005

            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_PALM', full_message=result_message))

        return {'result_code': result_code,
                'result_message': result_message}


    def delete_gap_feature_by_uid(self, user_id):
        """Delete gap feature data in gap_feature_t with user_id condition

        Args:
            user_id       (str)   : user_id of where condition

        Return:
            dict: result_code, result_message
        """

        try:

            cursor, conn = self.pool_init()

            cursor.execute('call delete_gap_feature_by_uid(%s)', (user_id))
            result_code = config.CODE_0
            conn.commit()
            result_message = 'Delete gap feature complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_GAP', full_message=result_message))
        except Exception as E:
            result_message = 'Delete gap feature error'
            result_code = config.CODE_1005
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_GAP', full_message=result_message))

        return {'result_code': result_code,
                'result_message': result_message}

    def is_regist(self, user_id):
        """Select all palm feature data in table for embedding

        Return:
            dict: result, result_code, result_message
        """

        result = []
        result_output = False
        try:

            cursor, conn = self.pool_init()
            cursor.execute('call is_regist(%s)', user_id)
            result_code = config.CODE_0
            result = cursor.fetchone()
            result_message = 'is_regist select complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        except Exception as E:
            traceback.print_exc()
            result_code = config.CODE_1006
            result_message = 'is_regist select error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        print(result)
        if not result:
            result_output = False
        else:
            result_output = True
        return {'result': result_output,
                'result_code': result_code,
                'result_message': str(result_message)}


    def get_booker_flag(self, user_id):
        """Select all palm feature data in table for embedding

        Return:
            dict: result, result_code, result_message
        """

        result = []
        result_output = False
        print(user_id)
        try:

            cursor, conn = self.pool_init()

            cursor, conn = self.pool_init()
            self.cursor.execute('call get_booker_flag(%s)', user_id)
            result_code = config.CODE_0
            result = self.cursor.fetchall()
            result_message = 'Find palm feature complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        except Exception as E:
            result_code = config.CODE_1006
            result_message = 'Find palm feature error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))

        if not result:
            result_output = False
            golf_id = None
        else:
            result_output = True
            golf_id = result

        return {'result': result_output,
                'result_golfclub_id':golf_id,
                'result_code': result_code,
                'result_message': str(result_message)}

    def get_golfclub_id_from_device_id(self, device_id):
        """Select all palm feature data in table for embedding

        Return:
            dict: result, result_code, result_message
        """

        result = []
        try:
            cursor, conn = self.pool_init()

            cursor.execute('call get_golfclub_id_from_device_id(%s)', device_id)
            result_code = config.CODE_0
            result = cursor.fetchone()
            result_message = 'Find palm feature complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        except Exception as E:
            result_code = config.CODE_1006
            result_message = 'Find palm feature error'
            log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message), exc_info=1)

        if len(result) <= 0:
            result_code = config.CODE_1007
            result_message = 'find palm feature null data error'
            log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message), exc_info=1)

        return {'result':result,
                'result_code': result_code,
                'result_message': str(result_message)}

    def delete_reservation_table_data(self):
        """Delete all data in table

        Args:
            table       (str)   : table name for delete data

        Return:
            dict: result_code, result_message
        """

        try:
            # TODO : result code check
            cursor, conn = self.pool_init()
            cursor.execute('call delete_reservation_t()')
            result_code = 0
            result_message = 'Delete reservation table data complete'
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_RESERVATION_TABLE', full_message= result_message))
        except Exception as E:
            result_message = 'Delete reservation table data error'
            result_code = config.CODE_1005
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='DELETE_RESERVATION_TABLE', full_message=result_message))

    def get_palm_feature(self ):
        """Select all palm feature data in table for embedding

        Return:
            dict: result, result_code, result_message
        """

        result = []
        try:
            cursor, conn = self.pool_init()
            cursor.execute('call find_palm_feature()')
            result_code = config.CODE_0
            result = cursor.fetchall()
            result_message = 'Find palm feature complete'
            self.pool.release(conn)

            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        except Exception as E:
            result_code = config.CODE_1006
            result_message = 'Find palm feature error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        if len(result) <= 0:
            result_code = config.CODE_1007
            result_message = 'find palm feature null data error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))

        return result

    def get_gap_feature(self ):
        """Select all gap feature data in table for embedding

        Return:
            dict: result, result_code, result_message
        """

        result = []
        try:
            cursor, conn = self.pool_init()
            cursor.execute('call find_gap_feature()')
            result_code = config.CODE_0
            result = cursor.fetchall()
            result_message = 'Find gap feature complete'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))
        except Exception as E:
            result_code = config.CODE_1006
            result_message = 'Find gap feature complete'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))

        if len(result) <= 0:
            result_code = config.CODE_1007
            result_message = 'find gap feature null data error'
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='SELECT_FEATURE', full_message=result_message))

        self.pool.release(conn)
        return result


    def insert_reservation_table(self, golfclub_id, user_id, tee_time):
        """Insert reservation data in reservation table

        Args:
            golfclub_id (str)   : golfclub_id data
            user_id     (str)   : user_id data

        Return:
            dict: result_code, result_message
        """
        print('aaaaaaaaaaaaa')
        insert_tuple_data = (golfclub_id, user_id, tee_time)
        try:
            #cursor, conn = self.pool_init()

            conn = self.pool.get_conn()
            cursor = conn.cursor()
            conn.ping(reconnect=True)
            cursor.execute('use ' + config.DB_NAME)
            conn.commit()
            cursor.execute('call insert_reservation_info(%s, %s, %s)', insert_tuple_data)
            result_code = config.CODE_0
            conn.commit()
            print('sssssssssssss')
            self.pool.release(conn)
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='INSERT_RESERVATION', full_message='Insert reservation table complete'))
        except Exception as E:
            result_code = config.CODE_1003
            print(E)
            traceback.print_exc()
            self.log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='INSERT_RESERVATION', full_message='Insert reservation table error'))


