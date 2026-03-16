import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import subprocess
import math

class DrawingNode(Node):

    def __init__(self):
        super().__init__('drawing_node')

        self.pen_down = True
        self.last_x = None
        self.last_y = None
        self.counter = 0

        self.create_subscription(
            Odometry,
            '/model/diff_drive_robot/odometry',
            self.odom_callback,
            10
        )

        self.get_logger().info("Drawing node started")

    def odom_callback(self, msg):

        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self.last_x is None:
            self.last_x = x
            self.last_y = y
            return

        dist = math.sqrt((x-self.last_x)**2 + (y-self.last_y)**2)

        if dist < 0.05:
            return

        if self.pen_down:
            self.spawn_dot(x,y)

        self.last_x = x
        self.last_y = y

    def spawn_dot(self,x,y):

        sdf = f"""
        <sdf version='1.7'>
          <model name='dot_{self.counter}'>
            <static>true</static>
            <link name='link'>
              <visual name='visual'>
                <geometry>
                  <cylinder>
                    <radius>0.005</radius>
                    <length>0.002</length>
                  </cylinder>
                </geometry>
                <material>
                  <ambient>0 0 0 1</ambient>
                </material>
              </visual>
            </link>
          </model>
        </sdf>
        """

        with open("/tmp/dot.sdf","w") as f:
            f.write(sdf)

        subprocess.run([
            "ros2","run","ros_gz_sim","create",
            "-file","/tmp/dot.sdf",
            "-x",str(x),
            "-y",str(y),
            "-z","0.001"
        ])

        self.counter += 1


def main():

    rclpy.init()

    node = DrawingNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()
