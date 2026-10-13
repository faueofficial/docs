#!/usr/bin/env python3
"""Builds the API reference from the OpenAPI contracts.

    python3 tools/build_reference.py

Reads `openapi/gateway.v1.yaml` and `openapi/gateway.admin.v1.yaml` and writes
`api-reference.md` and `admin-api-reference.md` beside this folder: every operation,
what it needs, the request body, and the response with a field table and an example.
The YAML is the source of truth; edit that and rerun, never the generated files.
"""
from __future__ import annotations

import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Spec:
    def __init__(self, path: pathlib.Path) -> None:
        self.doc = yaml.safe_load(path.read_text())

    def resolve(self, node):
        seen = 0
        while isinstance(node, dict) and "$ref" in node and seen < 20:
            cur = self.doc
            for part in node["$ref"][2:].split("/"):
                cur = cur[part]
            node = cur
            seen += 1
        return node

    # --- schema -> rows and example ---------------------------------------
    def flatten(self, schema, name="", required=False, depth=0):
        """Rows of (path, type, required, description) for a schema."""
        rows = []
        schema = self.resolve(schema) or {}
        if "allOf" in schema:
            merged = {"type": "object", "properties": {}, "required": []}
            for part in schema["allOf"]:
                part = self.resolve(part)
                merged["properties"].update(part.get("properties", {}))
                merged["required"] += part.get("required", [])
            merged["description"] = schema.get("description", "")
            schema = merged
        t = schema.get("type")
        if "oneOf" in schema or "anyOf" in schema:
            opts = [self.resolve(o) for o in schema.get("oneOf", schema.get("anyOf"))]
            label = " or ".join(self.type_label(o) for o in opts)
            if name:
                rows.append((name, label, required, schema.get("description", "")))
            return rows
        if t == "object" or "properties" in schema:
            if name:
                rows.append((name, "object", required, schema.get("description", "")))
            req = set(schema.get("required", []))
            for key, sub in (schema.get("properties") or {}).items():
                path = f"{name}.{key}" if name else key
                rows += self.flatten(sub, path, key in req, depth + 1) if depth < 6 else []
            ap = schema.get("additionalProperties")
            if isinstance(ap, dict) and not schema.get("properties"):
                rows.append((f"{name}.<key>" if name else "<key>", self.type_label(self.resolve(ap)), False, ap.get("description", "")))
            return rows
        if t == "array":
            item = self.resolve(schema.get("items", {}))
            if (item.get("type") == "object" or "properties" in item or "allOf" in item) and depth < 6:
                rows.append((name, "array of object", required, schema.get("description", "")))
                rows += self.flatten(item, f"{name}[]", False, depth + 1)
            else:
                rows.append((name, f"array of {self.type_label(item)}", required, schema.get("description", "")))
            return rows
        if name:
            rows.append((name, self.type_label(schema), required, schema.get("description", "")))
        return rows

    def type_label(self, s) -> str:
        s = self.resolve(s) or {}
        if "oneOf" in s or "anyOf" in s:
            return " or ".join(self.type_label(o) for o in s.get("oneOf", s.get("anyOf")))
        if "enum" in s:
            def lit(e):
                if e is None:
                    return "null"
                return f"`{str(e).lower()}`" if isinstance(e, bool) else f"`{e}`"
            # a slash, not a pipe: a pipe would end the table cell
            return " / ".join(lit(e) for e in s["enum"])
        t = s.get("type", "object")
        if isinstance(t, list):
            t = " or ".join("null" if x == "null" else x for x in t)
        if s.get("format"):
            t += f" ({s['format']})"
        return t

    def example(self, schema, depth=0):
        schema = self.resolve(schema) or {}
        if "example" in schema:
            return schema["example"]
        if "allOf" in schema:
            out = {}
            for part in schema["allOf"]:
                e = self.example(part, depth)
                if isinstance(e, dict):
                    out.update(e)
            return out
        if "oneOf" in schema or "anyOf" in schema:
            return self.example(schema.get("oneOf", schema.get("anyOf"))[0], depth)
        t = schema.get("type")
        if isinstance(t, list):
            t = next((x for x in t if x != "null"), "null")
        if "enum" in schema:
            return next((e for e in schema["enum"] if e is not None), None)
        if t == "object" or "properties" in schema:
            if depth > 5:
                return {}
            out = {k: self.example(v, depth + 1) for k, v in (schema.get("properties") or {}).items()}
            ap = schema.get("additionalProperties")
            if not out and isinstance(ap, dict):
                out = {"<key>": self.example(ap, depth + 1)}
            return out
        if t == "array":
            return [self.example(schema.get("items", {}), depth + 1)]
        fmt = schema.get("format")
        return {
            "string": {"uuid": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10", "date-time": "2026-10-13T09:30:00Z", "email": "ada@example.com", "uri": "https://example.com/..."}.get(fmt, "string"),
            "integer": 0, "number": 0, "boolean": True, "null": None,
        }.get(t, None)


def md_table(rows):
    if not rows:
        return ""
    out = ["| Field | Type | Required | Notes |", "|---|---|---|---|"]
    for name, typ, req, desc in rows:
        desc = " ".join(str(desc or "").split()).replace("|", "\\|")
        out.append(f"| `{name}` | {typ} | {'yes' if req else ''} | {desc} |")
    return "\n".join(out)


def schema_block(spec: Spec, schema) -> str:
    rows = spec.flatten(schema)
    ex = spec.example(schema)
    parts = []
    if rows:
        parts.append(md_table(rows))
    if ex not in (None, {}, []):
        parts.append("```json\n" + json.dumps(ex, indent=2, ensure_ascii=False) + "\n```")
    return "\n\n".join(parts)


def render(spec: Spec, title: str, intro: str) -> str:
    d = spec.doc
    lines = [f"# {title}", "", "> Generated from the OpenAPI contract by `tools/build_reference.py`. Do not edit by hand.", "", intro, ""]
    servers = ", ".join(f"`{s['url']}`" for s in d.get("servers", [])[:1])
    lines += [f"**Base URL:** {servers}", ""]
    tags = [t["name"] for t in d.get("tags", [])]
    tag_desc = {t["name"]: t.get("description", "") for t in d.get("tags", [])}
    ops: dict[str, list] = {t: [] for t in tags}
    for path, item in d["paths"].items():
        shared = item.get("parameters", [])
        for method, op in item.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tag = (op.get("tags") or ["other"])[0]
            ops.setdefault(tag, []).append((path, method.upper(), op, shared))
    lines += ["## Contents", ""]
    for t, lst in ops.items():
        if lst:
            lines.append(f"- [{t}](#{t}) ({len(lst)})")
    lines.append("")
    for t, lst in ops.items():
        if not lst:
            continue
        lines += [f"## {t}", "", tag_desc.get(t, ""), ""]
        for path, method, op, shared in lst:
            lines += [f"### `{method} {path}`", "", f"**{op.get('summary', '')}**", ""]
            if op.get("deprecated"):
                lines += ["> **Deprecated.**", ""]
            if op.get("description"):
                lines += [op["description"].strip(), ""]
            sec = op.get("security", d.get("security", []))
            lines += ["**Auth:** " + ("none" if sec == [] else "bearer token"), ""]
            params = [spec.resolve(p) for p in shared + op.get("parameters", [])]
            if params:
                lines += ["**Parameters**", "", "| Name | In | Type | Required | Notes |", "|---|---|---|---|---|"]
                for p in params:
                    sch = spec.resolve(p.get("schema", {}))
                    lines.append(f"| `{p['name']}` | {p['in']} | {spec.type_label(sch)} | {'yes' if p.get('required') else ''} | {' '.join(str(p.get('description', '')).split())} |")
                lines.append("")
            body = op.get("requestBody")
            if body:
                for ctype, media in spec.resolve(body)["content"].items():
                    lines += [f"**Request body** (`{ctype}`)", "", schema_block(spec, media.get("schema", {})), ""]
            lines += ["**Responses**", ""]
            for code, resp in op.get("responses", {}).items():
                resp = spec.resolve(resp)
                lines += [f"- **{code}**: {' '.join(str(resp.get('description', '')).split())}"]
                for ctype, media in (resp.get("content") or {}).items():
                    if ctype == "application/problem+json":
                        lines.append("  - body: `application/problem+json`, see *Errors* in the guide")
                    elif ctype.startswith("image/"):
                        lines.append(f"  - body: `{ctype}` (binary image)")
                    elif media.get("schema"):
                        lines += ["", f"  Body (`{ctype}`):", "", schema_block(spec, media["schema"]), ""]
            lines.append("")
    # shared schemas, for anyone generating types by hand
    lines += ["## Schemas", ""]
    for name, schema in d["components"]["schemas"].items():
        lines += [f"### {name}", "", schema_block(spec, {"$ref": f"#/components/schemas/{name}"}), ""]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    pub = Spec(ROOT / "openapi" / "gateway.v1.yaml")
    adm = Spec(ROOT / "openapi" / "gateway.admin.v1.yaml")
    (ROOT / "api-reference.md").write_text(render(
        pub, "FAUE API reference (v1)",
        "Every endpoint the mobile app and the website use, with request and response schemas. Read "
        "[app-developer-guide.md](app-developer-guide.md) first for authentication, errors, pagination and flows.",
    ))
    (ROOT / "admin-api-reference.md").write_text(render(
        adm, "FAUE admin API reference (v1)",
        "The operations console's API. A separate auth realm from the public API. Read "
        "[app-developer-guide.md](app-developer-guide.md#the-admin-api) for how it signs in.",
    ))
    print("wrote api-reference.md and admin-api-reference.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
