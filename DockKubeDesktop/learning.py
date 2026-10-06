"""Learning Centre: a popup study guide with real, readable tables.

The popup opens in its own window so the main DocKube layout keeps all of
its vertical space for commands and terminal output.

Content is authored as a small HTML subset (see ``learning_content``). The
parser below turns that into styled text blocks plus genuine table widgets,
because ``tk.Text`` cannot draw bordered tables and a naive tag stripper
reduces every table to unreadable ``|---|---|`` pipes.

Only the standard library plus customtkinter is used, matching the rest of
the project.
"""

import html
import re
import sys
import textwrap
import tkinter
import tkinter as tk
import tkinter.font
from html.parser import HTMLParser

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

# Colours reused from the DocKube dark palette.
BG = "#161b22"
FG = "#d4d4d4"
MUTED = "#8b949e"
BORDER = "#30363d"
HEADER_BG = "#1f6feb"
STRIPE = "#1b2028"
ACCENT = "#58a6ff"
GREEN = "#7ee787"
ORANGE = "#ffa657"
YELLOW = "#d29922"

TABLE_HEADING_BG = "#21262d"
TABLE_STRIPE = "#1a1f27"
TABLE_BG = "#161b22"

# Fixed width for the chapter sidebar. Setting this as a column minsize is
# what gives the scrollable TOC a real width to draw its scrollbar in.
SIDEBAR_WIDTH = 250


class Block:
    """One renderable piece of a chapter."""

    def __init__(self, kind, text="", rows=None, level=1):
        self.kind = kind      # title, h2, h3, h4, p, bullet, code, table, rule
        self.text = text
        self.rows = rows or []
        self.level = level


def _split_row(line):
    """Split a markdown table row on pipes, dropping the outer delimiters."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_separator(cells):
    """True for the ``|---|---|`` divider row that follows a header."""
    return bool(cells) and all(
        cell and set(cell) <= set("-: ") and "-" in cell for cell in cells)


def _inline(text):
    """Convert light inline markup into plain readable text.

    Backticks and bold markers are removed but the words survive, so a
    command like ``kubectl get pods`` stays readable inside a table cell.
    """
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "")
    return html.unescape(text).strip()


_TABLE_RE = re.compile(r"(?:^\|.*\|[ \t]*$\n?)+", re.MULTILINE)


def _markdown_tables_to_html(source):
    """Rewrite ``| a | b |`` markdown tables into real ``<table>`` markup.

    This is what turns the old unreadable pipes into proper grids.
    """
    def convert(match):
        lines = [line for line in match.group(0).splitlines() if line.strip()]
        if len(lines) < 2:
            return match.group(0)
        rows = [row for row in (_split_row(line) for line in lines)
                if not _is_separator(row)]
        if not rows:
            return match.group(0)
        out = ["<table>", "<tr>" +
               "".join(f"<th>{cell}</th>" for cell in rows[0]) + "</tr>"]
        for row in rows[1:]:
            out.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
        out.append("</table>")
        return "\n".join(out) + "\n"

    return _TABLE_RE.sub(convert, source)


class ContentParser(HTMLParser):
    """Turn authored HTML into a flat list of :class:`Block` objects.

    Anything unrecognised degrades to plain text rather than disappearing,
    which is exactly what the old regex tag-stripper failed to do.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.buffer = []
        self.list_stack = []
        self.in_code = False
        self.code_lines = []
        self.table_rows = []
        self.table_row = []
        self.table_cell = []
        self.in_table = False
        self.in_heading = False

    def _flush_paragraph(self):
        text = "".join(self.buffer).strip()
        self.buffer = []
        if text:
            self.blocks.append(Block("p", _inline(text)))

    def _flush_list_item(self):
        text = "".join(self.buffer).strip()
        self.buffer = []
        if text:
            depth = max(1, len(self.list_stack))
            self.blocks.append(Block("bullet", _inline(text), level=depth))

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4"):
            self._flush_paragraph()
            self.in_heading = True
            self.buffer = []
        elif tag == "p":
            self._flush_paragraph()
            self.buffer = []
        elif tag in ("ul", "ol"):
            self._flush_paragraph()
            self.list_stack.append(tag)
        elif tag == "li":
            self._flush_paragraph()
            self.buffer = []
        elif tag == "pre":
            # Only <pre> opens a code block; inline <code> stays in the
            # paragraph flow so a sentence is never split in two.
            self._flush_paragraph()
            self.in_code = True
            self.code_lines = []
        elif tag == "hr":
            self._flush_paragraph()
            self.blocks.append(Block("rule"))
        elif tag == "table":
            self._flush_paragraph()
            self.in_table = True
            self.table_rows = []
        elif tag == "tr":
            self.table_row = []
        elif tag in ("th", "td"):
            self.table_cell = []
        elif tag == "br":
            self.buffer.append("\n")

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4"):
            text = _inline("".join(self.buffer).strip())
            self.buffer = []
            self.in_heading = False
            level = int(tag[1])
            kind = "title" if level == 1 else f"h{min(level, 4)}"
            if text:
                self.blocks.append(Block(kind, text))
        elif tag == "p":
            self._flush_paragraph()
        elif tag == "li":
            self._flush_list_item()
        elif tag in ("ul", "ol"):
            self._flush_paragraph()
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "pre":
            self.in_code = False
            code = "\n".join(self.code_lines).rstrip()
            if code:
                self.blocks.append(Block("code", code))
            self.code_lines = []
        elif tag == "table":
            self.in_table = False
            if self.table_rows:
                self.blocks.append(Block("table", rows=self.table_rows))
            self.table_rows = []
        elif tag == "tr":
            if self.table_row:
                self.table_rows.append(self.table_row)
            self.table_row = []
        elif tag in ("th", "td"):
            self.table_row.append(_inline("".join(self.table_cell).strip()))
            self.table_cell = []

    def handle_data(self, data):
        if self.in_table:
            if data.strip():
                self.table_cell.append(data)
            return
        if self.in_code:
            self.code_lines.append(data)
            return
        self.buffer.append(data)

    def close(self):
        super().close()
        self._flush_paragraph()


def parse_content(source):
    """Parse a chapter string into blocks (HTML or legacy markdown)."""
    parser = ContentParser()
    parser.feed(_markdown_tables_to_html(source))
    parser.close()
    return parser.blocks


class TableWidget(tk.Frame):
    """A real, bordered table drawn on a single canvas.

    An earlier version built every cell from its own ``tk.Label``. Measuring
    that showed roughly 3 ms per label, so one large chapter cost well over a
    second and the popup was painfully slow. A canvas draws the same grid with
    rectangles and text items, which are not widgets and cost a fraction of
    that, so a whole table is now one widget.

    Cell text wraps at the column width, because ``create_text``'s ``width``
    option constrains it. Without wrapping, long cells render at their full
    natural width and overlap the neighbouring column.
    """

    CELL_PADX = 8
    CELL_PADY = 6
    MIN_COLUMN = 90
    MIN_WRAP = 60

    _normal_font = None
    _bold_font = None
    _metric_cache = {}
    _font_root = None

    def __init__(self, master, rows, max_width=980):
        super().__init__(master, background=TABLE_BG)
        self.rows = rows
        self._max_width = max_width
        self._columns = max(len(row) for row in rows)

        # Fonts belong to a Tk interpreter, so they are recreated whenever the
        # default root changes. A cached Font from a destroyed interpreter
        # raises TclError on use.
        if (TableWidget._font_root is not tkinter._default_root
                or TableWidget._normal_font is None):
            TableWidget._normal_font = tk.font.Font(
                family="Segoe UI", size=10)
            TableWidget._bold_font = tk.font.Font(
                family="Segoe UI", size=10, weight="bold")
            TableWidget._metric_cache.clear()
            TableWidget._font_root = tkinter._default_root

        self.canvas = tk.Canvas(self, background=TABLE_BG,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self._last_width = 0
        self._last_height = 0
        self._laid_out = False
        self.bind("<Configure>", self._on_resize, add="+")

    def _on_resize(self, event):
        # Only re-lay-out on a real width change; re-flowing a large table on
        # every pixel of a drag is what made resizing stutter. The first
        # Configure is the one that matters, so no idle fallback is needed.
        if abs(event.width - self._last_width) > 4:
            self._relayout(event.width)

    def _column_widths(self, total_width):
        """Distribute the available width using the longest cell per column."""
        longest = [1] * self._columns
        for row in self.rows:
            for column, cell in enumerate(row):
                longest[column] = max(longest[column], len(str(cell)))

        # Weight by content length but damp it, so one very long cell cannot
        # starve every other column.
        weights = [min(value, 90) ** 0.5 for value in longest]
        usable = max(total_width - 2, self._columns * self.MIN_COLUMN)
        scale = min(1.0, self._max_width / max(sum(weights), 1e-6))

        widths = []
        for weight in weights:
            widths.append(max(self.MIN_COLUMN,
                              int(usable * weight * scale / sum(weights))))
        return widths

    def _metrics(self, font):
        """Character width and line height, measured once per font."""
        key = str(font)
        cached = TableWidget._metric_cache.get(key)
        if cached is None:
            cached = (max(1.0, font.measure("0")),
                      max(1, font.metrics("linespace")))
            TableWidget._metric_cache[key] = cached
        return cached

    def _relayout(self, total_width=None):
        if not self.rows:
            return
        if total_width is None:
            total_width = max(self.canvas.winfo_width(), 1)
        total_width = max(total_width, self._columns * self.MIN_COLUMN + 2)
        # Re-laying out on every Configure event cascades: sizing the frame
        # fires another Configure. Only act on a genuine width change.
        if self._laid_out and abs(total_width - self._last_width) <= 4:
            return
        self._last_width = total_width

        canvas = self.canvas
        canvas.delete("all")

        columns = self._column_widths(total_width)
        offsets = []
        x = 1
        for width in columns:
            offsets.append(x)
            x += width

        pad = self.CELL_PADX
        wrap_widths = [max(self.MIN_WRAP, w - 2 * pad) for w in columns]
        normal_char, normal_line = self._metrics(self._normal_font)
        bold_char, bold_line = self._metrics(self._bold_font)

        # Pre-wrap every cell into explicit lines. Canvas does not break long
        # unbroken words, so something like an ARN in a narrow column would
        # render at full width and spill over the next column, which is exactly
        # the overlapping-text bug. Wrapping here also gives the row height
        # without asking Tk to measure anything.
        wrapped_rows = []
        row_heights = []
        for row_index, row in enumerate(self.rows):
            is_header = row_index == 0
            char_w, line_h = (bold_char, bold_line) if is_header else (
                normal_char, normal_line)
            lines = 1
            cells = []
            for column in range(self._columns):
                text = str(row[column]) if column < len(row) else ""
                per_line = max(4, int(wrap_widths[column] / char_w * 0.92))
                wrapped = textwrap.wrap(text, per_line, break_long_words=True,
                                        break_on_hyphens=False) or [""]
                lines = max(lines, len(wrapped))
                cells.append("\n".join(wrapped))
            wrapped_rows.append(cells)
            row_heights.append(lines * line_h + 2 * self.CELL_PADY)

        # Paint one filled rectangle per row rather than one per cell: every cell in
        # a row shares the same fill, so per-cell rectangles only existed to
        # draw the vertical separators, which are cheaper as lines.
        y = 1
        for row_index in range(len(self.rows)):
            height = row_heights[row_index]
            is_header = row_index == 0
            fill = TABLE_HEADING_BG if is_header else (
                TABLE_BG if row_index % 2 else TABLE_STRIPE)
            canvas.create_rectangle(
                offsets[0], y, offsets[-1] + columns[-1], y + height,
                fill=fill, outline=BORDER)
            for column in range(1, self._columns):
                canvas.create_line(offsets[column], y,
                                   offsets[column], y + height, fill=BORDER)
            y += height

        # Then draw the text on top. The lines are already wrapped, so no
        # width is passed to create_text.
        y = 1
        for row_index, row in enumerate(self.rows):
            height = row_heights[row_index]
            is_header = row_index == 0
            font = self._bold_font if is_header else self._normal_font
            colour = "#ffffff" if is_header else FG
            for column in range(self._columns):
                canvas.create_text(
                    offsets[column] + pad, y + self.CELL_PADY,
                    text=wrapped_rows[row_index][column],
                    anchor="nw", justify="left", font=font, fill=colour)
            y += height

        self._laid_out = True
        self._last_height = y + 1
        self.configure(height=self._last_height)


class _Pane(ctk.CTkScrollableFrame):
    """A scrollable pane whose CustomTkinter wheel bindings are muted.

    ``CTkScrollableFrame`` registers ``<MouseWheel>`` (and the shift keys)
    through ``bind_all()`` in its constructor. Those Tcl callbacks are owned
    by the widget: destroying the Learning window deletes them, but the
    script stays in the application's ``all`` tag. On the next open the new
    handlers are appended *behind* the dead ones, so every wheel event dies
    on the stale entry and nothing after it ever runs.

    DocKube drives scrolling from one long-lived dispatcher instead (see
    ``LearningWindow._register_wheel``), so the widget's own registration is
    simply dropped here at construction.
    """

    def bind_all(self, sequence=None, func=None, add=None):
        # Deliberately a no-op: the constructor's bind_all() calls are the
        # only ones this widget ever makes.
        return None


class LearningWindow(ctk.CTkToplevel):
    """The popup study guide.

    Opens in its own window so the main DocKube layout keeps its vertical
    space for commands. A sidebar lists every chapter; clicking one swaps the
    content pane to that chapter.
    """

    # Parsed chapters, shared across popups so revisiting one is instant.
    _block_cache = {}

    # One application-wide wheel handler per process. It is bound to the main
    # window (which outlives every popup) and routes to whichever Learning
    # window is currently open, so no handler is ever added or removed again.
    _wheel_host = None
    _active = None

    def __init__(self, master, chapters):
        super().__init__(master)
        self.chapters = chapters
        self.title("DocKube Learning Centre")
        self.geometry("1250x820")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self._section_marks = []
        self._toc_buttons = {}
        # Register before building: _Pane has muted the widget-level
        # handlers, so the dispatcher must be in place before any event.
        LearningWindow._active = self
        self._register_wheel(master)
        self._build()

    @classmethod
    def _register_wheel(cls, host):
        """Bind the wheel helper exactly once, on a widget that never dies."""
        if cls._wheel_host is not None:
            return
        cls._wheel_host = host
        host.bind_all("<MouseWheel>", cls._on_wheel, add="+")
        host.bind_all("<Button-4>", cls._on_wheel, add="+")
        host.bind_all("<Button-5>", cls._on_wheel, add="+")

    @classmethod
    def _on_wheel(cls, event):
        """Scroll the pane under the pointer, exactly once per event.

        Two bugs are solved in one handler. CustomTkinter converts the wheel
        to ``-int(delta / 6)`` units on Windows, which truncates the small
        deltas a precision touchpad emits down to zero -- that is why
        two-finger scrolling felt dead. And because CustomTkinter's own
        handlers are muted in ``_Pane``, this performs the full conversion
        for every event, with the same sign convention as everywhere else in
        DocKube: positive delta (wheel rolled away from the user) scrolls up.
        """
        window = cls._active
        if window is None:
            return
        try:
            if not window.winfo_exists():
                return
        except tk.TclError:
            return
        canvas = window._pane_canvas(getattr(event, "widget", None))
        if canvas is None:
            return
        num = getattr(event, "num", 0)
        if num in (4, 5):
            units = -1 if num == 4 else 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            if sys.platform.startswith("win"):
                units = -int(delta / 6)
                if units == 0:
                    # The touchpad micro-deltas int(delta / 6) swallows.
                    units = -1 if delta > 0 else 1
            elif sys.platform == "darwin":
                units = -delta
            else:
                units = -1 if delta > 0 else 1
        try:
            canvas.yview_scroll(units, "units")
        except tk.TclError:
            return

    def _pane_canvas(self, widget):
        """The canvas of the pane ``widget`` belongs to, or None."""
        outer = getattr(self, "outer", None)
        toc = getattr(self, "_toc", None)
        if outer is None or toc is None:
            return None
        current = widget
        while current is not None:
            if current is outer or current is outer._parent_canvas:
                return outer._parent_canvas
            if current is toc or current is toc._parent_canvas:
                return toc._parent_canvas
            current = getattr(current, "master", None)
        return None

    def destroy(self):
        if LearningWindow._active is self:
            LearningWindow._active = None
        super().destroy()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=SIDEBAR_WIDTH)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 6))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="DocKube Learning Centre",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="Start here if you are completely new",
                     text_color=MUTED, anchor="e").grid(row=0, column=2, sticky="e")
        ctk.CTkButton(header, text="Close", width=90, command=self.destroy).grid(
            row=0, column=3, padx=(12, 0))

        # The sidebar holds a scrollable TOC. It must be able to shrink, and
        # the TOC needs an explicit width, otherwise CustomTkinter computes a
        # zero-width scrollbar and hides it.
        sidebar = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=0)
        sidebar.grid(row=1, column=0, rowspan=2, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="CHAPTERS", anchor="w",
                     font=ctk.CTkFont(weight="bold"), text_color=MUTED).grid(
            row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        toc = _Pane(sidebar, fg_color="transparent",
                    scrollbar_button_color="#30363d",
                    scrollbar_button_hover_color="#484f58")
        toc.grid(row=1, column=0, sticky="nsew", padx=(6, 2), pady=(0, 4))
        self._toc = toc
        for index, (title, _body) in enumerate(self.chapters):
            button = ctk.CTkButton(
                toc, text=title, anchor="w", fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("#21262d", "#30363d"),
                command=lambda i=index: self.show_chapter(i))
            button.pack(fill="x", pady=2, padx=4)
            self._toc_buttons[index] = button

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=1, sticky="ew", padx=16, pady=(4, 10))
        footer.grid_columnconfigure(0, weight=1)
        self.status = ctk.CTkLabel(footer, text="", anchor="w", text_color=MUTED)
        self.status.grid(row=0, column=0, sticky="w")
        # Scrolling between chapters is gone, so give explicit step buttons.
        self.prev_btn = ctk.CTkButton(footer, text="Previous", width=90,
                                      command=lambda: self.step_chapter(-1))
        self.prev_btn.grid(row=0, column=1, padx=(8, 4))
        self.next_btn = ctk.CTkButton(footer, text="Next", width=90,
                                      command=lambda: self.step_chapter(1))
        self.next_btn.grid(row=0, column=2)

        # Tables are embedded as real child widgets inside this frame so they
        # scroll together with the surrounding text.
        self.outer = _Pane(self, fg_color="transparent")
        self.outer.grid(row=1, column=1, sticky="nsew", padx=16, pady=4)
        self.outer.grid_columnconfigure(0, weight=1)

        self._current = None
        self.show_chapter(0)

    def step_chapter(self, delta):
        """Move to the previous or next chapter, if there is one."""
        target = (self._current or 0) + delta
        if 0 <= target < len(self.chapters):
            self.show_chapter(target)

    def _clear(self):
        for child in self.outer.winfo_children():
            child.destroy()

    def _render(self, index):
        """Render one chapter only.

        Rendering all fifteen chapters built about 5,600 widgets inside a
        ``CTkScrollableFrame``, which rescans its children on every geometry
        change. That is quadratic and took the popup about 18 seconds to open.
        Building only the chapter the reader asked for keeps the widget count
        in the low hundreds and makes opening instant.
        """
        self._clear()
        self._current = index
        title, body = self.chapters[index]
        self._render_chapter(index, title, body, 0)
        self.outer._parent_canvas.yview_moveto(0.0)

    def _render_chapter(self, index, title, body, row):
        banner = tk.Frame(self.outer, background="#0d1117",
                          highlightbackground=BORDER, highlightthickness=1)
        banner.grid(row=row, column=0, sticky="ew", pady=(10, 6), padx=2)
        banner.grid_columnconfigure(0, weight=1)
        tk.Label(banner, text=f"{index + 1}. {title}", background="#0d1117",
                 foreground=ACCENT, anchor="w", justify="left",
                 font=("Segoe UI", 16, "bold"),
                 padx=12, pady=10).grid(row=0, column=0, sticky="ew")
        self._section_marks = [(index, banner)]
        row += 1

        for block in self._blocks_for(index, body):
            row = self._render_block(block, row)
        return row

    @staticmethod
    def _blocks_for(index, body):
        """Parse a chapter once and remember it for the next visit."""
        cache = LearningWindow._block_cache
        if index not in cache:
            cache[index] = parse_content(body)
        return cache[index]

    def _render_block(self, block, row):
        if block.kind == "title":
            return self._text(row, block.text, size=20, color=ACCENT, bold=True)
        if block.kind == "h2":
            return self._text(row, block.text, size=16, color=ACCENT, bold=True)
        if block.kind == "h3":
            return self._text(row, block.text, size=14, color="#79c0ff", bold=True)
        if block.kind == "h4":
            return self._text(row, block.text, size=13, color=MUTED, bold=True)
        if block.kind == "p":
            return self._text(row, block.text, size=12, color=FG)
        if block.kind == "bullet":
            indent = "    " * max(0, block.level - 1)
            return self._text(row, f"{indent}- {block.text}", size=12, color=FG)
        if block.kind == "code":
            return self._code(block.text, row)
        if block.kind == "table":
            return self._table(block.rows, row)
        if block.kind == "rule":
            tk.Frame(self.outer, height=1, background=BORDER).grid(
                row=row, column=0, sticky="ew", pady=8, padx=2)
            return row + 1
        return row

    def _text(self, row, text, size=12, color=FG, bold=False):
        # A plain tk.Label rather than a CTkLabel: CustomTkinter draws every
        # widget on a rounded canvas, which made chapter switching crawl. For
        # flat text on a flat background the result looks identical.
        label = tk.Label(
            self.outer, text=text, background=BG, foreground=color,
            anchor="w", justify="left", wraplength=900,
            font=("Segoe UI", size, "bold" if bold else "normal"))
        label.grid(row=row, column=0, sticky="ew", pady=2, padx=4)
        return row + 1

    def _code(self, text, row):
        box = tk.Frame(self.outer, background="#0d1117",
                       highlightbackground=BORDER, highlightthickness=1)
        box.grid(row=row, column=0, sticky="ew", pady=6, padx=4)
        tk.Label(box, text=text, background="#0d1117", foreground=GREEN,
                 font=("Cascadia Mono", 11), justify="left", anchor="w",
                 padx=12, pady=10).pack(fill="x")
        return row + 1

    def _table(self, rows, row):
        holder = tk.Frame(self.outer)
        holder.grid(row=row, column=0, sticky="ew", pady=8, padx=4)
        TableWidget(holder, rows).pack(fill="x", expand=True)
        return row + 1

    def show_chapter(self, index):
        """Show one chapter, rebuilding the pane only when it changes."""
        if not (0 <= index < len(self.chapters)):
            return
        if index != self._current:
            self._render(index)
        for number, button in self._toc_buttons.items():
            button.configure(
                fg_color="#1f6feb" if number == index else "transparent")
        self._update_footer(index)
        self.status.configure(text=f"Chapter {index + 1} of {len(self.chapters)}")

    def _update_footer(self, index):
        """Grey out Previous/Next when there is nothing in that direction."""
        state = lambda on: "normal" if on else "disabled"  # noqa: E731
        self.prev_btn.configure(state=state(index > 0))
        self.next_btn.configure(state=state(index < len(self.chapters) - 1))