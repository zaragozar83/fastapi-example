from time import sleep
from fastapi import FastAPI, Body, HTTPException, status, Header
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Final, Optional
from kafka import KafkaConsumer, KafkaProducer
import json
from multiprocessing import Process
import config as config
import concurrent.futures
from loguru import logger
import nest_asyncio

from models import MessageInput
from datetime import datetime

nest_asyncio.apply()
app = FastAPI()
# logger.info(f"db server url  {config.MONGODB}")
logger.info(f"kafka server  : {config.KAFKA_SERVER}")
sms_producers: Optional[KafkaProducer] = None

CACHE: Final = {}  # Cache to cache some data

DN_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(5)
MO_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(5)


# Config function

def get_producer() -> KafkaProducer:
    global sms_producers
    if sms_producers is None:
        sms_producers = KafkaProducer(bootstrap_servers=config.KAFKA_SERVER,
                                      value_serializer=lambda m: json.dumps(m).encode('utf8'))
    return sms_producers


def consume_mo(topic):
    '''
    Consuming MO ( Mobile Originate ) from Kafka
    '''
    logger.debug("Consuming mo")
    sleep(3)  # just to let docker ready to serve for kafka
    try:
        consumer = KafkaConsumer(topic, bootstrap_servers=config.KAFKA_SERVER)
        for message in consumer:
            data = message.value.decode('utf-8')
            logger.info(f"receiving MO trigger {message.topic} key={message.key} value= {data}")

    except Exception as e:
        logger.error(f"Error!! {e}")


@app.post("/send", response_description="Submit Sms")
async def submit_sms(sms_input:MessageInput= Body(...)):

    sms_input.request_date = datetime.now()
    message_data = [{'dest':dest, 'src':sms_input.src, 'lang':sms_input.lang, 'content': sms_input.content} for dest in sms_input.dest]
    sms_input = jsonable_encoder(sms_input)
    # await db["mt_submits"].insert_one(sms_input)
    print("Print values")
    print(f"message_data {message_data}")
    logger.info("message_data %s", message_data)
    logger.info("sms_input %s", sms_input)
    for _,msg in enumerate(message_data):
        print(f"msg: {msg}")
        get_producer().send( config.KAFKA_MT_TOPIC, msg)
        logger.info("Message sent")

    return {'success':True, 'message':'Success'}


@app.get("/producer")
async def submit_sms():

    message_data = 'Hello from fastapi'
    print(f"message_data: {message_data}")
    send = get_producer().send(config.KAFKA_MT_TOPIC, message_data)
    if send.is_done:
        print("It is done!")
    return {'success': True, 'message': 'Success'}


consumer_thread = Process(target=consume_mo, args=(config.KAFKA_MO_TOPIC,))


@app.on_event("startup")
async def startup():
    consumer_thread.start()
    logger.info("demo")


@app.on_event("shutdown")
def shutdown_event():
    DN_THREAD_POOL.shutdown()
    MO_THREAD_POOL.shutdown()
    consumer_thread.kill()
