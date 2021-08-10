from flask import Flask, jsonify, request, render_template
from flask_restful import Api
import logUtil
from SQLHandlerProc import SQLHandler
import numpy as np
import generalUtil
import io
import json
import config
import time, os
from featureLoader import FeatureLoader
import requests
import asyncio
from threading import Thread
from multiprocessing.pool import ThreadPool
import concurrent.futures
import traceback
app = Flask(__name__)
api = Api(app)
log_thread = logUtil.logThread()
log_thread.start()
sqlhandler = SQLHandler(log_thread)

feature_loader = FeatureLoader(sqlhandler,log_thread)

generalUtil.init(log_thread)
@app.route('/image_checker', methods=['POST'])
def image_checker():
    env_code_result = 0
    
    try:
        # print(request.files)
        palm_image = request.files['palm']
        gap_image_index_finger = request.files['gap0']
        gap_image_middle_finger = request.files['gap1']
        gap_image_ring_finger = request.files['gap2']
        gap_image_pinky_finger = request.files['gap3']

        palm_image = generalUtil.request_file_to_image(palm_image)
        result_message, env_code = generalUtil.illuminance_checker(palm_image, 'palm')
        if env_code != 0:
            env_code_result = env_code
        gap_image_index_finger = generalUtil.request_file_to_image(gap_image_index_finger)
        result_message, env_code = generalUtil.illuminance_checker(gap_image_index_finger, 'gap0')
        if env_code != 0:
            env_code_result = env_code
        gap_image_middle_finger = generalUtil.request_file_to_image(gap_image_middle_finger)
        result_message, env_code = generalUtil.illuminance_checker(gap_image_middle_finger, 'gap1')
        if env_code != 0:
            env_code_result = env_code
        gap_image_ring_finger = generalUtil.request_file_to_image(gap_image_ring_finger)
        result_message, env_code = generalUtil.illuminance_checker(gap_image_ring_finger, 'gap2')
        if env_code != 0:
            env_code_result = env_code
        gap_image_pinky_finger = generalUtil.request_file_to_image(gap_image_pinky_finger)
        result_message, env_code = generalUtil.illuminance_checker(gap_image_pinky_finger, 'gap3')
        if env_code != 0:
            env_code_result = env_code
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='IMAGE_CHECKER', full_message='feature request complete'))
        
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'feature request error',
                        'env_code':-1}
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='IMAGE_CHECKER', full_message='feature request error'))
        
        return jsonify(return_data)

    return {'result_code': config.CODE_0,
            'result_message':result_message,
            'env_code': env_code_result}

@app.route('/register', methods=['POST'])
def regist():
    """Regist user feature data on database and return complete or not

    Request:
        user_id         (str)   : request user_id from smartphone or tablet
        palm_feature    (json)  : request palm_feature from smartphone or tablet
        gap_features    (json)  : request gap_features from smartphone or tablet (index, middle, ring, pinky)
        model_version   (str)   : request model_version from smartphone or tablet

    Returns:
        json(dict): result_code, result_message
    """
    global sqlhandler
    
    # TODO if we need device infomation
    # device_info = generalUtil.request_device_info()
    
    return_data = {}
    start = time.time()
    user_info = generalUtil.request_user_info()
    
    try:
        palm_features = user_info.get_palm_feature()
        index_features = user_info.get_gap_feature_index_finger()
        middle_features = user_info.get_gap_feature_middle_finger()
        ring_features = user_info.get_gap_feature_ring_finger()
        pinky_features = user_info.get_gap_feature_pinky_finger()
        
        
        log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='featrure data json load complete', user_info=user_info))
        
    except Exception as e:
        return_data = {'result_code':config.CODE_1001,
                        'result_message':'feature json load error'}
        log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='featrure data json load error', user_info=user_info))
        return jsonify(return_data)
    
    return_data = sqlhandler.delete_palm_feature_by_uid(user_info.get_user_id())
    if not return_data['result_code'] == config.CODE_0:
        return jsonify(return_data)

    return_data = sqlhandler.delete_gap_feature_by_uid(user_info.get_user_id())
    if not return_data['result_code'] == config.CODE_0:
        return jsonify(return_data)
    
    for idx, (palm_feature, index_feature, middle_feature, ring_feature, pinky_feature) in enumerate(zip(palm_features, index_features, middle_features, ring_features, pinky_features)):
        try:
            feature_loader.append_feature(user_info.get_user_id(), palm_feature, index_feature, middle_feature, ring_feature, pinky_feature, idx)             
            palm_feature = np.array(palm_feature, dtype=np.float32) # list to numpy array
            palm_feature = palm_feature.tobytes() # numpy array to bytes
            
            index_feature = np.array(index_feature, dtype=np.float32) 
            index_feature = index_feature.tobytes() 

            middle_feature = np.array(middle_feature, dtype=np.float32) 
            middle_feature = middle_feature.tobytes() 

            ring_feature = np.array(ring_feature, dtype=np.float32) 
            ring_feature = ring_feature.tobytes()

            pinky_feature = np.array(pinky_feature, dtype=np.float32) 
            pinky_feature = pinky_feature.tobytes() 
            
            log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='featrure data json load complete', user_info=user_info))
        except Exception as e:
            return_data = {'result_code':config.CODE_1002,
                        'result_message':'palm feature slicing error - numpy'}
            log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='featrure data json load error', user_info=user_info))
            return jsonify(return_data)
        
        return_data = sqlhandler.insert_regist_feature(user_info.get_user_id(), str(idx), 
        palm_feature, index_feature, middle_feature, ring_feature, pinky_feature, user_info.get_model_version())
        if not return_data['result_code'] == config.CODE_0:
            return jsonify(return_data)
    
    log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='featrure slicing complete', user_info=user_info))
    if return_data['result_code'] == config.CODE_0:
        log_thread.queue_put(logUtil.get_graylog_dict(short_message='REGIST', full_message='regist complete', user_info=user_info))
    print("regist time :", time.time() - start)
    return jsonify(return_data)

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """User autheniticate process

    Request:
        palm_feature (json): unknown user's palm feature
        gap _feature (json): unknown user's gap features (index, middle, ring, pinky)

    Return:
        json(dict): user_id, distance, predict_user, result_code, result_message
            
    """
    global sqlhandler
    
    return_data = {}
    gap_features = []
    try:

        palm_image = request.files['palm']
        gap_image_index_finger = request.files['gap0']
        gap_image_middle_finger = request.files['gap1']
        gap_image_ring_finger = request.files['gap2']
        gap_image_pinky_finger = request.files['gap3']
        palm_image = generalUtil.request_file_to_image(palm_image)
        gap_image_index_finger = generalUtil.request_file_to_image(gap_image_index_finger)
        gap_image_middle_finger = generalUtil.request_file_to_image(gap_image_middle_finger)
        gap_image_ring_finger = generalUtil.request_file_to_image(gap_image_ring_finger)
        gap_image_pinky_finger = generalUtil.request_file_to_image(gap_image_pinky_finger)
        
        gap_image_index_finger = generalUtil.gap_crop(gap_image_index_finger)
        gap_image_middle_finger = generalUtil.gap_crop(gap_image_middle_finger)
        gap_image_ring_finger = generalUtil.gap_crop(gap_image_ring_finger)
        gap_image_pinky_finger = generalUtil.gap_crop(gap_image_pinky_finger)
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='palm_feature request complete'))
    except Exception as e:
        return_data = {'user_id':'0',
                        'distance':'1000',
                        'predict_user':'0',
                        'result_code':config.CODE_1000,
                        'result_message':'palm feature request error'}
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='palm feature request error'))
        return jsonify(return_data)
    try:
        palm_feature =  generalUtil.palm_predict(palm_image)
        index_feature =  generalUtil.gap_predict(gap_image_index_finger)
        middle_feature =  generalUtil.gap_predict(gap_image_middle_finger)
        ring_feature =  generalUtil.gap_predict(gap_image_ring_finger)
        pinky_feature =  generalUtil.gap_predict(gap_image_pinky_finger)
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='featrure data json load complete'))
        
        
    except Exception as e:
        traceback.print_exc()
        return_data = {'user_id':'0',
                        'distance':'1000',
                        'predict_user':'0',
                        'result_code':config.CODE_1001,
                        'result_message':'feature json load error'}
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='featrure data json load error'))
        return jsonify(return_data)
    try:
        palm_feature = np.array(palm_feature, dtype=np.float32) # list to numpy array

        index_feature = np.array(index_feature, dtype=np.float32) 
        gap_features.append(index_feature)

        middle_feature = np.array(middle_feature, dtype=np.float32) 
        gap_features.append(middle_feature)

        ring_feature = np.array(ring_feature, dtype=np.float32) 
        gap_features.append(ring_feature)

        pinky_feature = np.array(pinky_feature, dtype=np.float32) 
        gap_features.append(pinky_feature)
        
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='palm_featrure json load complete'))
        
    except Exception as e:
        return_data = {'user_id':'0',
                        'distance':'1000',
                        'predict_user':'0',
                        'result_code':config.CODE_1002,
                    'result_message':'palm feature slicing error - numpy'}
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', full_message='palm_featrure json load error'))
        return jsonify(return_data)
    user_data = feature_loader.get_user_feature()
    #step 1 use palm feature
    palm_data = generalUtil.calc_palm_distance(user_data, palm_feature)
    #step 2 use gap feature
    gap_data = generalUtil.calc_gap_distance(user_data, gap_features)
    #step 3 calc acc
    result_data = generalUtil.authenticate_result_maker(palm_data, gap_data)
    start_attend = time.time()
    if result_data['result_code'] == config.CODE_0:
        attend_server_url = 'https://attend.kakaovx.com/api'
        attend_request_data = {'mode':'attend',
                        'deviceNo':31,
                        'userId':result_data['user_id']}
        attend_response = requests.post(attend_server_url, attend_request_data).json()
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE_ATTEND',
        full_message='attend request complete code: ' + str(attend_response['code']) + 
        ' message: ' + str(attend_response['message']) + ' value: '+ str(attend_response['value'])))
        
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='AUTHENTICATE', 
        full_message='authenticate complete user: '+ result_data['user_id'] + ' accuracy: '
        + result_data['accuracy']+' nearest predict_user: '+result_data['predict_user']))
    
    return jsonify(result_data)

# ************Admin methods****************8

@app.route('/',methods=['POST', 'GET'])
def index_page():
    return render_template('index.html')

@app.route('/admin/delete_table_data', methods=['POST'])
def delete_table_data():
    """Delete all data in table
    
    Request:
        table (str): request table from smartphone or tablet

    Return:
        json(dict): result_code, result_message
    """
    global g_logger
    global sqlhandler

    logger = logUtil.set_context(g_logger, 'DELETE_TABLE')
    return_data = {}
    try:
        table = request.form['delete_table']
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='DELETE_TABLE', full_message='delete_table request complete'), exc_info=1)
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'delete_table request error'}    
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='DELETE_TABLE', full_message='delete_table request error'), exc_info=1)
        return jsonify(return_data)

    return_data = sqlhandler.delete_table_data(table)
    
    return jsonify(return_data)

@app.route('/admin/find_user_data', methods=['POST'])
def find_user_data():
    """Find user's all data (feature_fegist_date, time, is_booked etc...)

    Request:
        user_id (str): request user_id from smartphone or tablet

    Return:
        json(dict): result, result_code, result_message
    """
    global g_logger
    global sqlhandler

    logger = logUtil.set_context(g_logger, 'FIND_USER')
    return_data = {}
    try:
        user_id = request.form['user_id']
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_USER', full_message='user_id request complete'), exc_info=1)
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'find_user_data(): user_id request error\n'+ str(e)}
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_USER', full_message='user_id request error'), exc_info=1)
        return jsonify(return_data)

    table = config.USER_TABLE
    return_data = sqlhandler.find_data_by_condition_id('*', table, 'user_id', user_id)
    
    return jsonify(return_data)

@app.route('/admin/find_device_data', methods=['POST'])
def find_device_data():
    """Find device data (device_id, golfclub_id)

    Request:
        device_id (str): request device_id from tablet

    Return:
        json(dict): result, result_code, result_message
    """
    global g_logger
    global sqlhandler

    logger = g_logger
    
    return_data = {}
    try:
        device_id = request.form['device_id']
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_DEVICE', full_message='device_id request complete'), exc_info=1)
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'find_device_data(): device_id request error'}    
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_DEVICE', full_message='device_id request error'), exc_info=1)
        return jsonify(return_data)

    table = config.DEVICE_TABLE
    return_data = sqlhandler.find_data_by_condition_id('golfclub_id', table, 'device_id', device_id)
    
    return jsonify(return_data)

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    """Delete user in user table 

    Request:
        user_id (str): request user_id from smartphone or tablet
    
    Return:
        json (dict): result_code, result_message
    """
    global g_logger
    global sqlhandler
    
    logger = g_logger

    return_data = {}
    try:
        user_id = request.form['user_id']
        feature_loader.delete_feature(user_id)
        asyncio.run(logUtil.send_log(logger, logUtil.get_graylog_dict_no_user(short_message='DELETE_USER', full_message='user_id request complete')))
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'delete_user(): user_id request error'}
        asyncio.run(logUtil.send_log(logger, logUtil.get_graylog_dict_no_user(short_message='DELETE_USER', full_message='user_id request error')))
        return jsonify(return_data)

    return_data = sqlhandler.delete_feature_by_uid(config.USER_TABLE, user_id)
    
    return jsonify(return_data)

@app.route('/admin/find_golfclub_data', methods=['POST'])
def find_golf_club_data():
    """Find golfclub data (golfclub_id, golfclub_name, #TODO etc...)

    Request:
        golfclub_id (str): request golfclub_id from admin

    Return:
        json(dict): result, result_code, result_message
    """
    global g_logger
    global sqlhandler
    
    logger = g_logger
    return_data = {}
    try:
        golfclub_id = request.form['golfclub_id']
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_GOLFCLUB', full_message='golfclub_id request complete'), exc_info=1)
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'find_golf_club_data(): golfclub id request error'}
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='FIND_GOLFCLUB', full_message='golfclub_id request error'), exc_info=1)
        return jsonify(return_data)

    table = config.GOLF_CLUB_TABLE
    return_data = sqlhandler.find_data_by_condition_id('golfclub_name', table, 'golfclub_id', golfclub_id)
    
    return jsonify(return_data)

@app.route('/admin/is_regist', methods=['POST'])
def is_regist():
    global sqlhandler

    return_data = {}

    try:
        user_id = request.form['user_id']
        isregist = sqlhandler.is_regist(user_id)
        result_code = 0
        result_message = 'is_regist complete'
    except Exception as e:
        print(e)
        traceback.print_exc()
        result_code = 1000
        result_message = 'is_regist error'
        asyncio.run(logUtil.send_log(logger, logUtil.get_graylog_dict_no_user(short_message='ISREGIST',full_message=result_message)))
        return jsonify(return_data)
    return {'result':isregist,
    'result_code':result_code,
    'result_message':result_message}

@app.route('/admin/delete_feature', methods=['POST'])
def delete_feature():
    global g_logger
    global sqlhandler
    logger = g_logger

    return_data = {}
    try:
        user_id = request.form['user_id']
        sqlhandler.delete_palm_feature_by_uid(user_id)
        sqlhandler.delete_gap_feature_by_uid(user_id)
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='DELETE_USER', full_message='delete_feature(): user_id request error'))
        result_code = 0
        result_message = 'delete_feature complete'
    except Exception as e:
        return_data = {'result': 'None', 'result_code':config.CODE_1000,
        'result_message':'delete_feature(): user_id request error'}
        result_code = 1000
        result_message = 'delete_feature error'
        logger.debug(logUtil.get_graylog_dict_no_user(short_message='ISREGIST',full_message='user_id request error'), exc_info=1)
        return jsonify(return_data)
    return {'result_code':result_code,
    'result_message':result_message}

if __name__ == '__main__':
    app.run(debug=True, host='10.12.200.137', port=5000)
