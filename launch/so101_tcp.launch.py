import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    pkg_share_dir = get_package_share_directory('so101_tcp')
    urdf_file = os.path.join(pkg_share_dir, 'urdf', 'so101.urdf')
    bridge_config = os.path.join(pkg_share_dir, 'config', 'bridge.yaml')

    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=os.path.dirname(pkg_share_dir))

    ign_gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments=[('gz_args', '-r empty.sdf')])

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'so101', '-file', urdf_file],
        output='screen')

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config}],
        output='screen')

    controller_node = Node(
        package='so101_tcp',
        executable='tcp_controller',
        output='screen')

    voice_node = Node(
        package='so101_tcp',
        executable='voice_command',
        output='screen')

    return LaunchDescription([
        ign_resource_path,
        ign_gz,
        spawn,
        bridge,
        controller_node,
        voice_node,
    ])
