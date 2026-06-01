from __future__ import annotations

from dataclasses import dataclass

MODE_INDICATORS = {
    "normal": "", "insert": "-- INSERT --", "visual": "-- VISUAL --",
    "visual-line": "-- VISUAL LINE --", "visual-block": "-- VISUAL BLOCK --",
    "replace": "-- REPLACE --", "command": ":",
}


@dataclass
class TerminalFrame:
    lines: list[str]
    cursor_row: int
    cursor_col: int
    status: str
    mode: str


def render_vim(
    buffer: list[str],
    cursor: tuple[int, int],
    mode: str,
    rows: int = 24,
    cols: int = 80,
) -> TerminalFrame:
    content_rows = rows - 2
    cursor_line = cursor[0] - 1

    if len(buffer) <= content_rows:
        start = 0
    else:
        start = max(0, min(cursor_line - content_rows // 2, len(buffer) - content_rows))

    lines = []
    for i in range(content_rows):
        idx = start + i
        lines.append(buffer[idx][:cols] if idx < len(buffer) else "~")

    return TerminalFrame(
        lines=lines,
        cursor_row=cursor_line - start,
        cursor_col=cursor[1] - 1,
        status=f"[No Name]{' ' * (cols - 20)}{cursor[0]},{cursor[1]}",
        mode=MODE_INDICATORS.get(mode, f"-- {mode.upper()} --"),
    )


def render_to_string(frame: TerminalFrame, show_cursor: bool = True) -> str:
    output = []
    for i, line in enumerate(frame.lines):
        if show_cursor and i == frame.cursor_row:
            col = min(frame.cursor_col, len(line))
            line = line[:col] + "█" + line[col + 1:] if col < len(line) else line + "█"
        output.append(line)
    output.extend([frame.status, frame.mode])
    return "\n".join(output)


def raw_observation(
    buffer: list[str],
    cursor: tuple[int, int],
    mode: str,
    context: str | None = None,
) -> str:
    frame = render_vim(buffer, cursor, mode)
    output = render_to_string(frame)
    return f"[Context: {context}]\n\n{output}" if context else output
