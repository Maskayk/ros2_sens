"""ROS 2 service node for static STL dependency analysis."""

from __future__ import annotations

import json
import traceback

import rclpy
from rclpy.node import Node
from sens_interfaces.srv import ParseStl

from .analysis.pipeline import analyze
from .graph_adapter import adapt_dependency_graph


class StlAnalyzerNode(Node):
    """Expose tetram1t/stl_parser analysis as a ROS 2 service."""

    def __init__(self) -> None:
        super().__init__("stl_analyzer_node")
        self._service = self.create_service(
            ParseStl,
            "/sens/parse_code",
            self._handle_parse_stl,
        )
        self.get_logger().info("STL analyzer service is ready on /sens/parse_code")

    def _handle_parse_stl(
        self,
        request: ParseStl.Request,
        response: ParseStl.Response,
    ) -> ParseStl.Response:
        code = request.stl_code_text or ""
        self.get_logger().info(f"Received STL analysis request with {len(code)} characters")

        try:
            if not code.strip():
                raise ValueError("stl_code_text is empty")

            ir = analyze(code)
            adapted_graph = adapt_dependency_graph(ir, code)
            response.json_graph_output = json.dumps(
                adapted_graph,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            response.success = True
            response.message = "OK"
            self.get_logger().info(
                f"STL analysis completed: {len(adapted_graph.get('dependencies', []))} dependencies"
            )
            return response

        except (SyntaxError, KeyError, ValueError) as exc:
            response.json_graph_output = json.dumps({"dependencies": []}, separators=(",", ":"))
            response.success = False
            response.message = f"{type(exc).__name__}: {exc}"
            self.get_logger().error(f"STL analysis failed: {response.message}")
            return response
        except Exception as exc:  # Defensive boundary for third-party parser failures.
            response.json_graph_output = json.dumps({"dependencies": []}, separators=(",", ":"))
            response.success = False
            response.message = f"{type(exc).__name__}: {exc}"
            self.get_logger().error(f"Unexpected STL analysis failure: {response.message}")
            self.get_logger().error(traceback.format_exc())
            return response


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = StlAnalyzerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
