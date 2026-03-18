#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import time
import threading

class PlotterController(Node):

    def __init__(self):
        super().__init__('plotter_controller')

        # 1. Tell the node to sync its clock with Gazebo's physics engine
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pen_pub = self.create_publisher(Float64, '/pen_joint_controller/commands', 10)

        self.get_logger().info("Plotter Controller Started")

        # 2. Run the drawing routine in a background thread!
        # This allows rclpy.spin() to run in the main thread and process clock updates.
        self.thread = threading.Thread(target=self.draw_square)
        self.thread.start()

    def pen_down(self):
        msg = Float64()
        msg.data = -0.025     
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Down")
        time.sleep(1) # Standard sleep is fine here just for the physical delay

    def pen_up(self):
        msg = Float64()
        msg.data = 0.02      
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Up")
        time.sleep(1)

    def wait_for_sim_clock(self):
        # Prevent the loops from starting before Gazebo broadcasts the first clock message
        while self.get_clock().now().nanoseconds == 0:
            time.sleep(0.1)

    def move_forward(self, speed, duration):
        msg = Twist()
        msg.linear.x = speed
        msg.angular.z = 0.0
        self.wait_for_sim_clock()

        start_time = self.get_clock().now()
        dur = rclpy.duration.Duration(seconds=duration)

        # Loop based on SIMULATION time, not real time
        while (self.get_clock().now() - start_time) < dur:
            self.cmd_pub.publish(msg)
            time.sleep(0.05)

        self.stop_robot()

    def rotate(self, angular_speed, duration):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = angular_speed
        self.wait_for_sim_clock()

        start_time = self.get_clock().now()
        dur = rclpy.duration.Duration(seconds=duration)

        while (self.get_clock().now() - start_time) < dur:
            self.cmd_pub.publish(msg)
            time.sleep(0.05)

        self.stop_robot()

    def stop_robot(self):
        msg = Twist()
        self.cmd_pub.publish(msg)
        time.sleep(0.5)

    def draw_square(self):
        time.sleep(2) # Give Gazebo physics a moment to settle
        self.pen_up()
        self.pen_down()

        for _ in range(4):
            self.move_forward(0.5, 3.0)
            self.rotate(0.785, 2.0)

        self.pen_up()
        self.get_logger().info("Drawing Complete")

def main(args=None):
    rclpy.init(args=args)
    node = PlotterController()
    
    # Spin the node so it can receive messages (like the /clock) in the background
    rclpy.spin(node)
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()