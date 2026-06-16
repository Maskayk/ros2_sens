# Sens ROS 2 Quick Start

This workspace contains a minimal proof of concept for the Sens industrial
logging pipeline:

- `sens_interfaces`: custom ROS 2 interfaces.
- `sens_drivers`: simulated PLC input node.
- `sens_storage`: raw log receiver node.

## Build

Run these commands inside the Docker container:

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
```

If `$ROS_DISTRO` is not set, source the installed distribution directly, for
example:

```bash
source /opt/ros/humble/setup.bash
```

or:

```bash
source /opt/ros/jazzy/setup.bash
```

## Run

Open two terminals inside the Docker container.

Terminal 1:

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 run sens_storage storage_node
```

Terminal 2:

```bash
cd /root/ros2_ws
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash
ros2 run sens_drivers sim_plc_node
```

The storage node should print incoming records from `/sens/raw_logs`.

## Optional Checks

Inspect the generated interface:

```bash
ros2 interface show sens_interfaces/msg/RawLog
```

Echo raw messages directly:

```bash
ros2 topic echo /sens/raw_logs
```
