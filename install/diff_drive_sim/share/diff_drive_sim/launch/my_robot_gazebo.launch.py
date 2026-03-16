from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os

def generate_launch_description():
    pkg_path = get_package_share_directory('diff_drive_sim')
    ros_gz_sim_pkg_path = get_package_share_directory('ros_gz_sim') 

    robot_description = {
        "robot_description": ParameterValue(
            Command([
                "xacro ",
                os.path.join(pkg_path, "description", "diff_drive.xacro")
            ]),
            value_type=str
        )
    }

    xacro_path = os.path.join(pkg_path, 'description', 'diff_drive.xacro')
    world_path = os.path.join(pkg_path, 'worlds', 'obstacles.sdf')

    # Publish the robot state using the Command substitution
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': Command(['xacro ', xacro_path]),
            'use_sim_time': True  # Essential for Gazebo
        }],
        output='screen',
    )

    # Launch Gazebo (-r runs the simulation immediately)
    launch_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_pkg_path, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': f'-r {world_path}', 
            'on_exit_shutdown': 'true',
        }.items(),
    )

    # Spawn the robot entity in Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'robot',
            '-topic', '/robot_description',
            '-x', '0', '-y', '0', '-z', '0',
        ],
        output='screen',
    )

    # Run the ROS-Gazebo bridge
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': os.path.join(pkg_path, 'config', 'ros_gz_bridge.yaml'),
            'use_sim_time': True
        }],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher_node,
        launch_gazebo,
        spawn_entity,

        Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[
                robot_description,
                os.path.join(pkg_path, "config", "controllers.yaml")
            ],
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster"],
        ),

        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["pen_joint_controller"],
        ),

        ros_gz_bridge,
    ])