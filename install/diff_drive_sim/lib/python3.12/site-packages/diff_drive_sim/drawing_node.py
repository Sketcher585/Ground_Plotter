import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64  # Added import for the pen command
import subprocess
import math

class DrawingNode(Node):

    def __init__(self):
        super().__init__('drawing_node')

        self.pen_down = False # Start with pen up by default
        self.last_x = None
        self.last_y = None
        self.counter = 0

        # Subscribe to odometry
        self.create_subscription(
            Odometry,
            '/model/robot/odometry',
            self.odom_callback,
            10
        )
        
        # Subscribe to the pen joint controller to track up/down state
        self.create_subscription(
            Float64,
            '/pen_joint_controller/commands',
            self.pen_cmd_callback,
            10
        )

        self.get_logger().info("Drawing node started")

    def pen_cmd_callback(self, msg):
        # In your plotter controller, -0.025 is down and 0.02 is up.
        # So if the command is less than 0, the pen is touching the ground.
        if msg.data < 0.0:
            self.pen_down = True
            self.get_logger().info("Drawing Node: Pen is DOWN")
        else:
            self.pen_down = False
            self.get_logger().info("Drawing Node: Pen is UP")

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self.last_x is None:
            self.last_x = x
            self.last_y = y
            return

        dist = math.sqrt((x-self.last_x)**2 + (y-self.last_y)**2)

        if dist < 0.01:
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
                    <radius>0.05</radius>  <length>0.01</length>  </cylinder>
                </geometry>
                <material>
                  <ambient>1 0 0 1</ambient> <diffuse>1 0 0 1</diffuse>
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
            "-z","0.02"  # Lifted slightly higher to prevent floor clipping
        ])

        self.counter += 1

def main():
    rclpy.init()
    node = DrawingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()