import rosbag
from statistics import SmoothStatistics
import yaml
import math
import fire
TOPICS=['/spot/cmd_vel']

# config=None
# with open('config.yaml', 'r') as file:
#     config = yaml.safe_load(file)
# print (config)
# print (config['id0'])

def started(x):
    if math.fabs(x) > 0.2:
        return True
    else:
        return False
    
def ended(x, offset, duration):
    if math.fabs(x) < 0.05 and offset > duration-30:
        return True
    else:
        return False

def parse_bag(id):
    bagfn=f'{id}.bag'

    print ('processing {} now'.format(bagfn))
    stat = SmoothStatistics('result', 'dwa')
    bag = rosbag.Bag(bagfn)
    info_dict = yaml.load(bag._get_yaml_info())
    print ("info dict duration:", info_dict['duration'])
    t0=0
    start, end = 0, 0
    start_offset, end_offset = 0, 0
    for idx, value in enumerate(bag.read_messages(topics=TOPICS)):
        topic, msg, t = value
        if idx == 0:
            t0 = t.to_sec()
        offset = t.to_sec()-t0
        if started(msg.linear.x) and not ended(msg.linear.x, offset, info_dict['duration']):
            start += 1
            stat.include([msg.linear.x, msg.angular.z])
        if start == 1:
            start_offset = offset
            print (f"{id}: start offset: {offset} ")
        if ended(msg.linear.x, offset, info_dict['duration']):
            end_offset = offset
            print (f"{id}: end offset: {offset} ")
            # break
        # print ('off', offset)
    if end_offset == 0:
        print (f"full end: {offset}")
        end_offset = offset
    print (stat.str())
    print ("Duration: ", end_offset - start_offset)

def main(name='id1'):
    parse_bag(name)

fire.Fire(main)