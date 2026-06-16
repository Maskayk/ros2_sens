import re
try:
    from .expression_parser import build_expression
except ImportError:
    from expression_parser import build_expression

def parse_stl_mvp(code: str) -> dict:
    if not code:
        return {
            "warnings": [],
            "labels": {},
            "instructions": [],
            "cfg_edges": []
        }

    lines = code.split("\n")

    instructions = []
    labels_map = {}
    cfg_edges = []
    warnings = []

    pattern = re.compile(
        r'^\s*(?:(\w+)\s*:\s*)?([^\s]+)?(\s+.*)?$'
    )

    for idx, line in enumerate(lines):
        raw_line = line.strip()

        if not raw_line:
            continue

        if "//" in raw_line:
            raw_line = raw_line.split("//")[0].strip()

            if not raw_line:
                continue

        match = pattern.match(raw_line)

        if not match:
            warnings.append({
                "line": idx + 1,
                "type": "unparsed_line",
                "message": f"Could not parse line structure: '{line.strip()}'"
            })
            continue

        label, opcode, operand = match.group(1), match.group(2), match.group(3)

        inst_id = len(instructions)

        if label:
            if label in labels_map:
                warnings.append({
                    "line": idx + 1,
                    "type": "duplicate_label",
                    "message": f"Label '{label}' is already defined at instruction ID {labels_map[label]}"
                })
            else:
                labels_map[label] = inst_id

        if operand:
            operand = operand.strip()

        if opcode in ["A(", "O(", ")", "NOT", "SAVE"] or (
            opcode and opcode.endswith("(")
        ):
            warnings.append({
                "line": idx + 1,
                "type": "complex_syntax_stub",
                "message": f"Opcode '{opcode}' lacks expression-tree context for deeper Data-Flow."
            })

        instructions.append({
            "id": inst_id,
            "line": idx + 1,
            "label": label,
            "opcode": opcode,
            "operand": operand if operand else None
        })

    for inst in instructions:
        curr_id = inst["id"]
        opcode = inst["opcode"]
        operand = inst["operand"]

        if opcode in ["JU", "JC"]:
            kind = "jump" if opcode == "JU" else "branch_true"

            if operand not in labels_map:
                warnings.append({
                    "line": inst["line"],
                    "type": "unresolved_jump_target",
                    "message": f"Instruction '{opcode} {operand}' points to a non-existent label."
                })

                cfg_edges.append({
                    "from": curr_id,
                    "target_label": operand,
                    "resolved_target_id": None,
                    "kind": f"{opcode.lower()}_unresolved_target"
                })

            else:
                cfg_edges.append({
                    "from": curr_id,
                    "target_label": operand,
                    "resolved_target_id": labels_map[operand],
                    "kind": kind
                })

            if opcode == "JC" and curr_id + 1 < len(instructions):
                cfg_edges.append({
                    "from": curr_id,
                    "target_label": None,
                    "resolved_target_id": curr_id + 1,
                    "kind": "fallthrough"
                })

        else:
            if curr_id + 1 < len(instructions):
                cfg_edges.append({
                    "from": curr_id,
                    "target_label": None,
                    "resolved_target_id": curr_id + 1,
                    "kind": "fallthrough"
                })

    return {
        "warnings": warnings,
        "labels": labels_map,
        "instructions": instructions,
        "cfg_edges": cfg_edges
    }