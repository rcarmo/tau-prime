"""Portable declarative web UI contracts for Tau extensions."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, cast

from tau_agent.types import JSONObject, JSONPrimitive, JSONValue

MAX_CANONICAL_VIEW_BYTES = 64 * 1024
MAX_VIEW_DEPTH = 12
MAX_VIEW_NODES = 256
MAX_TEXT_BYTES = 16 * 1024
MAX_ACTION_PAYLOAD_BYTES = 8 * 1024
MAX_TABLE_ROWS = 50
MAX_TABLE_COLUMNS = 20

type Placement = Literal[
    "compose_above",
    "compose_below",
    "sidebar",
    "timeline_before",
    "timeline_after",
    "dashboard",
]
type StandardViewKind = Literal["card", "detail", "form"]
type TextStyle = Literal["normal", "muted", "code"]
type ButtonVariant = Literal["default", "primary", "secondary", "danger", "ghost"]
type FieldInputType = Literal["text", "textarea", "select"]
type StackDirection = Literal["row", "column"]
type FrozenJSONValue = JSONPrimitive | tuple[FrozenJSONValue, ...] | Mapping[str, FrozenJSONValue]
type FrozenJSONObject = Mapping[str, FrozenJSONValue]

_VIEW_KINDS: tuple[StandardViewKind, ...] = ("card", "detail", "form")
_PLACEMENTS: tuple[Placement, ...] = (
    "compose_above",
    "compose_below",
    "sidebar",
    "timeline_before",
    "timeline_after",
    "dashboard",
)
_TEXT_STYLES: tuple[TextStyle, ...] = ("normal", "muted", "code")
_BUTTON_VARIANTS: tuple[ButtonVariant, ...] = (
    "default",
    "primary",
    "secondary",
    "danger",
    "ghost",
)
_FIELD_INPUT_TYPES: tuple[FieldInputType, ...] = ("text", "textarea", "select")
_STACK_DIRECTIONS: tuple[StackDirection, ...] = ("row", "column")
_COMPONENT_KINDS: tuple[str, ...] = (
    "button",
    "field",
    "metric",
    "progress",
    "stack",
    "table",
    "text",
)
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


class ViewError(ValueError):
    """Stable error raised for declarative view parsing and validation failures."""


@dataclass(frozen=True, slots=True)
class Text:
    """Static or live text content."""

    text: str
    style: TextStyle = "normal"
    live: bool = False
    kind: Literal["text"] = "text"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "text",
            _require_string(self.text, path="text", max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(
            self,
            "style",
            cast(TextStyle, _require_literal(self.style, path="style", allowed=_TEXT_STYLES)),
        )
        object.__setattr__(self, "live", _require_bool(self.live, path="live"))


@dataclass(frozen=True, slots=True)
class Button:
    """Portable action trigger without runtime behavior."""

    label: str
    action_id: str
    accessible_label: str | None = None
    payload: FrozenJSONObject = field(default_factory=lambda: _empty_frozen_object())
    variant: ButtonVariant = "default"
    icon_only: bool = False
    kind: Literal["button"] = "button"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(self, "action_id", _require_slug(self.action_id, path="action_id"))
        object.__setattr__(self, "icon_only", _require_bool(self.icon_only, path="icon_only"))
        if self.accessible_label is None:
            if self.icon_only:
                raise ViewError("accessible_label is required when icon_only is true")
        else:
            object.__setattr__(
                self,
                "accessible_label",
                _require_string(
                    self.accessible_label,
                    path="accessible_label",
                    non_blank=True,
                    max_chars=128,
                    max_bytes=MAX_TEXT_BYTES,
                ),
            )
        object.__setattr__(
            self,
            "payload",
            _freeze_json_object(self.payload, path="payload"),
        )
        _validate_json_size(self.payload, path="payload", limit=MAX_ACTION_PAYLOAD_BYTES)
        object.__setattr__(
            self,
            "variant",
            cast(
                ButtonVariant,
                _require_literal(self.variant, path="variant", allowed=_BUTTON_VARIANTS),
            ),
        )


@dataclass(frozen=True, slots=True)
class Metric:
    """One labelled summary metric."""

    label: str
    value: str | int | float
    unit: str | None = None
    kind: Literal["metric"] = "metric"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(self, "value", _require_metric_value(self.value, path="value"))
        if self.unit is not None:
            object.__setattr__(
                self,
                "unit",
                _require_string(self.unit, path="unit", non_blank=True, max_bytes=MAX_TEXT_BYTES),
            )


@dataclass(frozen=True, slots=True)
class Progress:
    """One bounded progress value."""

    label: str
    value: int | float
    max: int | float
    kind: Literal["progress"] = "progress"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        max_value = _require_number(self.max, path="max")
        if max_value <= 0:
            raise ViewError("max must be greater than 0")
        value = _require_number(self.value, path="value")
        if value < 0 or value > max_value:
            raise ViewError("value must be between 0 and max")
        object.__setattr__(self, "max", max_value)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True, slots=True)
class FieldOption:
    """One declarative select option."""

    label: str
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(
            self,
            "value",
            _require_string(self.value, path="value", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )


@dataclass(frozen=True, slots=True)
class Field:
    """Portable form input description."""

    name: str
    label: str
    input_type: FieldInputType
    required: bool = False
    value: str | None = None
    options: tuple[FieldOption, ...] = ()
    kind: Literal["field"] = "field"

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _require_slug(self.name, path="name"))
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(
            self,
            "input_type",
            cast(
                FieldInputType,
                _require_literal(self.input_type, path="input_type", allowed=_FIELD_INPUT_TYPES),
            ),
        )
        object.__setattr__(self, "required", _require_bool(self.required, path="required"))
        if self.value is not None:
            object.__setattr__(
                self,
                "value",
                _require_string(self.value, path="value", max_bytes=MAX_TEXT_BYTES),
            )
        options = tuple(self.options)
        if not all(isinstance(option, FieldOption) for option in options):
            raise ViewError("options must contain only FieldOption values")
        if self.input_type == "select":
            if not options:
                raise ViewError("options is required when input_type is select")
            if self.value is not None and self.value not in {option.value for option in options}:
                raise ViewError("value must match a declared option")
        elif options:
            raise ViewError("options is only allowed when input_type is select")
        object.__setattr__(self, "options", options)


@dataclass(frozen=True, slots=True)
class TableColumn:
    """One declared table column."""

    label: str
    key: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        object.__setattr__(self, "key", _require_slug(self.key, path="key"))


@dataclass(frozen=True, slots=True)
class Table:
    """Portable table contribution."""

    label: str
    columns: tuple[TableColumn, ...]
    rows: tuple[FrozenJSONObject, ...] = ()
    kind: Literal["table"] = "table"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "label",
            _require_string(self.label, path="label", non_blank=True, max_bytes=MAX_TEXT_BYTES),
        )
        columns = tuple(self.columns)
        if not columns:
            raise ViewError("columns must not be empty")
        if len(columns) > MAX_TABLE_COLUMNS:
            raise ViewError(f"columns must contain at most {MAX_TABLE_COLUMNS} items")
        if not all(isinstance(column, TableColumn) for column in columns):
            raise ViewError("columns must contain only TableColumn values")
        seen_labels: set[str] = set()
        seen_keys: set[str] = set()
        for column in columns:
            if column.label in seen_labels:
                raise ViewError("column labels must be unique")
            if column.key in seen_keys:
                raise ViewError("column keys must be unique")
            seen_labels.add(column.label)
            seen_keys.add(column.key)
        rows = tuple(_freeze_json_object(row, path="rows[]") for row in self.rows)
        if len(rows) > MAX_TABLE_ROWS:
            raise ViewError(f"rows must contain at most {MAX_TABLE_ROWS} items")
        for row in rows:
            for key in row:
                if key not in seen_keys:
                    raise ViewError(f"row key is not a declared column: {key}")
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "rows", rows)


@dataclass(frozen=True, slots=True)
class Stack:
    """Nested component layout container."""

    direction: StackDirection
    children: tuple[Component, ...]
    accessible_label: str | None = None
    kind: Literal["stack"] = "stack"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "direction",
            cast(
                StackDirection,
                _require_literal(self.direction, path="direction", allowed=_STACK_DIRECTIONS),
            ),
        )
        if self.accessible_label is not None:
            object.__setattr__(
                self,
                "accessible_label",
                _require_string(
                    self.accessible_label,
                    path="accessible_label",
                    non_blank=True,
                    max_chars=128,
                    max_bytes=MAX_TEXT_BYTES,
                ),
            )
        children = tuple(self.children)
        if not children:
            raise ViewError("children must not be empty")
        for child in children:
            if not _is_component_instance(child):
                raise ViewError("children must contain only component values")
        object.__setattr__(self, "children", children)


type Component = Text | Button | Metric | Progress | Field | Table | Stack


@dataclass(frozen=True, slots=True)
class StandardView:
    """Portable declarative view contract."""

    id: str
    title: str
    placement: Placement
    components: tuple[Component, ...]
    kind: StandardViewKind = "card"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "kind",
            cast(
                StandardViewKind,
                _require_literal(self.kind, path="kind", allowed=_VIEW_KINDS),
            ),
        )
        object.__setattr__(self, "id", _require_slug(self.id, path="id"))
        object.__setattr__(
            self,
            "title",
            _require_string(
                self.title,
                path="title",
                non_blank=True,
                max_chars=128,
                max_bytes=MAX_TEXT_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "placement",
            cast(
                Placement,
                _require_literal(self.placement, path="placement", allowed=_PLACEMENTS),
            ),
        )
        components = tuple(self.components)
        for component in components:
            if not _is_component_instance(component):
                raise ViewError("components must contain only component values")
        object.__setattr__(self, "components", components)


def parse_view(value: object) -> StandardView:
    """Parse one raw JSON-like view payload into immutable typed dataclasses."""

    view = value if isinstance(value, StandardView) else _parse_standard_view(value, path="view")
    _validate_view_tree(view)
    payload = _serialize_view(view)
    _validate_json_size(payload, path="view", limit=MAX_CANONICAL_VIEW_BYTES)
    return view


def view_to_json(view: StandardView) -> JSONObject:
    """Return one deterministic JSON-safe representation of a typed view."""

    if not isinstance(view, StandardView):
        raise ViewError("view must be a StandardView")
    _validate_view_tree(view)
    payload = _serialize_view(view)
    _validate_json_size(payload, path="view", limit=MAX_CANONICAL_VIEW_BYTES)
    return payload


def _parse_standard_view(value: object, *, path: str) -> StandardView:
    data = _require_object(value, path=path)
    _reject_unknown_fields(
        data,
        path=path,
        allowed={"kind", "id", "title", "placement", "components"},
    )
    kind = cast(
        StandardViewKind,
        _require_literal(
            _require_present(data, "kind", path=path),
            path=f"{path}.kind",
            allowed=_VIEW_KINDS,
        ),
    )
    components_value = _require_present(data, "components", path=path)
    components = tuple(
        _parse_component(item, path=f"{path}.components[{index}]")
        for index, item in enumerate(_require_array(components_value, path=f"{path}.components"))
    )
    return StandardView(
        kind=kind,
        id=_require_slug(_require_present(data, "id", path=path), path=f"{path}.id"),
        title=_require_string(
            _require_present(data, "title", path=path),
            path=f"{path}.title",
            non_blank=True,
            max_chars=128,
            max_bytes=MAX_TEXT_BYTES,
        ),
        placement=cast(
            Placement,
            _require_literal(
                _require_present(data, "placement", path=path),
                path=f"{path}.placement",
                allowed=_PLACEMENTS,
            ),
        ),
        components=components,
    )


def _parse_component(value: object, *, path: str) -> Component:
    if _is_component_instance(value):
        return cast(Component, value)
    data = _require_object(value, path=path)
    kind = _require_present(data, "kind", path=path)
    if not isinstance(kind, str):
        raise ViewError(f"{path}.kind must be a string")
    if kind == "text":
        _reject_unknown_fields(data, path=path, allowed={"kind", "text", "style", "live"})
        return Text(
            text=_require_string(
                _require_present(data, "text", path=path),
                path=f"{path}.text",
                max_bytes=MAX_TEXT_BYTES,
            ),
            style=cast(
                TextStyle,
                _require_literal(
                    data.get("style", "normal"),
                    path=f"{path}.style",
                    allowed=_TEXT_STYLES,
                ),
            ),
            live=_require_bool(data.get("live", False), path=f"{path}.live"),
        )
    if kind == "button":
        _reject_unknown_fields(
            data,
            path=path,
            allowed={
                "kind",
                "label",
                "action_id",
                "accessible_label",
                "payload",
                "variant",
                "icon_only",
            },
        )
        icon_only = _require_bool(data.get("icon_only", False), path=f"{path}.icon_only")
        accessible_label_value = data.get("accessible_label")
        if accessible_label_value is None:
            accessible_label: str | None = None
            if icon_only:
                raise ViewError(f"{path}.accessible_label is required when icon_only is true")
        else:
            accessible_label = _require_string(
                accessible_label_value,
                path=f"{path}.accessible_label",
                non_blank=True,
                max_chars=128,
                max_bytes=MAX_TEXT_BYTES,
            )
        payload_value = data.get("payload", {})
        payload = _freeze_json_object(payload_value, path=f"{path}.payload")
        _validate_json_size(payload, path=f"{path}.payload", limit=MAX_ACTION_PAYLOAD_BYTES)
        return Button(
            label=_require_string(
                _require_present(data, "label", path=path),
                path=f"{path}.label",
                non_blank=True,
                max_bytes=MAX_TEXT_BYTES,
            ),
            action_id=_require_slug(
                _require_present(data, "action_id", path=path),
                path=f"{path}.action_id",
            ),
            accessible_label=accessible_label,
            payload=payload,
            variant=cast(
                ButtonVariant,
                _require_literal(
                    data.get("variant", "default"),
                    path=f"{path}.variant",
                    allowed=_BUTTON_VARIANTS,
                ),
            ),
            icon_only=icon_only,
        )
    if kind == "metric":
        _reject_unknown_fields(data, path=path, allowed={"kind", "label", "value", "unit"})
        return Metric(
            label=_require_string(
                _require_present(data, "label", path=path),
                path=f"{path}.label",
                non_blank=True,
                max_bytes=MAX_TEXT_BYTES,
            ),
            value=_require_metric_value(
                _require_present(data, "value", path=path),
                path=f"{path}.value",
            ),
            unit=(
                None
                if "unit" not in data or data["unit"] is None
                else _require_string(
                    data["unit"],
                    path=f"{path}.unit",
                    non_blank=True,
                    max_bytes=MAX_TEXT_BYTES,
                )
            ),
        )
    if kind == "progress":
        _reject_unknown_fields(data, path=path, allowed={"kind", "label", "value", "max"})
        max_value = _require_number(_require_present(data, "max", path=path), path=f"{path}.max")
        if max_value <= 0:
            raise ViewError(f"{path}.max must be greater than 0")
        progress_value = _require_number(
            _require_present(data, "value", path=path),
            path=f"{path}.value",
        )
        if progress_value < 0 or progress_value > max_value:
            raise ViewError(f"{path}.value must be between 0 and max")
        return Progress(
            label=_require_string(
                _require_present(data, "label", path=path),
                path=f"{path}.label",
                non_blank=True,
                max_bytes=MAX_TEXT_BYTES,
            ),
            value=progress_value,
            max=max_value,
        )
    if kind == "field":
        _reject_unknown_fields(
            data,
            path=path,
            allowed={"kind", "name", "label", "input_type", "required", "value", "options"},
        )
        input_type = cast(
            FieldInputType,
            _require_literal(
                _require_present(data, "input_type", path=path),
                path=f"{path}.input_type",
                allowed=_FIELD_INPUT_TYPES,
            ),
        )
        options_value = data.get("options")
        if input_type == "select":
            if options_value is None:
                raise ViewError(f"{path}.options is required when input_type is select")
            options = tuple(
                _parse_field_option(item, path=f"{path}.options[{index}]")
                for index, item in enumerate(_require_array(options_value, path=f"{path}.options"))
            )
            if not options:
                raise ViewError(f"{path}.options must not be empty")
        else:
            if options_value is not None:
                raise ViewError(f"{path}.options is only allowed when input_type is select")
            options = ()
        field_value = (
            None
            if "value" not in data or data["value"] is None
            else _require_string(data["value"], path=f"{path}.value", max_bytes=MAX_TEXT_BYTES)
        )
        if (
            input_type == "select"
            and field_value is not None
            and field_value not in {item.value for item in options}
        ):
            raise ViewError(f"{path}.value must match a declared option")
        return Field(
            name=_require_slug(_require_present(data, "name", path=path), path=f"{path}.name"),
            label=_require_string(
                _require_present(data, "label", path=path),
                path=f"{path}.label",
                non_blank=True,
                max_bytes=MAX_TEXT_BYTES,
            ),
            input_type=input_type,
            required=_require_bool(data.get("required", False), path=f"{path}.required"),
            value=field_value,
            options=options,
        )
    if kind == "table":
        _reject_unknown_fields(data, path=path, allowed={"kind", "label", "columns", "rows"})
        columns = tuple(
            _parse_table_column(item, path=f"{path}.columns[{index}]")
            for index, item in enumerate(
                _require_array(_require_present(data, "columns", path=path), path=f"{path}.columns")
            )
        )
        if not columns:
            raise ViewError(f"{path}.columns must not be empty")
        if len(columns) > MAX_TABLE_COLUMNS:
            raise ViewError(f"{path}.columns must contain at most {MAX_TABLE_COLUMNS} items")
        seen_labels: set[str] = set()
        seen_keys: set[str] = set()
        for index, column in enumerate(columns):
            if column.label in seen_labels:
                raise ViewError(f"{path}.columns[{index}].label must be unique")
            if column.key in seen_keys:
                raise ViewError(f"{path}.columns[{index}].key must be unique")
            seen_labels.add(column.label)
            seen_keys.add(column.key)
        rows_raw = _require_array(data.get("rows", []), path=f"{path}.rows")
        if len(rows_raw) > MAX_TABLE_ROWS:
            raise ViewError(f"{path}.rows must contain at most {MAX_TABLE_ROWS} items")
        rows: list[FrozenJSONObject] = []
        for row_index, row_value in enumerate(rows_raw):
            row = _freeze_json_object(row_value, path=f"{path}.rows[{row_index}]")
            for key in row:
                if key not in seen_keys:
                    raise ViewError(f"{path}.rows[{row_index}].{key} is not a declared column")
            rows.append(row)
        return Table(
            label=_require_string(
                _require_present(data, "label", path=path),
                path=f"{path}.label",
                non_blank=True,
                max_bytes=MAX_TEXT_BYTES,
            ),
            columns=columns,
            rows=tuple(rows),
        )
    if kind == "stack":
        _reject_unknown_fields(
            data,
            path=path,
            allowed={"kind", "direction", "accessible_label", "children"},
        )
        children = tuple(
            _parse_component(item, path=f"{path}.children[{index}]")
            for index, item in enumerate(
                _require_array(
                    _require_present(data, "children", path=path),
                    path=f"{path}.children",
                )
            )
        )
        if not children:
            raise ViewError(f"{path}.children must not be empty")
        return Stack(
            direction=cast(
                StackDirection,
                _require_literal(
                    _require_present(data, "direction", path=path),
                    path=f"{path}.direction",
                    allowed=_STACK_DIRECTIONS,
                ),
            ),
            accessible_label=(
                None
                if "accessible_label" not in data or data["accessible_label"] is None
                else _require_string(
                    data["accessible_label"],
                    path=f"{path}.accessible_label",
                    non_blank=True,
                    max_chars=128,
                    max_bytes=MAX_TEXT_BYTES,
                )
            ),
            children=children,
        )
    allowed = ", ".join(_COMPONENT_KINDS)
    raise ViewError(f"{path}.kind must be one of: {allowed}")


def _parse_field_option(value: object, *, path: str) -> FieldOption:
    data = _require_object(value, path=path)
    _reject_unknown_fields(data, path=path, allowed={"label", "value"})
    return FieldOption(
        label=_require_string(
            _require_present(data, "label", path=path),
            path=f"{path}.label",
            non_blank=True,
            max_bytes=MAX_TEXT_BYTES,
        ),
        value=_require_string(
            _require_present(data, "value", path=path),
            path=f"{path}.value",
            non_blank=True,
            max_bytes=MAX_TEXT_BYTES,
        ),
    )


def _parse_table_column(value: object, *, path: str) -> TableColumn:
    data = _require_object(value, path=path)
    _reject_unknown_fields(data, path=path, allowed={"label", "key"})
    return TableColumn(
        label=_require_string(
            _require_present(data, "label", path=path),
            path=f"{path}.label",
            non_blank=True,
            max_bytes=MAX_TEXT_BYTES,
        ),
        key=_require_slug(_require_present(data, "key", path=path), path=f"{path}.key"),
    )


def _validate_view_tree(view: StandardView) -> None:
    nodes = 0

    def walk(component: Component, *, path: str, depth: int) -> None:
        nonlocal nodes
        if depth > MAX_VIEW_DEPTH:
            raise ViewError(f"{path} exceeds maximum depth {MAX_VIEW_DEPTH}")
        nodes += 1
        if nodes > MAX_VIEW_NODES:
            raise ViewError(f"{path} exceeds maximum node count {MAX_VIEW_NODES}")
        if isinstance(component, Button):
            _validate_json_size(
                component.payload,
                path=f"{path}.payload",
                limit=MAX_ACTION_PAYLOAD_BYTES,
            )
        if isinstance(component, Stack):
            for index, child in enumerate(component.children):
                walk(child, path=f"{path}.children[{index}]", depth=depth + 1)

    for index, component in enumerate(view.components):
        walk(component, path=f"view.components[{index}]", depth=1)


def _serialize_view(view: StandardView) -> JSONObject:
    return {
        "kind": view.kind,
        "id": view.id,
        "title": view.title,
        "placement": view.placement,
        "components": [_serialize_component(component) for component in view.components],
    }


def _serialize_component(component: Component) -> JSONObject:
    if isinstance(component, Text):
        return {
            "kind": component.kind,
            "text": component.text,
            "style": component.style,
            "live": component.live,
        }
    if isinstance(component, Button):
        payload: JSONObject = {
            "kind": component.kind,
            "label": component.label,
            "action_id": component.action_id,
            "accessible_label": component.accessible_label,
            "payload": _plain_json_object(component.payload),
            "variant": component.variant,
            "icon_only": component.icon_only,
        }
        return _without_none(payload)
    if isinstance(component, Metric):
        payload = {
            "kind": component.kind,
            "label": component.label,
            "value": cast(JSONValue, _plain_metric_value(component.value)),
            "unit": component.unit,
        }
        return _without_none(payload)
    if isinstance(component, Progress):
        return {
            "kind": component.kind,
            "label": component.label,
            "value": cast(JSONValue, component.value),
            "max": cast(JSONValue, component.max),
        }
    if isinstance(component, Field):
        payload = {
            "kind": component.kind,
            "name": component.name,
            "label": component.label,
            "input_type": component.input_type,
            "required": component.required,
            "value": component.value,
            "options": [
                {"label": option.label, "value": option.value} for option in component.options
            ],
        }
        if component.input_type != "select":
            payload.pop("options")
        return _without_none(payload)
    if isinstance(component, Table):
        columns: list[JSONObject] = [
            {"label": column.label, "key": column.key} for column in component.columns
        ]
        rows: list[JSONObject] = []
        for row in component.rows:
            row_payload: JSONObject = {}
            for column in component.columns:
                if column.key in row:
                    row_payload[column.key] = _plain_json_value(row[column.key])
            rows.append(row_payload)
        return {
            "kind": component.kind,
            "label": component.label,
            "columns": cast(JSONValue, columns),
            "rows": cast(JSONValue, rows),
        }
    return (
        {
            "kind": component.kind,
            "direction": component.direction,
            "accessible_label": component.accessible_label,
            "children": [_serialize_component(child) for child in component.children],
        }
        if isinstance(component, Stack)
        else _unreachable_component(component)
    )


def _plain_metric_value(value: str | int | float) -> JSONPrimitive:
    if isinstance(value, str):
        return value
    return cast(JSONPrimitive, value)


def _unreachable_component(component: Component) -> JSONObject:
    raise AssertionError(f"Unsupported component: {component!r}")


def _without_none(value: JSONObject) -> JSONObject:
    return {key: item for key, item in value.items() if item is not None}


def _require_present(data: Mapping[str, object], key: str, *, path: str) -> object:
    if key not in data:
        raise ViewError(f"{path}.{key} is required")
    return data[key]


def _require_object(value: object, *, path: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise ViewError(f"{path} must be a JSON object")


def _require_array(value: object, *, path: str) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, Mapping)):
        return tuple(value)
    raise ViewError(f"{path} must be a JSON array")


def _reject_unknown_fields(
    data: Mapping[str, object],
    *,
    path: str,
    allowed: set[str],
) -> None:
    unknown = sorted(key for key in data if key not in allowed)
    if unknown:
        raise ViewError(f"{path} contains unknown field: {unknown[0]}")


def _require_literal(value: object, *, path: str, allowed: tuple[str, ...]) -> str:
    if not isinstance(value, str):
        raise ViewError(f"{path} must be one of: {', '.join(allowed)}")
    if value not in allowed:
        raise ViewError(f"{path} must be one of: {', '.join(allowed)}")
    return value


def _require_bool(value: object, *, path: str) -> bool:
    if not isinstance(value, bool):
        raise ViewError(f"{path} must be a boolean")
    return value


def _require_string(
    value: object,
    *,
    path: str,
    non_blank: bool = False,
    max_chars: int | None = None,
    max_bytes: int | None = None,
) -> str:
    if not isinstance(value, str):
        raise ViewError(f"{path} must be a string")
    if non_blank and not value.strip():
        if max_chars is not None:
            raise ViewError(f"{path} must be non-blank and at most {max_chars} characters")
        raise ViewError(f"{path} must be non-blank")
    if max_chars is not None and len(value) > max_chars:
        if non_blank:
            raise ViewError(f"{path} must be non-blank and at most {max_chars} characters")
        raise ViewError(f"{path} must be at most {max_chars} characters")
    if max_bytes is not None and len(value.encode("utf-8")) > max_bytes:
        raise ViewError(f"{path} exceeds {max_bytes} bytes")
    return value


def _require_slug(value: object, *, path: str) -> str:
    if not isinstance(value, str):
        raise ViewError(f"{path} must be a lowercase slug")
    if _SAFE_SLUG_RE.fullmatch(value) is None:
        raise ViewError(f"{path} must be a lowercase slug")
    return value


def _require_number(value: object, *, path: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ViewError(f"{path} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise ViewError(f"{path} must be a finite number")
    return value


def _require_metric_value(value: object, *, path: str) -> str | int | float:
    if isinstance(value, str):
        return _require_string(value, path=path, non_blank=True, max_bytes=MAX_TEXT_BYTES)
    return _require_number(value, path=path)


def _empty_frozen_object() -> FrozenJSONObject:
    return cast(FrozenJSONObject, MappingProxyType({}))


def _freeze_json_object(value: object, *, path: str) -> FrozenJSONObject:
    if not isinstance(value, Mapping):
        raise ViewError(f"{path} must be a JSON object")
    frozen: dict[str, FrozenJSONValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ViewError(f"{path} contains a non-string key")
        frozen[key] = _freeze_json_value(item, path=f"{path}.{key}")
    return cast(FrozenJSONObject, MappingProxyType(frozen))


def _freeze_json_value(value: object, *, path: str) -> FrozenJSONValue:
    if value is None or isinstance(value, (str, bool)):
        return cast(FrozenJSONValue, value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ViewError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        return _freeze_json_object(value, path=path)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, Mapping)):
        return tuple(_freeze_json_value(item, path=f"{path}[]") for item in value)
    raise ViewError(f"{path} contains a non-JSON value")


def _validate_json_size(value: object, *, path: str, limit: int) -> None:
    encoded = json.dumps(
        _plain_json_value(cast(FrozenJSONValue | JSONValue | JSONObject, value)),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > limit:
        raise ViewError(f"{path} JSON exceeds {limit} bytes")


def _plain_json_object(value: Mapping[str, FrozenJSONValue]) -> JSONObject:
    return {key: _plain_json_value(value[key]) for key in sorted(value)}


def _plain_json_value(value: FrozenJSONValue | JSONValue | JSONObject) -> JSONValue:
    if value is None or isinstance(value, (str, bool, int)):
        return cast(JSONValue, value)
    if isinstance(value, float):
        return value
    if isinstance(value, Mapping):
        return {key: _plain_json_value(value[key]) for key in sorted(value)}
    return [_plain_json_value(item) for item in value]


def _is_component_instance(value: object) -> bool:
    return isinstance(value, (Text, Button, Metric, Progress, Field, Table, Stack))


__all__ = [
    "Button",
    "ButtonVariant",
    "Component",
    "Field",
    "FieldInputType",
    "FieldOption",
    "FrozenJSONObject",
    "FrozenJSONValue",
    "MAX_ACTION_PAYLOAD_BYTES",
    "MAX_CANONICAL_VIEW_BYTES",
    "MAX_TABLE_COLUMNS",
    "MAX_TABLE_ROWS",
    "MAX_TEXT_BYTES",
    "MAX_VIEW_DEPTH",
    "MAX_VIEW_NODES",
    "Metric",
    "Placement",
    "Progress",
    "Stack",
    "StackDirection",
    "StandardView",
    "StandardViewKind",
    "Table",
    "TableColumn",
    "Text",
    "TextStyle",
    "ViewError",
    "parse_view",
    "view_to_json",
]
