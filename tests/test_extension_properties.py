import copy
import json
import random

import pytest

from tau_extensions.web import (
    MAX_CANONICAL_VIEW_BYTES,
    MAX_TEXT_BYTES,
    MAX_VIEW_DEPTH,
    MAX_VIEW_NODES,
    Stack,
    StandardView,
    Text,
    ViewError,
    parse_view,
    view_to_json,
)

_UNICODE_CHARS = tuple("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_áβ漢🙂🚀")


def _random_text(rng: random.Random) -> str:
    length = rng.randint(0, 100)
    return "".join(rng.choice(_UNICODE_CHARS) for _ in range(length))


def _build_component(rng: random.Random, depth: int, remaining: list[int]) -> Text | Stack:
    remaining[0] -= 1

    can_stack = depth < 5 and remaining[0] > 0 and rng.random() >= 0.6
    if not can_stack:
        return Text(text=_random_text(rng))

    child_cap = min(3, remaining[0])
    child_count = rng.randint(1, child_cap)
    children: list[Text | Stack] = []
    for _ in range(child_count):
        if remaining[0] <= 0:
            break
        children.append(_build_component(rng, depth + 1, remaining))

    return Stack(direction=rng.choice(("column", "row")), children=tuple(children))


def _generate_standard_view(seed: int) -> StandardView:
    rng = random.Random(seed)
    remaining = [rng.randint(1, 40)]

    components: list[Text | Stack] = []
    while remaining[0] > 0:
        components.append(_build_component(rng, depth=1, remaining=remaining))
        if len(components) >= 8 and rng.random() < 0.5:
            break

    return StandardView(
        kind=rng.choice(("card", "detail", "form")),
        id=f"prop-view-{seed}",
        title=f"Property View {seed}",
        placement=rng.choice(
            (
                "compose_above",
                "compose_below",
                "sidebar",
                "timeline_before",
                "timeline_after",
                "dashboard",
            )
        ),
        components=tuple(components),
    )


def _random_scalar(rng: random.Random) -> object:
    choice = rng.randint(0, 5)
    if choice == 0:
        return None
    if choice == 1:
        return rng.choice((True, False))
    if choice == 2:
        return rng.randint(-10_000, 10_000)
    if choice == 3:
        return rng.uniform(-1_000.0, 1_000.0)
    if choice == 4:
        return _random_text(rng)
    return rng.choice(([], {}))


def _random_json_like(rng: random.Random, depth: int, max_depth: int) -> object:
    if depth >= max_depth:
        return _random_scalar(rng)

    choice = rng.randint(0, 3)
    if choice == 0:
        return _random_scalar(rng)
    if choice == 1:
        return [_random_json_like(rng, depth + 1, max_depth) for _ in range(rng.randint(0, 4))]
    if choice == 2:
        return {
            f"k{depth}_{index}_{rng.randint(0, 999)}": _random_json_like(rng, depth + 1, max_depth)
            for index in range(rng.randint(0, 4))
        }

    return {
        "kind": rng.choice(("card", "detail", "form", "unknown", 123, None)),
        "id": _random_text(rng),
        "title": _random_text(rng),
        "placement": rng.choice(
            (
                "compose_above",
                "compose_below",
                "sidebar",
                "timeline_before",
                "timeline_after",
                "dashboard",
                "footer",
                5,
            )
        ),
        "components": _random_json_like(rng, depth + 1, max_depth),
    }


def _generate_payload(seed: int) -> object:
    if seed % 10 == 0:
        return view_to_json(_generate_standard_view(seed + 1000))
    return _random_json_like(random.Random(seed), depth=0, max_depth=6)


def _walk_components(components: list[object], depth: int = 1) -> tuple[int, int, int]:
    max_depth = depth
    node_count = 0
    max_text_bytes = 0

    for component in components:
        if not isinstance(component, dict):
            continue
        node_count += 1
        kind = component.get("kind")
        if kind == "text":
            text = component.get("text", "")
            if isinstance(text, str):
                max_text_bytes = max(max_text_bytes, len(text.encode("utf-8")))
        elif kind == "stack":
            children = component.get("children", [])
            if isinstance(children, list):
                child_depth, child_nodes, child_max_text = _walk_components(children, depth + 1)
                max_depth = max(max_depth, child_depth)
                node_count += child_nodes
                max_text_bytes = max(max_text_bytes, child_max_text)

    return max_depth, node_count, max_text_bytes


def test_standard_view_text_stack_roundtrip_is_stable_and_non_mutating() -> None:
    for seed in range(100):
        view = _generate_standard_view(seed)
        payload = view_to_json(view)
        before = copy.deepcopy(payload)

        reparsed = parse_view(payload)

        assert payload == before
        assert view_to_json(reparsed) == before


def test_parse_view_handles_arbitrary_json_like_payloads_without_internal_leaks() -> None:
    for seed in range(200):
        payload = _generate_payload(seed)

        try:
            parsed = parse_view(payload)
        except (RecursionError, KeyError) as error:
            pytest.fail(f"seed={seed} leaked {type(error).__name__}: {error}")
        except ViewError:
            continue
        except Exception as error:  # pragma: no cover - explicit hard failure path
            pytest.fail(f"seed={seed} raised unexpected {type(error).__name__}: {error}")

        canonical = view_to_json(parsed)

        try:
            encoded = json.dumps(
                canonical,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as error:
            pytest.fail(f"seed={seed} produced non-serializable canonical JSON: {error}")

        assert len(encoded.encode("utf-8")) <= MAX_CANONICAL_VIEW_BYTES

        max_depth, node_count, max_text_bytes = _walk_components(canonical.get("components", []))
        assert max_depth <= MAX_VIEW_DEPTH
        assert node_count <= MAX_VIEW_NODES
        assert max_text_bytes <= MAX_TEXT_BYTES
