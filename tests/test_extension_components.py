import re
from collections.abc import Callable

import pytest

from tau_extensions.web import (
    MAX_ACTION_PAYLOAD_BYTES,
    MAX_CANONICAL_VIEW_BYTES,
    MAX_TABLE_COLUMNS,
    MAX_TABLE_ROWS,
    MAX_TEXT_BYTES,
    MAX_VIEW_DEPTH,
    MAX_VIEW_NODES,
    Button,
    Field,
    FieldOption,
    Metric,
    Progress,
    Stack,
    StandardView,
    Table,
    TableColumn,
    Text,
    ViewError,
    parse_view,
    view_to_json,
)


def _expect_view_error(factory: Callable[[], object], message: str) -> None:
    with pytest.raises(ViewError, match=rf"^{re.escape(message)}$"):
        factory()


def _base_view_payload(
    *,
    components: object | None = None,
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": "card",
        "id": "demo-view",
        "title": "Demo View",
        "placement": "sidebar",
        "components": components if components is not None else [{"kind": "text", "text": "ok"}],
    }
    payload.update(overrides)
    return payload


def _all_component_view_payload() -> dict[str, object]:
    return {
        "kind": "detail",
        "id": "extension-demo",
        "title": "Extension Demo",
        "placement": "dashboard",
        "components": [
            {"kind": "text", "text": "Status", "style": "muted", "live": True},
            {
                "kind": "button",
                "label": "Refresh",
                "action_id": "refresh-status",
                "accessible_label": "Refresh status",
                "payload": {"z": {"b": 2, "a": [1, None, True]}, "a": 1},
                "variant": "primary",
                "icon_only": True,
            },
            {"kind": "metric", "label": "Latency", "value": 42.5, "unit": "ms"},
            {"kind": "progress", "label": "Completed", "value": 3, "max": 5},
            {
                "kind": "field",
                "name": "environment",
                "label": "Environment",
                "input_type": "select",
                "required": True,
                "value": "prod",
                "options": [
                    {"label": "Production", "value": "prod"},
                    {"label": "Staging", "value": "staging"},
                ],
            },
            {
                "kind": "table",
                "label": "Services",
                "columns": [
                    {"label": "Name", "key": "name"},
                    {"label": "Status", "key": "status"},
                ],
                "rows": [
                    {"status": "ok", "name": "alpha"},
                    {"name": "beta"},
                ],
            },
            {
                "kind": "stack",
                "direction": "row",
                "accessible_label": "Nested summary",
                "children": [{"kind": "text", "text": "Nested", "style": "code", "live": False}],
            },
        ],
    }


def _all_component_view() -> StandardView:
    return StandardView(
        kind="detail",
        id="extension-demo",
        title="Extension Demo",
        placement="dashboard",
        components=(
            Text(text="Status", style="muted", live=True),
            Button(
                label="Refresh",
                action_id="refresh-status",
                accessible_label="Refresh status",
                payload={"z": {"b": 2, "a": (1, None, True)}, "a": 1},
                variant="primary",
                icon_only=True,
            ),
            Metric(label="Latency", value=42.5, unit="ms"),
            Progress(label="Completed", value=3, max=5),
            Field(
                name="environment",
                label="Environment",
                input_type="select",
                required=True,
                value="prod",
                options=(
                    FieldOption(label="Production", value="prod"),
                    FieldOption(label="Staging", value="staging"),
                ),
            ),
            Table(
                label="Services",
                columns=(
                    TableColumn(label="Name", key="name"),
                    TableColumn(label="Status", key="status"),
                ),
                rows=(
                    {"status": "ok", "name": "alpha"},
                    {"name": "beta"},
                ),
            ),
            Stack(
                direction="row",
                accessible_label="Nested summary",
                children=(Text(text="Nested", style="code", live=False),),
            ),
        ),
    )


def _stack_chain(depth: int) -> dict[str, object]:
    node: dict[str, object] = {"kind": "text", "text": "leaf"}
    for _index in range(depth):
        node = {"kind": "stack", "direction": "column", "children": [node]}
    return node


def test_text_constructor_builds_text_component() -> None:
    text = Text(text="Ready", style="code", live=True)

    assert text.kind == "text"
    assert text.text == "Ready"
    assert text.style == "code"
    assert text.live is True


def test_button_constructor_freezes_payload_and_validates_accessibility() -> None:
    button = Button(
        label="Refresh",
        action_id="refresh-status",
        accessible_label="Refresh status",
        payload={"b": 2, "a": {"d": False, "c": None}},
        variant="secondary",
        icon_only=True,
    )

    assert button.kind == "button"
    assert dict(button.payload) == {"b": 2, "a": {"d": False, "c": None}}
    assert button.variant == "secondary"
    assert button.icon_only is True

    _expect_view_error(
        lambda: Button(label="Icon", action_id="icon-action", icon_only=True),
        "accessible_label is required when icon_only is true",
    )


def test_metric_and_progress_constructors_validate_values() -> None:
    metric = Metric(label="Latency", value=12.5, unit="ms")
    progress = Progress(label="Completed", value=3, max=5)

    assert metric.kind == "metric"
    assert metric.value == 12.5
    assert metric.unit == "ms"
    assert progress.kind == "progress"
    assert progress.value == 3
    assert progress.max == 5


def test_field_and_option_constructors_build_select_fields() -> None:
    option = FieldOption(label="Production", value="prod")
    field = Field(
        name="environment",
        label="Environment",
        input_type="select",
        required=True,
        value="prod",
        options=(option, FieldOption(label="Staging", value="staging")),
    )

    assert option.label == "Production"
    assert option.value == "prod"
    assert field.kind == "field"
    assert field.required is True
    assert field.value == "prod"
    assert field.options == (
        FieldOption(label="Production", value="prod"),
        FieldOption(label="Staging", value="staging"),
    )


def test_table_and_column_constructors_build_portable_tables() -> None:
    column = TableColumn(label="Name", key="name")
    table = Table(
        label="Services",
        columns=(column, TableColumn(label="Status", key="status")),
        rows=({"status": "ok", "name": "alpha"}, {"name": "beta"}),
    )

    assert column.label == "Name"
    assert column.key == "name"
    assert table.kind == "table"
    assert table.columns == (
        TableColumn(label="Name", key="name"),
        TableColumn(label="Status", key="status"),
    )
    assert tuple(dict(row) for row in table.rows) == (
        {"status": "ok", "name": "alpha"},
        {"name": "beta"},
    )


def test_stack_and_standard_view_constructors_build_nested_views() -> None:
    stack = Stack(direction="column", accessible_label="Status summary", children=(Text("ok"),))
    view = StandardView(
        id="status-view",
        title="Status View",
        placement="compose_above",
        components=(stack,),
    )

    assert stack.kind == "stack"
    assert stack.direction == "column"
    assert stack.children == (Text("ok"),)
    assert view.kind == "card"
    assert view.id == "status-view"
    assert view.components == (stack,)


def test_parse_view_and_view_to_json_roundtrip_all_component_types() -> None:
    parsed = parse_view(_all_component_view_payload())
    expected = _all_component_view()

    assert parsed == expected
    assert view_to_json(parsed) == {
        "kind": "detail",
        "id": "extension-demo",
        "title": "Extension Demo",
        "placement": "dashboard",
        "components": [
            {"kind": "text", "text": "Status", "style": "muted", "live": True},
            {
                "kind": "button",
                "label": "Refresh",
                "action_id": "refresh-status",
                "accessible_label": "Refresh status",
                "payload": {"a": 1, "z": {"a": [1, None, True], "b": 2}},
                "variant": "primary",
                "icon_only": True,
            },
            {"kind": "metric", "label": "Latency", "value": 42.5, "unit": "ms"},
            {"kind": "progress", "label": "Completed", "value": 3, "max": 5},
            {
                "kind": "field",
                "name": "environment",
                "label": "Environment",
                "input_type": "select",
                "required": True,
                "value": "prod",
                "options": [
                    {"label": "Production", "value": "prod"},
                    {"label": "Staging", "value": "staging"},
                ],
            },
            {
                "kind": "table",
                "label": "Services",
                "columns": [
                    {"label": "Name", "key": "name"},
                    {"label": "Status", "key": "status"},
                ],
                "rows": [
                    {"name": "alpha", "status": "ok"},
                    {"name": "beta"},
                ],
            },
            {
                "kind": "stack",
                "direction": "row",
                "accessible_label": "Nested summary",
                "children": [{"kind": "text", "text": "Nested", "style": "code", "live": False}],
            },
        ],
    }
    assert parse_view(view_to_json(expected)) == expected


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (_base_view_payload(unexpected=True), "view contains unknown field: unexpected"),
        (_base_view_payload(kind="panel"), "view.kind must be one of: card, detail, form"),
        (
            _base_view_payload(placement="footer"),
            (
                "view.placement must be one of: compose_above, compose_below, sidebar, "
                "timeline_before, timeline_after, dashboard"
            ),
        ),
        (_base_view_payload(components={"kind": "text"}), "view.components must be a JSON array"),
        (
            _base_view_payload(components=[{"kind": 3, "text": "ok"}]),
            "view.components[0].kind must be a string",
        ),
        (
            _base_view_payload(components=[{"kind": "unknown"}]),
            (
                "view.components[0].kind must be one of: button, field, metric, "
                "progress, stack, table, text"
            ),
        ),
        (
            _base_view_payload(components=[{"kind": "text", "text": "ok", "extra": True}]),
            "view.components[0] contains unknown field: extra",
        ),
        (
            _base_view_payload(components=[{"kind": "text", "text": 1}]),
            "view.components[0].text must be a string",
        ),
        (
            _base_view_payload(
                components=[
                    {
                        "kind": "field",
                        "name": "environment",
                        "label": "Environment",
                        "input_type": "dropdown",
                    }
                ]
            ),
            "view.components[0].input_type must be one of: text, textarea, select",
        ),
    ],
)
def test_parse_view_rejects_unknown_fields_kinds_and_types(
    payload: dict[str, object],
    message: str,
) -> None:
    _expect_view_error(lambda: parse_view(payload), message)


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (
            {"kind": "button", "label": "Icon", "action_id": "icon-action", "icon_only": True},
            "view.components[0].accessible_label is required when icon_only is true",
        ),
        (
            {
                "kind": "stack",
                "direction": "row",
                "accessible_label": "   ",
                "children": [{"kind": "text", "text": "ok"}],
            },
            "view.components[0].accessible_label must be non-blank and at most 128 characters",
        ),
        (
            {
                "kind": "field",
                "name": "environment",
                "label": "Environment",
                "input_type": "select",
            },
            "view.components[0].options is required when input_type is select",
        ),
        (
            {
                "kind": "field",
                "name": "environment",
                "label": "Environment",
                "input_type": "select",
                "options": [],
            },
            "view.components[0].options must not be empty",
        ),
        (
            {
                "kind": "field",
                "name": "notes",
                "label": "Notes",
                "input_type": "text",
                "options": [{"label": "Ignored", "value": "ignored"}],
            },
            "view.components[0].options is only allowed when input_type is select",
        ),
        (
            {
                "kind": "field",
                "name": "environment",
                "label": "Environment",
                "input_type": "select",
                "value": "qa",
                "options": [{"label": "Production", "value": "prod"}],
            },
            "view.components[0].value must match a declared option",
        ),
    ],
)
def test_parse_view_rejects_accessibility_and_select_errors(
    component: dict[str, object],
    message: str,
) -> None:
    _expect_view_error(lambda: parse_view(_base_view_payload(components=[component])), message)


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (
            {"kind": "progress", "label": "Completed", "value": 1, "max": 0},
            "view.components[0].max must be greater than 0",
        ),
        (
            {"kind": "progress", "label": "Completed", "value": -1, "max": 5},
            "view.components[0].value must be between 0 and max",
        ),
        (
            {"kind": "progress", "label": "Completed", "value": 6, "max": 5},
            "view.components[0].value must be between 0 and max",
        ),
    ],
)
def test_parse_view_rejects_progress_bounds(component: dict[str, object], message: str) -> None:
    _expect_view_error(lambda: parse_view(_base_view_payload(components=[component])), message)


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (
            {"kind": "table", "label": "Services", "columns": []},
            "view.components[0].columns must not be empty",
        ),
        (
            {
                "kind": "table",
                "label": "Services",
                "columns": [
                    {"label": "Name", "key": "name"},
                    {"label": "Name", "key": "status"},
                ],
            },
            "view.components[0].columns[1].label must be unique",
        ),
        (
            {
                "kind": "table",
                "label": "Services",
                "columns": [
                    {"label": "Name", "key": "name"},
                    {"label": "Status", "key": "name"},
                ],
            },
            "view.components[0].columns[1].key must be unique",
        ),
        (
            {
                "kind": "table",
                "label": "Services",
                "columns": [
                    {"label": f"Column {index}", "key": f"column-{index}"}
                    for index in range(MAX_TABLE_COLUMNS + 1)
                ],
            },
            f"view.components[0].columns must contain at most {MAX_TABLE_COLUMNS} items",
        ),
        (
            {
                "kind": "table",
                "label": "Services",
                "columns": [{"label": "Name", "key": "name"}],
                "rows": [{"name": str(index)} for index in range(MAX_TABLE_ROWS + 1)],
            },
            f"view.components[0].rows must contain at most {MAX_TABLE_ROWS} items",
        ),
        (
            {
                "kind": "table",
                "label": "Services",
                "columns": [{"label": "Name", "key": "name"}],
                "rows": [{"status": "ok"}],
            },
            "view.components[0].rows[0].status is not a declared column",
        ),
    ],
)
def test_parse_view_rejects_invalid_tables(component: dict[str, object], message: str) -> None:
    _expect_view_error(lambda: parse_view(_base_view_payload(components=[component])), message)


def test_parse_view_rejects_oversized_button_payloads() -> None:
    payload = _base_view_payload(
        components=[
            {
                "kind": "button",
                "label": "Run",
                "action_id": "run-action",
                "payload": {"blob": "x" * MAX_ACTION_PAYLOAD_BYTES},
            }
        ]
    )

    _expect_view_error(
        lambda: parse_view(payload),
        f"view.components[0].payload JSON exceeds {MAX_ACTION_PAYLOAD_BYTES} bytes",
    )


def test_view_to_json_rejects_oversized_canonical_views() -> None:
    view = StandardView(
        id="oversized-view",
        title="Oversized View",
        placement="timeline_after",
        components=tuple(Text("x" * MAX_TEXT_BYTES) for _index in range(5)),
    )

    _expect_view_error(
        lambda: view_to_json(view),
        f"view JSON exceeds {MAX_CANONICAL_VIEW_BYTES} bytes",
    )


def test_parse_view_rejects_excessive_depth() -> None:
    payload = _base_view_payload(components=[_stack_chain(MAX_VIEW_DEPTH)])
    path = "view.components[0]" + ".children[0]" * MAX_VIEW_DEPTH

    _expect_view_error(
        lambda: parse_view(payload),
        f"{path} exceeds maximum depth {MAX_VIEW_DEPTH}",
    )


def test_parse_view_rejects_excessive_node_count() -> None:
    payload = _base_view_payload(
        components=[{"kind": "text", "text": str(index)} for index in range(MAX_VIEW_NODES + 1)]
    )

    _expect_view_error(
        lambda: parse_view(payload),
        f"view.components[{MAX_VIEW_NODES}] exceeds maximum node count {MAX_VIEW_NODES}",
    )
