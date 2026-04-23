from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, StrictUndefined, UndefinedError

from .schemas import load_template_descriptor, load_values_yaml


def render_template_environment(*, env_root: Path, template_path: Path, values_path: Path) -> str:
    includes = load_template_descriptor(template_path)
    values = load_values_yaml(values_path)
    resolved_root = env_root.resolve()
    fragments: list[str] = []

    for include in includes:
        include_path = env_root / include
        try:
            resolved_include = include_path.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(f"template include not found: {include}") from exc
        if not resolved_include.is_relative_to(resolved_root):
            raise ValueError(f"template include escapes environment root: {include}")
        fragments.append(resolved_include.read_text(encoding="utf-8").rstrip("\n"))

    combined = "\n".join(fragments)
    renderer = Environment(undefined=StrictUndefined, autoescape=False)
    try:
        return renderer.from_string(combined).render(**values)
    except UndefinedError as exc:
        raise ValueError(f"template value is undefined: {exc}") from exc


__all__ = ["render_template_environment"]
