import zmq
import json
import threading
from current_state.models import JobState, Location
from tracking_events.models import TrackingEvent
from datetime import datetime

context = zmq.Context()


class Msg:
    def __init__(self, msg_dict):
        self.job_id = msg_dict["job_id"]
        self.location = Location.objects.get(name=msg_dict["location"])
        # if not exists:
        #    raise ValueError("unknown location: {}".format(self.location))
        self.event_type = msg_dict.get("mode", "I")
        self.timestamp = datetime.fromisoformat(msg_dict["timestamp"])

    def __str__(self):
        return f"{super().__str__()}:{self.job_id},{self.location.name},{self.event_type},{self.timestamp}"


class StateModel:
    def __init__(self, zmq_config):
        zmq_in_conf = zmq_config["state_in"]
        self.zmq_in = context.socket(zmq_in_conf["type"])
        if zmq_in_conf["bind"]:
            self.zmq_in.bind(zmq_in_conf["address"])
        else:
            self.zmq_in.connect(zmq_in_conf["address"])

        zmq_out_conf = zmq_config["state_out"]
        self.zmq_out = context.socket(zmq_out_conf["type"])
        if zmq_out_conf["bind"]:
            self.zmq_out.bind(zmq_out_conf["address"])
        else:
            self.zmq_out.connect(zmq_out_conf["address"])

    def start(self):
        t = threading.Thread(target=self.run)
        t.start()

    def run(self):
        while True:
            msg = self.zmq_in.recv()
            msg_json = json.loads(msg)
            print("got ", msg)
            try:
                topic_parts = msg_json["topic"].split("/")
                msg_payload = msg_json["payload"]
                if topic_parts[-1] == "jobs":
                    self.handle_scan(msg_payload)
                elif topic_parts[-1] == "custom_entry_update":
                    self.handle_custom_field_update(msg_payload)
            except Exception as e:
                print("ERROR")
                print(e.msg)

    def handle_custom_field_update(self, msg):
        print(msg)
        try:
            try:
                job = JobState.objects.get(id=msg["id"])
                if "user1" in msg.keys():
                    job.user1 = msg["user1"]
                if "user2" in msg.keys():
                    job.user2 = msg["user2"]
                if "user3" in msg.keys():
                    job.user3 = msg["user3"]
                print(job)
                job.save()
            except JobState.DoesNotExist:
                print(
                    f"Job not found with id {msg['id']}, could not update custom fields"
                )
            # send update event
            update_msg = {
                "id": job.id,
                "state": "changed",
                "location": job.location.name,
                "timestamp": (
                    job.timestamp.isoformat()
                    if isinstance(job.timestamp, datetime)
                    else job.timestamp
                ),
                "user1": job.user1,
                "user2": job.user2,
                "user3": job.user3,
            }
            print(update_msg)
            # send update
            self.zmq_out.send_json(
                {"topic": "state/update/changed", "payload": update_msg}
            )

        except Exception as e:
            print("ERROR")
            print(e.msg)

    def handle_scan(self, raw_msg):
        # TODO: bug with rescan getting caught by two job filter...
        print(raw_msg)
        # listen for incoming events
        try:
            # validate
            msg = Msg(raw_msg)

            # log event
            te = TrackingEvent.objects.create(
                job_id=msg.job_id,
                location=msg.location.name,
                event_type=msg.event_type,
                timestamp=msg.timestamp,
            )

            print(msg)

            old_location = None
            # determine new state
            print('curr_objects ===>>>',JobState.objects.filter(location__exact=msg.location))
            try:
                job = JobState.objects.get(id=msg.job_id)
            except JobState.DoesNotExist:
<<<<<<< HEAD
                job = JobState(id=msg.job_id, location=Location.objects.get(name="New"), timestamp=msg.timestamp)
            print('===>>>',job.location.name,job.timestamp)
=======
                # TODO: this trips up on initial scan as it immmediately transfers to post hold.....
                job = JobState(id=msg.job_id, location=msg.location, timestamp=msg.timestamp)
            print('===>>>',job.location.name,msg.location)
>>>>>>> e72b78e (Update state_model.py)
            last_ts=job.timestamp
            if job.location == msg.location:
                #print(
                #    "Job already scanned to location at {0}, ignoring new scan at {1}".format(
                #        job.timestamp, msg.timestamp
                #    )
                #)
                print('transfer job===>>>',job.location.post_hold)
                if job.location.post_hold:
                    old_location=job.location
                    hold_loc=job.location.post_hold
                    job.location=hold_loc
                    job.timestamp=msg.timestamp
                else:
                    # no post hold.... do nothing this is a conventional section
                    #old_location=job.location
                    #job.location=Location.objects.get(name="Complete")
                    #job.timestamp=msg.timestamp
                    return
            elif len(JobState.objects.filter(location__exact=msg.location))>0:
                self.zmq_out.send_json({"topic": "state/update/error", "payload": {'id':msg.job_id,'state':'error','location':msg.location.name,'message':'scan out first','timestamp':datetime.now().isoformat()}})
                return
            else:
                old_location = job.location
                job.location = msg.location
                job.timestamp = msg.timestamp
            print('===>>>',msg.timestamp,job.timestamp,last_ts)
            if last_ts and old_location and msg.timestamp>=last_ts:
                if old_location.post_hold:
                    c_td=msg.timestamp-last_ts
                    cycle_msg={
                        'job_id':msg.job_id,
                        'state':'complete',
                        'cycle_time':c_td.seconds,
                        'location':old_location.name,
                        "timestamp": (
                            msg.timestamp.isoformat()
                            if isinstance(msg.timestamp, datetime)
                            else msg.timestamp
                        ),
                    }
                    self.zmq_out.send_json({'topic':'timing/cycletime','payload':cycle_msg})
            print('saving ->',job)
            job.save()

            # send update event
            update_msg = {
                "id": job.id,
                "state": "entered",
                "location": job.location.name,
                "timestamp": (
                    job.timestamp.isoformat()
                    if isinstance(job.timestamp, datetime)
                    else job.timestamp
                ),
            }
            print(update_msg)
            # send update
            self.zmq_out.send_json(
                {"topic": "state/update/entered", "payload": update_msg}
            )

            if old_location:
                exit_msg = {
                    "id": job.id,
                    "state": "exited",
                    "location": old_location.name,
                    "timestamp": (
                        job.timestamp.isoformat()
                        if isinstance(job.timestamp, datetime)
                        else job.timestamp
                    ),
                }
                print(exit_msg)
                self.zmq_out.send_json(
                    {"topic": "state/update/exited", "payload": exit_msg}
                )

        except Exception as e:
            print("ERROR")
            print(e)
