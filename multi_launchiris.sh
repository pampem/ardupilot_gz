#! /bin/bash

# Terminal 1
konsole --new-tab --title "launch" -e bash -c "\
source /opt/ros/humble/setup.bash;\
source ~/ros2_ws/install/setup.bash;\
ros2 run micro_ros_agent micro_ros_agent udp4 -p 2019;\
exec bash" &

sleep 2s

# Terminal 2
konsole --new-tab --title "launch" -e bash -c "\
source /opt/ros/humble/setup.bash;\
source ~/ros2_ws/install/setup.bash;\
ros2 launch ardupilot_gz_bringup iris_runway_multi.launch.py rviz:=false use_gz_tf:=true;\
exec bash" &

sleep 1s # コマンドが完了するのを待つ

# Terminal 3
konsole --new-tab --title "mavproxy" -e bash -c "\
mavproxy.py --master udp:127.0.0.1:14550  --console --map;\
exec bash" &

echo "Done！🚁💻"
