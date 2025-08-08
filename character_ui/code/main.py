import paho.mqtt.client as mqtt
import _thread as thread
from RGB1602 import RGB1602
import toml,logging,datetime,_thread,time,json

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('Character_UI')

class MqttClient:
    def __init__(self,conf,dsp=None):
        self.dsp=dsp
        self.conf=conf
        if not 'addr' in self.conf:
            self.conf['addr']='localhost'
            self.conf['port']=1883
        self._cli=mqtt.Client()
        self._cli.on_connect=self.onConnect
        self._cli.on_message=self.onMessage
    def run(self):
        self._cli.connect_async(self.conf['addr'],port=self.conf['port'])
        self._cli.loop_forever(retry_first_connection=True)
        #self._cli.disconnect()
        if self.dsp:
            self.dsp.stop()
    def onConnect(self,*args):
        logger.info(str(args))
        self._cli.subscribe('job_db/state/update/+')
        if self.dsp:
            # this may look a little weird but we want to show the firstline after we show the secondline for 4 seeconds
            # and as the cache is emptry at this point the firstline goes first and placed in the cache before the timeout line....
            self.dsp.show('Idle\nScan to start')
            self.dsp.show('Connected to -\n{:^16}'.format(self.conf['addr']),timeout=10)
    def onMessage(self,client,userdata,msg):
        topic=msg.topic
        msg=json.loads(msg.payload)
        logger.info(f'message from MQTT {topic}->{str(msg)}')
        if msg['location']!=self.conf['location']:
            logger.info('ignoring message for location %s' % msg['location'])
            return 
        ts=datetime.datetime.fromisoformat(msg['timestamp'])
        if topic.endswith('entered'):
            logger.info('job %s entered location' % msg['id'])
            job_id=msg['id']
            if self.dsp:
                self.dsp.show(f'Job: {job_id}\nstarted {ts.hour:02d}:{ts.minute:02d}')
        elif topic.endswith('exited'):
            logger.info('job exited')
            if self.dsp:
                self.dsp.show(f'Idle from: {ts.hour:02d}:{ts.minute:02d}\nScan to start')
        elif topic.endswith('error'):
            if msg['message']=='scan out first':
                logger.error('ERROR - location already occupied')
                if self.dsp:
                    self.dsp.show('ERROR - Scan\nout first',timeout=5)

class Display:
    '''Base class for displays'''
    lines=2
    def __init__(self,disp_config):
        # override to open display based on config
        self.conf=disp_config
        self._cache=[]
        self.mutex=thread.allocate_lock()
        self.timeout=-1
        self._run=True
    def show(self,msg,timeout=-1):
        # msg should be list or tuple of strings
        # if timeout set set display the recreate from cache after timeout...
        if type(msg)==str:
            msg=msg.split('\n')
        if len(msg)>self.lines:
            # too many lines for this display, trim and warn...
            msg=msg[:self.lines]
            logger.info('truncating message with too many lines to %s lines to fit in display' % self.lines)
        if timeout==-1:
            self._cache=msg
        logger.info(f'display {msg} with timeout {timeout}')
        with self.mutex:
            self.timeout=timeout
            self._show(msg)
    def start(self):
        thread.start_new_thread(self.loop,(),{})
    def stop(self):
        self._run=False
    def loop(self):
        self.timeout=0
        while self._run:
            #logger.info(f'tick -> {self.timeout}')
            with self.mutex:
                if self.timeout>0:
                    self.timeout=self.timeout-1
                elif self.timeout==0:
                    logger.info(f'resetting to {self._cache}')
                    self.timeout=self.timeout-1
                    self._show(self._cache)
            time.sleep(1)
        logger.info('display loop exited')
        self.clear()
    def _show(self,lines):
        # override to display lines on display...
        pass
    def clear(self):
        # override to clear display
        pass

class WS1602RGB(Display):
    def __init__(self,disp_config):
        super(WS1602RGB,self).__init__(disp_config)
        self.dsp=RGB1602(16,2)
    def _show(self,msg):
        if not msg:
            print('WTF??',msg)
            return
        if msg[0].startswith('Job'):
            self.dsp.setRGB(0,255,0)
        elif msg[0].startswith('ERROR'):
            self.dsp.setRGB(255,0,0)
        else:
            self.dsp.setRGB(255,255,255)
        self.dsp.clear()
        if len(msg)>=1:
            self.dsp.setCursor(0,0)
            self.dsp.printout(msg[0])
        if len(msg)>=2:
            self.dsp.setCursor(0,1)
            self.dsp.printout(msg[1])
    def clear(self):
        self.dsp.clear()
        self.dsp.setRGB(255,255,255)

DSP_TYPE_MAP={'WS1602RGB':WS1602RGB}

if __name__=='__main__':
    c_f=open('config/config.toml','r')
    conf=toml.loads(c_f.read())
    c_f.close()
    print(conf)
    if conf['display']['type'] in DSP_TYPE_MAP:
        dsp=DSP_TYPE_MAP[conf['display']['type']](conf['display'])
        dsp.clear()
        dsp.start()
        cli=MqttClient(conf['connection'],dsp=dsp)
    else:
        cli=MqttClient(conf['connection'])
    cli.run()
    dsp.stop()
    