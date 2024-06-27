#! /bin/bash

# Terminal 1
konsole --new-tab --title "launch" -e bash -c "\
source /opt/ros/humble/setup.bash;\
source ~/ros2_ws/install/setup.bash;\
ros2 launch ardupilot_gz_bringup iris_maze.launch.py rviz:=false use_gz_tf:=true;\
exec bash" &

sleep 1s

# Terminal 2
konsole --new-tab --title "mavproxy" -e bash -c "\
mavproxy.py --master udp:127.0.0.1:14550  --console --map;\
exec bash" &

echo "Done！🚁💻"
