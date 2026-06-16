# Sens Workspace Build Instructions

## Package Layout

```text
src/
  sens_interfaces/
    msg/RawLog.msg
    CMakeLists.txt
    package.xml
  sens_drivers/
    sens_drivers/sim_plc_node.py
    package.xml
    setup.py
    setup.cfg
    resource/sens_drivers
  sens_storage/
    sens_storage/storage_node.py
    package.xml
    setup.py
    setup.cfg
    resource/sens_storage
```

## Full Build From a Clean Shell

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Launch the Proof of Concept

Use two container terminals after the workspace has been built.

Receiver:

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 run sens_storage storage_node
```

Simulator:

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 run sens_drivers sim_plc_node
```

## Simulator Parameters

The PLC simulator publishes one `sens_interfaces/msg/RawLog` message every
50 ms by default. You can tune it at startup:

```bash
ros2 run sens_drivers sim_plc_node --ros-args \
  -p publish_period_ms:=50 \
  -p change_probability:=0.35
```
