#!/usr/bin/env python3

import rospy
import numpy as np

from aruco_msgs.msg import MarkerArray
from visualization_msgs.msg import MarkerArray as vMarkerArray
from visualization_msgs.msg import Marker
import tf2_ros

import tf2_geometry_msgs

class AMdetector:
    def __init__(self):
        self.rate = rospy.Rate(10)
        
        #subscriber
        rospy.Subscriber('/camera/aruco/markers',MarkerArray,self.marker_callback)

        #publisher
        self.marker_pub = rospy.Publisher('/marker', vMarkerArray, queue_size=10)

        self.buffer = tf2_ros.Buffer(rospy.Duration(100))
        self.listener = tf2_ros.TransformListener(self.buffer)

        self.marker_array = None
        #print("bashfullll")

        self.init_aruco = np.zeros(4)
        self.marker_array = vMarkerArray()

        while not rospy.is_shutdown():
            self.rate.sleep()

    def marker_callback(self, msg):
        self.marker = msg.markers
        for marker in self.marker:
            if marker.id <= 3 and marker.id != 0 : # id 500 is the map definition marker
                if not self.init_aruco[marker.id]:
                    if marker.pose.pose.position.z <= 1.5:
                        try:
                            #print("trying")
                            trans = self.buffer.lookup_transform("map","camera_color_optical_frame", msg.header.stamp, rospy.Duration(0.5))
                            do_trans = tf2_geometry_msgs.do_transform_pose(marker.pose, trans)
                            self.marker = Marker()
                            self.marker.header.frame_id = "map"
                            self.marker.header.stamp = msg.header.stamp
                            self.marker.ns = "aruco_" + str(marker.id)
                            self.marker.id = marker.id 
                            self.marker.type = Marker.CUBE
                            self.marker.action = Marker.ADD
    
                            self.marker.pose.position = do_trans.pose.position
                            self.marker.pose.orientation = do_trans.pose.orientation
    
                            self.marker.scale.x = 0.05
                            self.marker.scale.y = 0.05
                            self.marker.scale.z = 0.05
                            self.marker.color.a = 1.0
                            self.marker.color.r = 1.0
                            self.marker.color.g = 0.0
                            self.marker.color.b = 0.0
                            self.marker_array.markers.append(self.marker)
                            self.init_aruco[marker.id] = 1
                            # print(self.init_aruco)
                        except:
                            rospy.loginfo("No transform from map to camera")            
        self.pubMarker()

    def pubMarker(self):
        if self.marker_array != None:
            self.marker_pub.publish(self.marker_array)

def main():
    rospy.init_node('AM_detector')
    am = AMdetector()
    while not rospy.is_shutdown():
        if am.detected:
            am.pubMarker()

    print("Shutting down")



if __name__ == '__main__':
    main()