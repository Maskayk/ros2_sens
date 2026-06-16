"""Convert academic STL dependency analysis into industrial JSON edges."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

INPUT_OPCODES = {"A", "AN", "O", "ON", "L"}
INVERTING_OPCODES = {"AN", "ON"}
OUTPUT_OPCODES = {"=", "S", "R", "T"}
STRUCTURAL_OPCODES = {
    "NETWORK",
    "TITLE",
    "FUNCTION",
    "FUNCTION_BLOCK",
    "ORGANIZATION_BLOCK",
    "DATA_BLOCK",
    "BEGIN",
    "END_FUNCTION",
    "END_FUNCTION_BLOCK",
    "END_ORGANIZATION_BLOCK",
    "END_DATA_BLOCK",
}
NOISE_OPERAND_RE = re.compile(
    r"^(?:AKKU|ACCU|AR[12]?|BR|BIE|OV|OS|OR|STA|RLO|CC[01]?|DBNO|DINO|STW|"
    r"ACCU[12]|P##|TEMP|#TEMP|L#|W#|B#|DW#|[+-]?\d+(?:\.\d+)?|[A-Z]+\d+:)$",
    re.IGNORECASE,
)
INTERNAL_ADDRESS_RE = re.compile(
    r"^(?:M|MB|MW|MD|DB|DBB|DBW|DBD|DI|DIB|DIW|DID|L|LB|LW|LD)\d+(?:\.\d+)?$",
    re.IGNORECASE,
)
PHYSICAL_ADDRESS_RE = re.compile(
    r"^(?:I|IB|IW|ID|E|EB|EW|ED|Q|QB|QW|QD|A|AB|AW|AD|PI|PQ|PE|PA)\d+(?:\.\d+)?$",
    re.IGNORECASE,
)
BLOCK_RE = re.compile(
    r'^\s*(?:FUNCTION|FUNCTION_BLOCK|ORGANIZATION_BLOCK|FC|FB|OB)\s+"?([A-Za-z_][\w$]*)"?',
    re.IGNORECASE,
)
NETWORK_RE = re.compile(r"^\s*NETWORK(?:\s+(\d+))?\b", re.IGNORECASE)


@dataclass(frozen=True)
class InstructionContext:
    block_name: str
    network_number: int


@dataclass(frozen=True)
class SourceOperand:
    name: str
    inverted: bool


def adapt_dependency_graph(ir: dict[str, Any], stl_code_text: str) -> dict[str, list[dict[str, Any]]]:
    """Return clean source-to-target equipment dependencies.

    The upstream project exposes a parser, CFG, reaching definitions and a dependency graph.
    This adapter keeps that IR as the parse authority, then projects instruction-level STL
    boolean/data logic into commissioning-oriented edges grouped by Siemens NETWORK blocks.
    """

    instructions = ir.get("instructions", [])
    line_context = extract_line_context(stl_code_text)
    dependencies: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int, str]] = set()

    for network in group_instructions_by_network(instructions, line_context):
        sources: list[SourceOperand] = []

        for inst in network:
            opcode = normalize_opcode(inst.get("opcode"))
            operand = normalize_operand(inst.get("operand"))

            if not opcode or opcode in STRUCTURAL_OPCODES:
                continue

            if opcode in INPUT_OPCODES and is_real_signal(operand, role="source"):
                sources.append(SourceOperand(name=operand, inverted=opcode in INVERTING_OPCODES))
                continue

            if opcode in OUTPUT_OPCODES and is_real_signal(operand, role="target"):
                ctx = context_for_instruction(inst, line_context)
                for source in sources:
                    edge_type = "inverted" if source.inverted else "direct_logic"
                    key = (source.name, operand, ctx.block_name, ctx.network_number, edge_type)
                    if key in seen:
                        continue
                    seen.add(key)
                    dependencies.append(
                        {
                            "source": source.name,
                            "target": operand,
                            "block_name": ctx.block_name,
                            "network_number": ctx.network_number,
                            "type": edge_type,
                        }
                    )

                if opcode == "T":
                    sources = []

    return {"dependencies": dependencies}


def extract_line_context(stl_code_text: str) -> dict[int, InstructionContext]:
    """Map raw STL line numbers to block and network metadata."""

    block_name = "UNKNOWN_BLOCK"
    network_number = 0
    implicit_network = 0
    contexts: dict[int, InstructionContext] = {}

    for line_number, raw_line in enumerate(stl_code_text.splitlines(), start=1):
        line = strip_comment(raw_line).strip()
        if not line:
            continue

        block_match = BLOCK_RE.match(line)
        if block_match:
            block_name = block_match.group(1)
            network_number = 0
            implicit_network = 0

        network_match = NETWORK_RE.match(line)
        if network_match:
            if network_match.group(1):
                network_number = int(network_match.group(1))
            else:
                implicit_network += 1
                network_number = implicit_network

        contexts[line_number] = InstructionContext(
            block_name=block_name,
            network_number=network_number,
        )

    return contexts


def group_instructions_by_network(
    instructions: Iterable[dict[str, Any]],
    line_context: dict[int, InstructionContext],
) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_key: tuple[str, int] | None = None

    for inst in instructions:
        ctx = context_for_instruction(inst, line_context)
        key = (ctx.block_name, ctx.network_number)
        opcode = normalize_opcode(inst.get("opcode"))

        if current and (key != current_key or opcode == "NETWORK"):
            groups.append(current)
            current = []

        current_key = key
        current.append(inst)

    if current:
        groups.append(current)

    return groups


def context_for_instruction(
    inst: dict[str, Any],
    line_context: dict[int, InstructionContext],
) -> InstructionContext:
    line = inst.get("line")
    if isinstance(line, int) and line in line_context:
        return line_context[line]
    return InstructionContext(block_name="UNKNOWN_BLOCK", network_number=0)


def normalize_opcode(opcode: Any) -> str:
    return str(opcode or "").strip().upper()


def normalize_operand(operand: Any) -> str:
    value = str(operand or "").strip()
    if not value:
        return ""
    value = value.split("//", 1)[0].strip()
    return value.strip('"')


def strip_comment(line: str) -> str:
    return line.split("//", 1)[0]


def is_real_signal(operand: str, role: str) -> bool:
    if not operand:
        return False

    cleaned = operand.strip()
    if NOISE_OPERAND_RE.match(cleaned):
        return False
    if cleaned.endswith(":"):
        return False
    if cleaned.startswith(("#", "P#")):
        return False
    if INTERNAL_ADDRESS_RE.match(cleaned):
        return False

    if PHYSICAL_ADDRESS_RE.match(cleaned):
        return True

    has_letter = any(ch.isalpha() for ch in cleaned)
    if not has_letter:
        return False

    upper = cleaned.upper()
    if role == "target" and upper.startswith(("TMP", "TEMP", "AUX", "INT_")):
        return False

    return True
