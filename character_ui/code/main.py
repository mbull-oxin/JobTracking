import paho.mqtt.client as mqtt
import toml,logging,datetime

logger=logging.getLogger('Character_UI')

class MqttClient:
    def __init__(self,broker_addr,dsp):
        self._cli=mqtt.Client('local_ui',True)
        self._cli.on_connect=self.onConnect
        self._cli.on_message=self.onMessage
        self._cli.connect('mqtt.docker.local',port=1883)
        self.dsp=dsp
    def onConnect(self,client,userdata,flags,reason_code,properties):
        self._cli.subscribe('state/update/+')
    def onMessage(self,client,userdata,msg):
        ts=datetime.datetime.fromisoformat(msg['timestamp'])
        if msg.topic.endswith('entered'):
            print('job %s entered location' % msg['job_id'])
            self.dsp.show(f'Job: {msg.job_id}\nstarted {ts.hour}:{ts.min}')
        elif msg.topic.endswith('exited'):
            print('job exited')
            self.dsp.show(f'Idle\nSince: {ts.hour}:{ts.min}')
        

class Display:
    '''Base class for displays'''
    lines=2
    def __init__(self,disp_config):
        # override to open display based on config
        self.conf=disp_config
    def show(self,msg):
        if len(msg)>self.lines:
            # too many lines for this display, trim and warn...
            msg=msg[:self.lines]
            logger.info('truncating message with too many lines to %s lines to fit in display' % self.lines)
        # override to show msg on display

class 

if __name__=='__main__':
    c_f=open('config.toml','r')
    conf=toml.loads(c_f.read())
    c_f.close()
    self.