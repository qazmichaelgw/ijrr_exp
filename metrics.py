import rosbag
from statistics import SmoothStatistics
import yaml
import math
import fire
import numpy as np
TOPICS=['/spot/cmd_vel']
TOPICS2 = ['/spot/cmd_vel', '/spot/odometry']

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

def dist(p1, p2):
    return np.linalg.norm(p1 - p2)

def parse_bag(id):
    bagfn=f'{id}.bag'

    print ('processing {} now'.format(bagfn))
    stat = SmoothStatistics('result', 'ijrr')
    bag = rosbag.Bag(bagfn)
    info_dict = yaml.load(bag._get_yaml_info())
    print ("info dict duration:", info_dict['duration'])
    # print (info_dict)
    t0=0
    p0=None
    pt=None
    start, end = 0, 0
    start_offset, end_offset = 0, 0
    # because inet mode always has output. The /spot/vel will never be zero.
    # it moves only if the position changes. 
    s1,s2,e1,e2=[False]*4
    for idx, value in enumerate(bag.read_messages(topics=TOPICS2)):
        topic, msg, t = value
        if idx == 0:
            t0 = t.to_sec()
            if topic == '/spot/odometry':
                p0 = np.array([msg.pose.pose.position.x, msg.pose.pose.position.y])
        if topic == '/spot/odometry':
            pt = np.array([msg.pose.pose.position.x, msg.pose.pose.position.y])

    for idx, value in enumerate(bag.read_messages(topics=TOPICS2)):
        topic, msg, t = value
        offset = t.to_sec()-t0
        if topic == '/spot/cmd_vel':
            if started(msg.linear.x) and not ended(msg.linear.x, offset, info_dict['duration']):
                start += 1
            if start == 1:
                start_offset = offset
                s1 = True
            if ended(msg.linear.x, offset, info_dict['duration']):
                end_offset = offset
                e1 = True
                break

            if s1 and s2 and not e1 and not e2:
                stat.include([msg.linear.x, msg.angular.z])
        elif topic == '/spot/odometry':
            distance = dist(np.array([msg.pose.pose.position.x, msg.pose.pose.position.y]), p0)
            if distance > 0.1:
                if offset > start_offset and s2 == False:
                    start_offset = offset
                    s2 = True

            distance = dist(np.array([msg.pose.pose.position.x, msg.pose.pose.position.y]), pt)
            if distance < 0.3:
                if offset > end_offset and e2 == False:
                    end_offset = offset
                    e2 = True
        # print ('off', offset)
    if end_offset == 0:
        print (f"full end: {offset}")
        end_offset = offset
    print (stat.str())
    print (f"{id}: start offset: {start_offset} ")
    print (f"{id}: end offset: {end_offset} ")
    print ("Duration: ", end_offset - start_offset)

def main(name):
    parse_bag(name)

fire.Fire(main)