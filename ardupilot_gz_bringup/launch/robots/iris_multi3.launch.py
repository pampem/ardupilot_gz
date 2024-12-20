# Copyright 2023 ArduPilot.org.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Launch an iris quadcopter in Gazebo and Rviz.

ros2 launch ardupilot_sitl sitl_dds_udp.launch.py
transport:=udp4
refs:=$(ros2 pkg prefix ardupilot_sitl)
      /share/ardupilot_sitl/config/dds_xrce_profile.xml
port:=2019
synthetic_clock:=True
wipe:=False
model:=json
speedup:=1
slave:=0
instance:=0
defaults:=$(ros2 pkg prefix ardupilot_sitl)
          /share/ardupilot_sitl/config/default_params/gazebo-iris.parm,
          $(ros2 pkg prefix ardupilot_sitl)
          /share/ardupilot_sitl/config/default_params/dds_udp.parm
sim_address:=127.0.0.1
master:=tcp:127.0.0.1:5760
sitl:=127.0.0.1:5501
"""
import os

from typing import List

from ament_index_python.packages import get_package_share_directory

from launch import LaunchContext
from launch import LaunchDescription
from launch import LaunchDescriptionEntity
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def launch_robot_state_publisher(
    context: LaunchContext, *args, **kwargs
) -> List[LaunchDescriptionEntity]:
    """Return a robot state publisher launch description."""
    # Packages.
    pkg_ardupilot_gazebo = get_package_share_directory("ardupilot_gazebo")

    # Get substitutions for arguments.
    name = LaunchConfiguration("name").perform(context)
    instance = int(LaunchConfiguration("instance").perform(context))

    # Compute ports
    port_offset = 10 * instance
    control_port = 9002 + port_offset

    # Set `SDF_PATH` required by `sdformat_urdf`.
    if "GZ_SIM_RESOURCE_PATH" in os.environ:
        gz_sim_resource_path = os.environ["GZ_SIM_RESOURCE_PATH"]
        if "SDF_PATH" in os.environ:
            sdf_path = os.environ["SDF_PATH"]
            os.environ["SDF_PATH"] = sdf_path + ":" + gz_sim_resource_path
        else:
            os.environ["SDF_PATH"] = gz_sim_resource_path

    # Load SDF file.
    sdf_file = os.path.join(
        pkg_ardupilot_gazebo, "models", "iris_with_gimbal", "model.sdf"
    )
    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    # Update SDFormat:
    #
    # <include> iris_with_standoffs
    #   <name>iris</name>
    #
    # OdometryPublisher frames
    #   <odom_frame>iris/odom</odom_frame>
    #   <robot_base_frame>iris</robot_base_frame>
    #
    # ArduPilotPlugin port
    #   <fdm_port_in>9002</fdm_port_in>
    #
    robot_desc = robot_desc.replace("<name>iris</name>", f"<name>{name}</name>")
    robot_desc = robot_desc.replace(
        "<odom_frame>iris/odom</odom_frame>", f"<odom_frame>{name}/odom</odom_frame>"
    )
    robot_desc = robot_desc.replace(
        "<robot_base_frame>iris</robot_base_frame>",
        f"<robot_base_frame>{name}</robot_base_frame>",
    )
    robot_desc = robot_desc.replace(
        "<fdm_port_in>9002</fdm_port_in>", f"<fdm_port_in>{control_port}</fdm_port_in>"
    )

    # print(robot_desc)

    # Remap the `tf` and `tf_static` under `ignore` to prevent conflicts.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        namespace=f"{name}",
        output="both",
        parameters=[
            {"robot_description": robot_desc},
            # {"frame_prefix": f"{name}/"},
        ],
        remappings=[
            ("/tf", "ignore/tf"),
            ("/tf_static", "ignore/tf_static"),
        ],
    )
    return [robot_state_publisher]


def launch_spawn_robot(
    context: LaunchContext, *args, **kwargs
) -> List[LaunchDescriptionEntity]:
    """Return a Gazebo spawn robot launch description."""
    # Get substitutions for arguments.
    name = LaunchConfiguration("name")
    pos_x = LaunchConfiguration("x")
    pos_y = LaunchConfiguration("y")
    pos_z = LaunchConfiguration("z")
    rot_r = LaunchConfiguration("R")
    rot_p = LaunchConfiguration("P")
    rot_y = LaunchConfiguration("Y")

    # Spawn robot.
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        namespace=name,
        arguments=[
            "-world",
            "",
            "-param",
            "",
            "-name",
            name,
            "-topic",
            "robot_description",
            "-x",
            pos_x,
            "-y",
            pos_y,
            "-z",
            pos_z,
            "-R",
            rot_r,
            "-P",
            rot_p,
            "-Y",
            rot_y,
        ],
        output="screen",
    )
    return [spawn_robot]


def launch_bridge(
    context: LaunchContext, *args, **kwargs
) -> List[LaunchDescriptionEntity]:
    """Return a ros_gz_bridge action."""
    # Packages.
    pkg_project_bringup = get_package_share_directory("ardupilot_gz_bringup")

    # Retrieve launch arguments.
    name = LaunchConfiguration("name").perform(context)

    # Bridge - launching the node in a namespace also places the /tf
    # in a namespace, so we need to undo the mapping.
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        namespace=name,
        parameters=[
            {
                "config_file": os.path.join(
                    pkg_project_bringup, "config", "iris_bridge_multi.yaml"
                ),
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        remappings=[
            (f"/{name}/tf", "/tf"),
            (f"/{name}/tf_static", "/tf_static"),
        ],
        output="screen",
    )
    return [bridge]


def generate_launch_description() -> LaunchDescription:
    """Generate a launch description for a iris quadcopter."""
    launch_arguments = generate_launch_arguments()

    return LaunchDescription(
        launch_arguments
        + [OpaqueFunction(function=launch_robot_state_publisher)]
        + [OpaqueFunction(function=launch_spawn_robot)]
        # + [OpaqueFunction(function=launch_bridge)]
    )


def generate_launch_arguments() -> List[DeclareLaunchArgument]:
    """Generate a list of launch arguments."""
    return [
        # Gazebo model launch arguments.
        DeclareLaunchArgument(
            "model",
            default_value="iris",
            description="Name or filepath of the model to load.",
        ),
        DeclareLaunchArgument(
            "name",
            default_value="iris",
            description="Name for the model instance.",
        ),
        DeclareLaunchArgument(
            "x",
            default_value="0",
            description="The intial 'x' position (m).",
        ),
        DeclareLaunchArgument(
            "y",
            default_value="0",
            description="The intial 'y' position (m).",
        ),
        DeclareLaunchArgument(
            "z",
            default_value="0",
            description="The intial 'z' position (m).",
        ),
        DeclareLaunchArgument(
            "R",
            default_value="0",
            description="The intial roll angle (radians).",
        ),
        DeclareLaunchArgument(
            "P",
            default_value="0",
            description="The intial pitch angle (radians).",
        ),
        DeclareLaunchArgument(
            "Y",
            default_value="0",
            description="The intial yaw angle (radians).",
        ),
        # SITL launch arguments.
        DeclareLaunchArgument(
            "instance",
            default_value="0",
            description="Set instance of SITL "
            "(adds 10*instance to all port numbers).",
        ),
        # Optional SITL launch arguments.
        DeclareLaunchArgument(
            "sysid",
            default_value="",
            description="Set SYSID_THISMAV.",
        ),
    ]
