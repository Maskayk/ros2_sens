"""Raw log subscriber for the Sens storage pipeline."""

from __future__ import annotations

import rclpy
from rclpy._rclpy_pybind11 import RCLError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from sens_interfaces.msg import RawLog


class StorageNode(Node):
    """Receive RawLog events and expose them through ROS 2 logging."""

    def __init__(self) -> None:
        super().__init__("storage_node")

        qos_profile = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._subscription = self.create_subscription(
            RawLog,
            "/sens/raw_logs",
            self._on_raw_log,
            qos_profile,
        )

        self.get_logger().info("Storage node started: listening on /sens/raw_logs")

    def _on_raw_log(self, message: RawLog) -> None:
        timestamp = f"{message.timestamp.sec}.{message.timestamp.nanosec:09d}"
        self.get_logger().info(
            f"raw_log tag={message.tag_name} value={message.value} timestamp={timestamp}"
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = StorageNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if rclpy.ok():
            node.get_logger().info("Storage node stopped by operator")
    except (ExternalShutdownException, RCLError):
        pass
    finally:
        try:
            node.destroy_node()
        except RCLError:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
