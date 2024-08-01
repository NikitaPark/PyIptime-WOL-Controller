from fastapi import FastAPI, Header
import os
from typing import Union

from iptime import WOLController

app = FastAPI()

ROUTER_HOST = os.environ.get('ROUTER_HOST', '192.168.0.1')
ROUTER_PORT = os.environ.get('ROUTER_PORT', 80)
ROUTER_USERNAME = os.environ.get('ROUTER_USERNAME', 'admin')
ROUTER_PASSWORD = os.environ.get('ROUTER_PASSWORD', 'admin')

WAKE_KEY = os.environ.get('WAKE_KEY', 'wake')

ctl = WOLController(host=ROUTER_HOST, port=ROUTER_PORT)
ctl.login(username=ROUTER_USERNAME, password=ROUTER_PASSWORD)

@app.post("/wa3k-on-l4n")
def wake_pc(mac_addr: str, x_api_key: Union[str, None] = Header(default=None)):
    try:
        if x_api_key == WAKE_KEY:
            ctl.do_wake_pc(mac_addr=mac_addr)
        
            return {"status": "OK"}
        
        else:
            return {
                "status": "Failed",
                "caused_by": "Key dose not matched."
            }
    
    except Exception as e:
        return {
            "status": "Failed",
            "caused_by": str(e)
        }