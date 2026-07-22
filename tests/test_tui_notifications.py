from io import StringIO

from tau_coding.tui.terminal_notification import (
    TerminalNotificationController,
    desktop_notification_sequence,
    terminal_notification_supported,
)


def test_desktop_notification_sequence_uses_ghostty_osc9() -> None:
    assert desktop_notification_sequence(
        "Done",
        environ={"TERM_PROGRAM": "ghostty"},
    ) == "\x1b]9;Done\x07"


def test_desktop_notification_sequence_uses_kitty_osc99() -> None:
    assert desktop_notification_sequence(
        "Done",
        environ={"TERM": "xterm-kitty"},
    ) == "\x1b]99;;Done\x1b\\"


def test_terminal_notification_controller_writes_bell() -> None:
    out = StringIO()
    controller = TerminalNotificationController("bell", enabled=True, writer=out.write)

    controller.notify_turn_finished()
    assert out.getvalue() == "\a"


def test_terminal_notification_disabled_in_ci() -> None:
    assert terminal_notification_supported(environ={"CI": "1"}) is False
