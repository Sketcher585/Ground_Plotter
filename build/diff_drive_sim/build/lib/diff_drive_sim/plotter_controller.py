#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64
import time
import threading
import sys
import select
import termios
import tty

class InteractivePlotter(Node):

    def __init__(self):
        super().__init__('interactive_plotter')

        # Sync clock with Gazebo
        self.set_parameters([rclpy.parameter.Parameter('use_sim_time', rclpy.Parameter.Type.BOOL, True)])
        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pen_pub = self.create_publisher(Float64, '/pen_joint_controller/commands', 10)

        self.get_logger().info("Interactive Plotter Started!")
        self.get_logger().info("Click on this terminal window, then press:")
        self.get_logger().info(" [s] - Draw Square")
        self.get_logger().info(" [t] - Draw Triangle")
        self.get_logger().info(" [c] - Draw Circle")
        self.get_logger().info(" [q] or Ctrl+C to Quit")

    # --- PEN CONTROLS ---
    def pen_down(self):
        msg = Float64()
        msg.data = -0.025     
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Down")
        time.sleep(1.0)

    def pen_up(self):
        msg = Float64()
        msg.data = 0.02      
        self.pen_pub.publish(msg)
        self.get_logger().info("Pen Up")
        time.sleep(1.0)

    # --- MOVEMENT CONTROLS ---
    def wait_for_sim_clock(self):
        self.get_logger().info("Waiting for Gazebo clock... (Is Gazebo paused?)")
        while self.get_clock().now().nanoseconds == 0:
            time.sleep(0.1)
        self.get_logger().info("Clock received!")

    def move(self, linear_speed, angular_speed, duration):
        msg = Twist()
        msg.linear.x = float(linear_speed)
        msg.angular.z = float(angular_speed)
        
        self.wait_for_sim_clock()

        start_time = self.get_clock().now()
        dur = rclpy.duration.Duration(seconds=duration)

        while (self.get_clock().now() - start_time) < dur:
            self.cmd_pub.publish(msg)
            time.sleep(0.01) # 100Hz update rate

        self.stop_robot()

    def stop_robot(self):
        self.cmd_pub.publish(Twist())
        time.sleep(0.5)

    # --- SHAPE DRAWING ROUTINES ---
    def draw_square(self):
        self.get_logger().info("Drawing Square...")
        self.pen_down()
        for _ in range(4):
            self.move(linear_speed=0.1, angular_speed=0.0, duration=10.0)
            self.move(linear_speed=0.0, angular_speed=0.2, duration=7.85)
        self.pen_up()
        self.get_logger().info("Square Complete!")

    def draw_triangle(self):
        self.get_logger().info("Drawing Triangle...")
        self.pen_down()
        for _ in range(3):
            self.move(linear_speed=0.1, angular_speed=0.0, duration=10.0)
            self.move(linear_speed=0.0, angular_speed=0.2, duration=10.47)
        self.pen_up()
        self.get_logger().info("Triangle Complete!")

    def draw_circle(self):
        self.get_logger().info("Drawing Circle...")
        self.pen_down()
        self.move(linear_speed=0.1, angular_speed=0.2, duration=31.4)
        self.pen_up()
        self.get_logger().info("Circle Complete!")

    # --- KEYBOARD LISTENER (Now runs in Main Thread) ---
    def keyboard_listener(self):
        settings = termios.tcgetattr(sys.stdin)
        try:
            while rclpy.ok():
                tty.setraw(sys.stdin.fileno())
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                
                if rlist:
                    key = sys.stdin.read(1).lower()
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings) # Restore terminal instantly to print logs
                    
                    if key == 's':
                        self.draw_square()
                    elif key == 't':
                        self.draw_triangle()
                    elif key == 'c':
                        self.draw_circle()
                    elif key == 'q' or key == '\x03': # '\x03' is Ctrl+C
                        self.get_logger().info("Quitting...")
                        break
                else:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        except Exception as e:
            self.get_logger().error(f"Keyboard error: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

def main(args=None):
    rclpy.init(args=args)
    node = InteractivePlotter()
    
    # 1. Spin ROS 2 in a background thread so it can constantly update the clock
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        # 2. Run the keyboard listener in the main thread to prevent terminal lockups
        node.keyboard_listener()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()