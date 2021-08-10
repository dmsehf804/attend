import time
import config
import numpy as np
import os
import logUtil
from flask import request, jsonify
from deviceInfo import DeviceInfo
from userInfo import UserInfo
import json
import numpy as np
import cv2
import tensorflow as tf
import io
import multiprocessing
from threading import Thread
from gapAlignment import GapAlignment, cropping_and_saving_images

input_size =224

interpreter_palm = tf.lite.Interpreter(model_path=str('palm_id.tflite'))
interpreter_palm.allocate_tensors()

input_details = interpreter_palm.get_input_details()[0]
output_details = interpreter_palm.get_output_details()[0]

gap_input_size = 128

interpreter_gap = tf.lite.Interpreter(model_path=str('gap_id.tflite'))

input_details_gap = interpreter_gap.get_input_details()[0]
output_details_gap = interpreter_gap.get_output_details()[0]
interpreter_gap.allocate_tensors()
gap_alignment = GapAlignment()
def init(thread):
    global log_thread
    log_thread = thread


def illuminance_checker(image, part):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    height, width = gray.shape
    pixel_right = 0
    pixel_left = 0
    pixel_bottom = 0
    pixel_top = 0
    pixel_sum = 0
    for h in range(0, height):
        for w in range(0, width):
            if w < (width / 2):
                pixel_right += gray[h, w]
            if w >= (width / 2):
                pixel_left += gray[h, w]
            if h < (height / 2):
                pixel_bottom += gray[h, w]
            if h >= (height / 2):
                pixel_top += gray[h, w]
            pixel_sum += gray[h, w]
    illuminance_all_pixel = int(pixel_sum / (height* width))
    if illuminance_all_pixel <= config.illuminance_all_pixel_threshold_lower:
        return part + " (이)가 너무 어둡습니다.", 1
    if illuminance_all_pixel >= config.illuminance_all_pixel_threshold_upper:
        return part + " (이)가 너무 밝습니다.", 2
    if abs((pixel_bottom / (height * width)) - (pixel_top / (height * width))) > config.bot_top_sub_threshold:
        return part + " 그림자 감지.", 3
    if abs((pixel_left / (height * width)) - (pixel_right / (height * width))) > config.left_rigt_sub_threshold:
        return part + " 그림자 감지.", 3
    
    return "정상 촬영 전체조도: " + str(illuminance_all_pixel), 0
    

def request_file_to_image(image):
    img_read = image.read()
    nparr = np.fromstring(img_read, np.uint8)
    
    #IMREAD_UNCHANGED #IMREAD_COLOR
    original_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
    original_img = original_img[:,:,:3]
    #original_img = cv2.cvtColor(original_img, cv2.COLOR_RGB2BGR)
    cv2.imwrite('1.png', original_img)
    return original_img

#flask 이미지 모델입력에 적합한 형식으로 바꾸기
def request_file_to_images(images):
    original_imgs = []
    for idx, image in enumerate(images):
        img_read = image.read()
        nparr = np.fromstring(img_read, np.uint8)
                    
        #IMREAD_UNCHANGED #IMREAD_COLOR
        original_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        original_img = original_img[:,:,:3]
        #original_img = cv2.cvtColor(original_img, cv2.COLOR_RGB2BGR)
        original_imgs.append(original_img)
    return original_imgs

def palm_predict(palm_image):
    
    image = (palm_image / 127.5) - 1.
        
    image = np.expand_dims(image, axis=0).astype(input_details_gap["dtype"])
            
    interpreter_palm.set_tensor(input_details_gap["index"], image)
    interpreter_palm.invoke()
    palm_feature = interpreter_palm.get_tensor(output_details_gap["index"])[0]
    

    return palm_feature

def gap_predict(gap_image):
    image = (gap_image / 127.5) - 1.
        
    image = np.expand_dims(image, axis=0).astype(input_details_gap["dtype"])
            
    interpreter_gap.set_tensor(input_details_gap["index"], image)
    interpreter_gap.invoke()
    gap_feature = interpreter_gap.get_tensor(output_details_gap["index"])[0]
    
    return gap_feature

def palm_predicts(palm_imgs):
    palm_features = []
    for palm_image in palm_imgs:
        image = (palm_image / 127.5) - 1.
            
        image = np.expand_dims(image, axis=0).astype(input_details_gap["dtype"])
                
        interpreter_palm.set_tensor(input_details_gap["index"], image)
        interpreter_palm.invoke()
        palm_feature = interpreter_palm.get_tensor(output_details_gap["index"])[0]
        palm_features.append(palm_feature)
    
    return palm_features

def gap_predicts(gap_images):
    gap_features = []
    for gap_image in gap_images:
        print(gap_image.shape)
        image = (gap_image / 127.5) - 1.
            
        image = np.expand_dims(image, axis=0).astype(input_details_gap["dtype"])
                
        interpreter_gap.set_tensor(input_details_gap["index"], image)
        interpreter_gap.invoke()
        gap_feature = interpreter_gap.get_tensor(output_details_gap["index"])[0]
        gap_features.append(gap_feature)
    
    return gap_features

def request_user_info():
    """Request user information from device

    Return:
        user_info(class): include user data
    """
    palm_images = []
    gap_image_index_fingers = []
    gap_image_middle_fingers = []
    gap_image_ring_fingers = []
    gap_image_pinky_fingers = []

    output_path = 'out'
    outputs = []
    try:
        user_id = request.form.get('user_id')
        user_name = request.form.get('user_name')
        for idx in range(5):
            palm_images.append(request.files.get('palm'+str(idx)))
            
            gap_image_index_fingers.append(request.files.get('gap0_'+str(idx)))
            
            gap_image_middle_fingers.append(request.files.get('gap1_'+str(idx)))
            
            gap_image_ring_fingers.append(request.files.get('gap2_'+str(idx)))
            
            gap_image_pinky_fingers.append(request.files.get('gap3_'+str(idx)))
            

        model_version = request.form.get('model_version')
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='REQUEST_USER_INFO', full_message='user info request complete'))
    except Exception as e:
        return_data = {'result_code':config.CODE_1000,
                        'result_message':'REQUEST_USER_INFO request error'}    
        log_thread.queue.put(logUtil.get_graylog_dict_no_user(short_message='REQUEST_USER_INFO', full_message='user info request error'))
        return jsonify(return_data)
    
    palm_images = request_file_to_images(palm_images)
    gap_image_index_fingers = request_file_to_images(gap_image_index_fingers)

    gap_image_middle_fingers = request_file_to_images(gap_image_middle_fingers)
    gap_image_ring_fingers = request_file_to_images(gap_image_ring_fingers)
    gap_image_pinky_fingers = request_file_to_images(gap_image_pinky_fingers)
    
    gap_image_index_fingers = gap_crops(gap_image_index_fingers)
    gap_image_middle_fingers = gap_crops(gap_image_middle_fingers)
    gap_image_ring_fingers = gap_crops(gap_image_ring_fingers)
    gap_image_pinky_fingers = gap_crops(gap_image_pinky_fingers)
    
    palm_feature = palm_predicts(palm_images)
    gap_feature_index_finger = gap_predicts(gap_image_index_fingers)
    gap_feature_middle_finger = gap_predicts(gap_image_middle_fingers)
    gap_feature_ring_finger = gap_predicts(gap_image_ring_fingers)
    gap_feature_pinky_finger = gap_predicts(gap_image_pinky_fingers)
    user_info = UserInfo(
        user_id,
        user_name,
        palm_feature,
        gap_feature_index_finger,
        gap_feature_middle_finger,
        gap_feature_ring_finger,
        gap_feature_pinky_finger,
        model_version
    )

    return user_info

def calc_palm_distance(user_data, input_feature, threshold=config.PALM_THRESHOLD):
    """Calculate distance between user's feature in database and request unknown feature

    Args:
        user_feature_list (list) : user's feature list data
        user_id_list (list) : user's id list data
        input_feature (numpy array) : input unknown user's feature
        data (dict) : result - select table data(features), result_code, result_message
        threshold (int) : distance threshold default: 65

    Return:
        data        (dict)  : 
            - result        (str)   : select table result (redundancy)
            - user_id       (str)   : nearest user_id 
            - distance      (str)   : distance
            - predict_user  (str)   : if predict unknow then nearest user_id
    """
    
    data = []
    try:
        data = nearest_class(user_data, input_feature, config.N_TOP,'palm')
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST', full_message='user feature list slicing complete'))
    except Exception as e:
        return_data = {'user_id':'0',
                        'distance':'1000',
                        'predict_user':'0','result_code':config.CODE_1010,
                        'result_message':'user feature list slicing error'}
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST', full_message='user feature list slicing error'))
        return data, return_data
    log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST_PALM', full_message=str(data)))
    return data

def nearest_class(user_data, input_feature, n_tops, featrue_flag, gap_index=-1):

    n_top_datas = []

    for idx, key in enumerate(user_data):
        if featrue_flag in key:

            if featrue_flag=='gap':
                distance = np.linalg.norm(input_feature - user_data[key][gap_index])
            else:
                distance = np.linalg.norm(input_feature - user_data[key])

            if config.GAP_THRESHOLD < distance and featrue_flag == 'gap':
                n_top_datas.append( { 'user_id': '0', 'distance': distance })
            elif config.PALM_THRESHOLD < distance and featrue_flag == 'palm':

                n_top_datas.append( { 'user_id': '0', 'distance': distance })
            else:
                n_top_datas.append( { 'user_id': key.split('_')[0], 'distance': distance })

    n_top_datas = sorted(n_top_datas, key=(lambda x: x['distance']))[:5]
    log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='NEAREST_CLASS', full_message=featrue_flag+' nearest class complete '))
    return n_top_datas

def calc_gap_distance(user_data, input_feature, threshold=config.GAP_THRESHOLD):
    """Calculate distance between user's feature in database and request unknown feature

    Args:
        user_feature_list (list) : user's feature list data
        user_id_list (list) : user's id list data
        input_feature (numpy array) : input unknown user's feature
        data (dict) : result - select table data(features), result_code, result_message
        threshold (int) : distance threshold default: #TODO

    Return:
        data        (dict)  : 
            - result        (str)   : select table result (redundancy)
            - user_id       (str)   : nearest user_id 
            - distance      (str)   : distance
            - predict_user  (str)   : if predict unknow then nearest user_id
    """
    
    data = []
    try:
        for idx in range(4):
            data.append(nearest_class(user_data, input_feature[idx], config.N_TOP,'gap', idx))
        log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST', full_message='user feature list slicing complete'))
    except Exception as e:
        return_data = {'user_id':'0',
                        'distance':'1000',
                        'predict_user':'0','result_code':config.CODE_1010,
                        'result_message':'user feature list slicing error'}
        Thread(target=logUtil.send_graylog, args=(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST', full_message='user feature list slicing error'),)).start()
        return data, return_data
    log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='CALC_DIST_GAP', full_message=str(data)))
    return data

def authenticate_result_maker(palm_data, gap_data):
    """Making result data #TODO
    """

    user_list = []
    distance_list = []
    unknown_cnt = 0
    same_user_cnt = 0
    zero_user_cnt = 0
    result_dict = {}
    palm_score = [7, 6, 4, 2, 1]
    gap_score = [7, 5, 3, 2, 1]
    pinky_score = [6, 4, 3, 2, 1]
    tmp_user = ''
    predict_user = '0'
    for idx, n_top_dict in enumerate(palm_data):
        if idx == 0 and n_top_dict['user_id'] == '0':
            unknown_cnt += 1
        if n_top_dict['user_id'] =='0':
            zero_user_cnt +=1
        if idx == 0 and n_top_dict['user_id'] != '0':
            tmp_user = n_top_dict['user_id']
        if n_top_dict['user_id'] == tmp_user:
            same_user_cnt += 1
        if n_top_dict['user_id'] in result_dict.keys():
            result_dict[n_top_dict['user_id']] = result_dict[n_top_dict['user_id']] + palm_score[idx]
        else:
            result_dict[n_top_dict['user_id']] = palm_score[idx]

        user_list.append(n_top_dict['user_id'])
        distance_list.append(n_top_dict['distance'])
    for idx in range(4):
        for index, n_top_dict in enumerate(gap_data[idx]):
            if index == 0 and n_top_dict['user_id'] == '0':
                unknown_cnt += 1

            if n_top_dict['user_id'] in result_dict.keys():
                if index ==4:
                    result_dict[n_top_dict['user_id']] = result_dict[n_top_dict['user_id']] + pinky_score[idx]
                else:
                    result_dict[n_top_dict['user_id']] = result_dict[n_top_dict['user_id']] + gap_score[idx]
            else:
                if index == 4:
                    result_dict[n_top_dict['user_id']] = pinky_score[index]
                else:
                    result_dict[n_top_dict['user_id']] = gap_score[index]

            user_list.append(n_top_dict['user_id'])
            distance_list.append(n_top_dict['distance'])
    user_dict = {}
    result_user = ''
    accuracy = 0.
    for (user, distance) in zip(user_list, distance_list):
        distance = float(distance)
        try:
            user_dict[user] += 1
        except:
            user_dict[user] = 1
        
    log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='RESULT_MAKER', full_message='user count complete : '+ str(user_dict)))
    if result_dict:
        max_score = 0
        for (user, score) in zip(result_dict.keys(), result_dict.values()):
            if max_score < score :
                max_score = score
                predict_user = user
                accuracy = score
        if unknown_cnt >= 3 or user_dict[predict_user] < 6:
            result_user = '0'
        else:
            result_user = predict_user
        if same_user_cnt >=4:
            result_user = tmp_user
        elif zero_user_cnt ==5:
            result_user = '0'
    
    log_thread.queue_put(logUtil.get_graylog_dict_no_user(short_message='RESULT_MAKER', full_message='select result user complete : '+ str(result_user)))
    log_thread.queue_put(logUtil.get_graylog_dict_no_user_acc(short_message='RESULT_MAKER', full_message='accuracy calc complete : '+ str(accuracy),acc=str(accuracy)))
    return {'user_id': str(result_user),
            'accuracy': str(accuracy),
            'result_code': config.CODE_0,
            'result_message': 'good',
            'predict_user': str(predict_user)}

def gap_crop(original_image):
    """Returns alignmented and cropped gap image.

    Args:
        original_image (numpy ndarray) : A long image in vertical orientation from clients with (H, W, 3) shapes.

    Returns:
        A numpy ndarray with (W, W, 3) shapes.
        
    """
    crop_image = gap_alignment.cropping(original_image)
    return crop_image

def gap_crops(original_images):
    crop_images = []
    for img in original_images:
        crop_image = gap_alignment.cropping(img)
        if type(crop_image) == np.ndarray:
            crop_images.append(crop_image)
        else:
            jsonify({'result_code':config.CODE_1008,'result_message':'gap crops false return'})
    return crop_images
