import os
import redis
import json

from multiprocessing import Process


redis_conn = redis.StrictRedis(host='10.12.200.127', port=6379, db=0,charset="utf-8", decode_responses=True)
def sub(name: str):
    pubsub = redis_conn.pubsub()
    pubsub.subscribe('startScripts')
    for message in pubsub.listen():
        print(message)
        if message.get("type") == "message":
            #data = json.loads(message.get("data"))
            m = pubsub.get_message()
            print(type(message))
            data = message.get("data")
            print("%s : %s" % (name, data))
            

if __name__ == "__main__":
    Process(target=sub, args=("reader1",)).start()
