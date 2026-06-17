"""ROS 2 service node for static STL dependency analysis."""

from __future__ import annotations

import traceback

import rclpy
from rclpy.node import Node
from sens_interfaces.srv import ParseStl

try:  # Prefer an external/copied stl_parser package when it is installed.
    from stl_parser import Parser
except ImportError:  # Fall back to the parser facade shipped in this ROS package.
    from .parser import Parser

from .graph_adapter import transform_pdg_to_sens_json

_EMPTY_GRAPH_JSON = '{"dependencies":[]}'


class StlAnalyzerNode(Node):
    """Expose STL PDG analysis as a ROS 2 service."""

    def __init__(self) -> None:
        super().__init__("stl_analyzer_node")
        self._parser = Parser()
        self._service = self.create_service(
            ParseStl,
            "/sens/parse_code",
            self.parse_stl_callback,
        )
        self.get_logger().info("STL analyzer service is ready on /sens/parse_code")

    def parse_stl_callback(
        self,
        request: ParseStl.Request,
        response: ParseStl.Response,
    ) -> ParseStl.Response:
        """Parse raw STL text and return the filtered Sens dependency JSON."""

        raw_stl = request.stl_code_text or ""
        self.get_logger().info(f"Received STL analysis request with {len(raw_stl)} characters")

        try:
            pdg_graph = self._parse_to_pdg(raw_stl)
            response.json_graph_output = transform_pdg_to_sens_json(pdg_graph)
            response.success = True
            response.message = "OK"
            return response
        except Exception as exc:  # Keep parser/syntax failures inside the service boundary.
            response.json_graph_output = _EMPTY_GRAPH_JSON
            response.success = False
            response.message = f"{type(exc).__name__}: {exc}"
            self.get_logger().error(f"STL analysis failed: {response.message}")
            self.get_logger().error(traceback.format_exc())
            return response

    def _parse_to_pdg(self, raw_stl: str):
        if hasattr(self._parser, "parse_string_to_pdg"):
            return self._parser.parse_string_to_pdg(raw_stl)
        if hasattr(self._parser, "parse_to_pdg"):
            return self._parser.parse_to_pdg(raw_stl)
        if hasattr(self._parser, "parse"):
            return self._parser.parse(raw_stl)
        raise AttributeError("Parser does not expose a PDG parsing method")


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
