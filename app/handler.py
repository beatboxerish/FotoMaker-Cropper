import runpod
import subprocess
import requests
import time
from app import init, inference


def check_api_availability(host):
    while True:
        try:
            response = requests.get(host)
            return
        except requests.exceptions.RequestException as e:
            print(f"API is not available, retrying in 200ms... ({e})")
        except Exception as e:
            print('something went wrong')
        time.sleep(200/1000)


def handler(event):
    '''
    This is the handler function that will be called by the serverless.
    '''
    global model
    response = inference(event)
    return response


init()
runpod.serverless.start({"handler": handler})
