import redis 
import json
def send_messageq(): 
    r = redis.StrictRedis(host='10.12.200.127', port=6379, db=0) 
    p = r.pubsub() 
    print("Starting main scripts...")
    user_data = {"a":"{b:c}"}
    user_data = json.dumps(user_data)
    r.publish('user_data', user_data) 
    print("Done") 
if __name__ == '__main__': 
    send_messageq()

