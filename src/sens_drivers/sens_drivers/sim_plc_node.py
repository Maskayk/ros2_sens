"""Simulated PLC publisher for Sens raw industrial tag logs."""

from __future__ import annotations

import random
from dataclasses import dataclass

import rclpy
from rclpy._rclpy_pybind11 import RCLError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from sens_interfaces.msg import RawLog


@dataclass(frozen=True)
class SimulatedTag:
    """Configuration for one simulated PLC tag."""

    name: str
    values: tuple[str, ...]


class SimPlcNode(Node):
    """Publish pseudo-random PLC tag state changes as RawLog messages."""

    DEFAULT_TAGS = (
        SimulatedTag("A1_Cyl3_Actuate", ("0", "1")),
        SimulatedTag("A1_Cyl3_Open_Sens", ("0", "1")),
        SimulatedTag("A1_Cyl3_Close_Sens", ("0", "1")),
    )

    def __init__(self) -> None:
        super().__init__("sim_plc_node")

        self.declare_parameter("publish_period_ms", 50)
        self.declare_parameter("change_probability", 0.35)

        publish_period_ms = self.get_parameter("publish_period_ms").value
        self._change_probability = float(self.get_parameter("change_probability").value)
        self._tags = self.DEFAULT_TAGS
        self._state = {tag.name: random.choice(tag.values) for tag in self._tags}

        qos_profile = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self._publisher = self.create_publisher(RawLog, "/sens/raw_logs", qos_profile)
        self._timer = self.create_timer(float(publish_period_ms) / 1000.0, self._on_timer)

        self.get_logger().info(
            "Simulated PLC started: publishing RawLog messages to /sens/raw_logs "
            f"every {publish_period_ms} ms"
        )

    def _on_timer(self) -> None:
        tag = random.choice(self._tags)
        current_value = self._state[tag.name]

        if random.random() < self._change_probability:
            available_values = [value for value in tag.values if value != current_value]
            next_value = random.choice(available_values)
            self._state[tag.name] = next_value
        else:
            next_value = current_value

        message = RawLog()
        message.tag_name = tag.name
        message.value = next_value
        message.timestamp = self.get_clock().now().to_msg()

        self._publisher.publish(message)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SimPlcNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if rclpy.ok():
            node.get_logger().info("Simulated PLC stopped by operator")
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
