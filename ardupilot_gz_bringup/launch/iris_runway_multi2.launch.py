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

# Adapted from https://github.com/gazebosim/ros_gz_project_template
#
# Copyright 2019 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Launch an iris quadcopter in Gazebo and Rviz."""
import math
import os

from typing import List

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """Generate a launch description for a iris quadcopter."""
    pkg_project_gazebo = get_package_share_directory("ardupilot_gz_gazebo")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    # Declare all launch arguments.
    launch_arguments = generate_launch_arguments()

    # Iris.
    num_rows = 1
    num_cols = 2
    num_robots = num_rows * num_rows
    robots = []
    for i in range(num_robots):
        pos_x = float(i % num_cols)
        pos_y = float(i // num_cols)

        robot = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [
                    PathJoinSubstitution(
                        [
                            FindPackageShare("ardupilot_gz_bringup"),
                            "launch",
                            "robots",
                            "iris_multi2.launch.py",
                        ]
                    ),
                ]
            ),
            launch_arguments={
                "model": "iris_with_gimbal",
                "name": f"iris{i}",
                "x": f"{pos_x}",
                "y": f"{pos_y}",
                "z": "0.2",
                "R": "0.0",
                "P": "0.0",
                "Y": f"{math.pi / 2.0}",
                "instance": f"{i}",
                "sysid": f"{i + 1}",
            }.items(),
        )
        robots.append(robot)

    # Gazebo.
    gz_sim_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": "-v4 -s -r "
            + os.path.join(pkg_project_gazebo, "worlds", "iris_runway_multi.sdf")
        }.items(),
    )

    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": "-v4 -g"}.items(),
    )

    return LaunchDescription(
        launch_arguments
        + [
            gz_sim_server,
            gz_sim_gui,
        ]
        + robots
    )


def generate_launch_arguments() -> List[DeclareLaunchArgument]:
    """Generate a list of launch arguments."""
    return [
        
    ]
