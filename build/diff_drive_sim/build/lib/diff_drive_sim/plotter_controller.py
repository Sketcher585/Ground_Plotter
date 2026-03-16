#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import time


class PlotterController(Node):

    def __init__(self):
        super().__init__('plotter_controller')

        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        
        self.pen_pub = self.create_publisher(Float64,
                                             '/pen_joint_controller/commands',
                                             10)

        self.get_logger().info("Plotter Controller Started")

        time.sleep(2)

        self.draw_square()



    def pen_down(self):
        msg = Float64()
        msg.data = -0.025     
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Down")
        time.sleep(1)

    def pen_up(self):
        msg = Float64()
        msg.data = 0.02      
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Up")
        time.sleep(1)


    def move_forward(self, speed, duration):
        msg = Twist()
        msg.linear.x = speed
        msg.angular.z = 0.0

        start = time.time()

        while time.time() - start < duration:
            self.cmd_pub.publish(msg)
            time.sleep(0.1)

        self.stop_robot()

    def rotate(self, angular_speed, duration):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = angular_speed

        start = time.time()

        while time.time() - start < duration:
            self.cmd_pub.publish(msg)
            time.sleep(0.1)

        self.stop_robot()

    def stop_robot(self):
        msg = Twist()
        self.cmd_pub.publish(msg)
        time.sleep(0.5)


    def draw_square(self):

        self.pen_up()
        time.sleep(1)

        self.pen_down()

        for _ in range(4):

            self.move_forward(0.5, 3)

            self.rotate(0.785, 2)

        self.pen_up()

        self.get_logger().info("Drawing Complete")


def main(args=None):
    rclpy.init(args=args)

    node = PlotterController()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()