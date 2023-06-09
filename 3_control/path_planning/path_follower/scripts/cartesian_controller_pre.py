#!/usr/bin/env python3

import rospy
import numpy
from robp_msgs.msg import DutyCycles
from robp_msgs.msg import Encoders
from geometry_msgs.msg import Twist 

#we define some constants
Kpa=0.000000012
Kpb=0.000000012
Kia=0.0000000017
Kib=0.0000000017
r=0.04921 #radious of the wheel
b=0.3 #distance between the wheels
f=20 #desired frequency in H
ticks=3072 #number of ticks per rev of the encoder

class CartesianController:
    
    def __init__(self):
        #we initialize some variables
        self.estimated_w_left=0
        self.estimated_w_right=0
        self.desired_w_left=0
        self.desired_w_right=0
        self.integral_error_left=0
        self.integral_error_right=0
        self.msg = False
        self.msg_enc = False
        self.delta_encoder_left = 0
        self.delta_encoder_right = 0
        self.dt_left = 0
        self.dt_right = 0
        self.reset_integral = False

        #we create the subscribers and the publishers
        rospy.Subscriber('/motor/encoders',Encoders,self.encoders_callback,queue_size=1)
        rospy.Subscriber('/motor_controller/twist',Twist,self.twist_callback,queue_size=1)
        self.duty_cycles_pub=rospy.Publisher('/motor/duty_cycles',DutyCycles,queue_size=1)
    
        while not rospy.is_shutdown():
            duty_msg=DutyCycles()

            if self.msg:
                self.estimated_w_left=(2*numpy.pi*r*f*self.delta_encoder_left)/(ticks*r)
                self.estimated_w_right=(2*numpy.pi*r*f*self.delta_encoder_right)/(ticks*r)

                #now we calculate the errors
                left_error=self.desired_w_left-self.estimated_w_left
                right_error=self.desired_w_right-self.estimated_w_right
            
                self.integral_error_left = self.integral_error_left + left_error*self.dt_left
                self.integral_error_right =self.integral_error_right + right_error*self.dt_right
                

                #we calculate now the duty-cycle for each wheel
                 
                # if self.reset_integral:
                #     self.integral_error_left = 0
                #     self.integral_error_right = 0
                #     self.reset_integral = False

                duty_left = Kpa*left_error + Kia*self.integral_error_left
                duty_right = Kpb*right_error + Kib*self.integral_error_right

                # if abs(duty_left) > 1.2 or abs(duty_right) > 1.2:
                #     self.reset_integral = True

                duty_msg.duty_cycle_left=duty_left
                duty_msg.duty_cycle_right=duty_right
                #we publish the duty cycle
                print((self.estimated_w_left+self.estimated_w_right)/2)
                
            else: 
                duty_msg.duty_cycle_left = 0
                duty_msg.duty_cycle_right = 0

            self.duty_cycles_pub.publish(duty_msg)

    def twist_callback(self,msg):
        self.msg = True
        #we get the linear and angular velocity
        v=msg.linear.x
        w=msg.angular.z

        #we estimate the desired angular velocity of each wheel
        r=0.04921 #radious of the wheel
        b=0.3 #distance between the wheels
        self.desired_w_left=(2*v - w*b)/(2*r)
        self.desired_w_right=(2*v + w*b)/(2*r)
        
    
    def encoders_callback(self,msg):
        self.msg_enc = True
        #we get the values of the encoder
        self.delta_encoder_left=msg.delta_encoder_left
        self.delta_encoder_right=msg.delta_encoder_right
        self.dt_left = msg.delta_time_left
        self.dt_right = msg.delta_time_right

if __name__ == '__main__':

    rospy.init_node('cartesian_controller')

    controller=CartesianController()

    rate=rospy.Rate(10)
    
    while not rospy.is_shutdown():

        rate.sleep()
