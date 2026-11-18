"""5e.tools entry trees (strings, entries, list, table) to card sections."""

from __future__ import annotations

from ...model import Table


def _inline(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_inline(item) for item in value)
    if isinstance(value, dict):
        if "roll" in value:
            return _roll(value["roll"])
        if "exact" in value:
            return str(value["exact"])
        if "entries" in value:
            return " ".join(_inline(item) for item in value["entries"])
        if "entry" in value:
            return _inline(value["entry"])
        if "name" in value:
            return str(value["name"])
    return ""


def _roll(roll: object) -> str:
    if isinstance(roll, str):
        return roll
    if not isinstance(roll, dict):
        return ""
    if "exact" in roll:
        return str(roll["exact"])
    if "min" in roll and "max" in roll:
        return f"{roll['min']}-{roll['max']}"
    return ""


class _Builder:
    def __init__(self) -> None:
        self.sections: list[tuple[str, list[str | Table]]] = [("", [])]

    def heading(self, name: str) -> None:
        self.sections.append((name, []))

    def para(self, text: str, depth: int = 0) -> None:
        self.sections[-1][1].append("  " * depth + text)

    def visit(self, node: object, depth: int = 0) -> None:
        if node is None:
            return
        if isinstance(node, str):
            self.para(node, depth)
            return
        if isinstance(node, list):
            for item in node:
                self.visit(item, depth)
            return
        if not isinstance(node, dict):
            return
        kind = node.get("type")
        if kind == "entries" and node.get("name"):
            before = len(self.sections)
            self.heading(str(node["name"]))
            self.visit(node.get("entries", []), depth)
            if not self.sections[-1][1]:
                del self.sections[before:]
        elif kind in ("list", "options"):
            for item in node.get("items", []):
                self.item(item, depth)
        elif kind == "table":
            self.table(node)
        elif kind in ("inset", "insetReadaloud", "quote"):
            self.visit(node.get("entries", []), depth)
        elif "entries" in node:
            self.visit(node["entries"], depth)
        elif "items" in node:
            for item in node["items"]:
                self.item(item, depth)

    def item(self, item: object, depth: int) -> None:
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if "entry" in item:
                body = _inline(item["entry"])
                self.para("- " + " ".join(part for part in (name, body) if part), depth)
                return
            if "entries" in item or "items" in item:
                if name:
                    self.heading(name)
                self.visit(item, depth)
                return
        self.para("- " + _inline(item), depth)

    def table(self, node: dict) -> None:
        labels = [str(label) for label in (node.get("colLabels") or [])]
        rows = [[_inline(cell) for cell in row] for row in node.get("rows", [])]
        rows = [row for row in rows if any(row)]
        if not rows:
            return
        width = max([len(labels)] + [len(row) for row in rows])
        labels += [""] * (width - len(labels))
        rows = [row + [""] * (width - len(row)) for row in rows]
        header = any(labels)
        self.sections[-1][1].append(Table(([labels] if header else []) + rows, header=header))


def flatten(nodes: object) -> list[tuple[str, list[str | Table]]]:
    builder = _Builder()
    builder.visit(nodes)
    return [(heading, paragraphs) for heading, paragraphs in builder.sections if paragraphs]
