"""Demo of lux sensor and led from raspberry pi
Distributed version - server side: read from an mqtt message queue
and save the datainto a postgres database. We assume the database has
a schema "iot".

Here is the sql to setup the database table (via psql):
drop table if exists events;
drop sequence if exists events_seq;
create sequence events_seq;
create table events (id bigint NOT NULL DEFAULT nextval('events_seq'), ts timestamp NOT NULL, sensor_id integer NOT NULL, val double precision NOT NULL);
"""
import sys
import asyncio
import getpass

from thingflow.base import Scheduler, SensorEvent
from thingflow.adapters.mqtt import MQTTReader
from thingflow.adapters.postgres import PostgresWriter, SensorEventMapping
import thingflow.filters.select
import thingflow.filters.json

connect_string="dbname=iot user=%s" % getpass.getuser()

mapping = SensorEventMapping('events')

def setup(host):
    mqtt = MQTTReader(host, topics=[('bogus/bogus', 2)])
    decoded =  mqtt.select(lambda m:(m.payload).decode("utf-8")) \
                   .from_json(constructor=SensorEvent)
    scheduler = Scheduler(asyncio.get_event_loop())
    decoded.connect(PostgresWriter(scheduler, connect_string, mapping))
    decoded.output()
    mqtt.print_downstream()
    return mqtt, scheduler
    

def main(host):
    mqtt, scheduler = setup(host)
    stop = scheduler.schedule_on_private_event_loop(mqtt)
    print("starting run...")
    try:
        scheduler.run_forever()
    except KeyboardInterrupt:
        stop()
    return 0

if __name__ == '__main__':
    if len(sys.argv)!=2:
        print("%s BROKER" % sys.argv[0])
        sys.exit(1)
    host=sys.argv[1]
    main(host)
