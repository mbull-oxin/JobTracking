import zmq
import asyncio

from zmq.asyncio import Context

context = Context.instance()

zmq_config = {
    "state_in": {
        "type": zmq.SUB,
        "address": "tcp://127.0.0.1:6000",
        "bind": False,
    },
    "state_out": {
        "type": zmq.PUSH,
        "address": "tcp://127.0.0.1:6001",
        "bind": False,
    },
}

class Monitor:
    def __init__(self,brk_addr):
        self.brk_conn=context.socket(zmq.SUB)
        self.brk_conn.connect('tcp://broker.jobtracking.local:6000')
        self.brk_conn.setsockopt(zmq.SUBSCRIBE,'')