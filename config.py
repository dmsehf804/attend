import socket
import platform


#facility
FACILITY_NAME = 'palm_recognition_attend'

#version
VERSION = '1.0'

#host info
HOST_NAME = str(socket.gethostname())

HOST_IP_EXTERNAL = '10.12.200.127'

#host software info
HOST_OS = 'OS: ' + platform.system()+ ' VERSION: ' + platform.version()

#log level
LOG_DEBUG = 'debug'
LOG_INFO = 'info'
LOG_WARN = 'warn'
LOG_ERROR = 'error'
LOG_CRITICAL = "critical"

#service type
DEV = 'dev'
STAGE = 'stage'
REAL = 'real'

#DB
DB_NAME     = 'palmDB'


#connection(local dev)
HOST        = '10.12.200.127'
DB_USER     = 'palm'
PW          = '0000'

#TABLES
RESERVATION_TABLE       = 'reservation_t'
USER_TABLE              = 'user_t'
DEVICE_TABLE            = 'device_t'
GOLF_CLUB_TABLE         = 'golf_club_t'
PALM_FEATURE_TABLE      = 'palm_feature_t'
PALM_MODEL_PARAM_TABLE  = 'palm_model_param_t'
GAP_FEATURE_TABLE       = 'gap_feature_t'
GAP_MODEL_PARAM_TABLE   = 'gap_model_param_t'

#distance threshold
PALM_THRESHOLD  = 17000
GAP_THRESHOLD   = 8000

#result info
N_TOP = 5

#result code
CODE_0 = 0  #'good'

#error code
CODE_1000 = 1000    #'data request error'
CODE_1001 = 1001    #'json load error'
CODE_1002 = 1002    #'numpy error'
CODE_1003 = 1003    #'sql insert error'
CODE_1004 = 1004    #'sql update error'
CODE_1005 = 1005    #'sql drop error'
CODE_1006 = 1006    #'sql select error'
CODE_1007 = 1007    #'sql select error - NULL data'
CODE_1008 = 1008    # gap extract error
CODE_1010 = 1010    #'data slicing error'
CODE_1011 = 1011    #'list index error'

#log config
GRAYLOG_HTTP_ADDR = 'graylog-ai.kakaovx.net'
GRAYLOG_PORT = 12201

#image checker

illuminance_all_pixel_threshold_lower=75
illuminance_all_pixel_threshold_upper=230
bot_top_sub_threshold = 50
left_rigt_sub_threshold = 50
