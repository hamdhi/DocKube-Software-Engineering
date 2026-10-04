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

# Slight breathing room so a chapter heading is not glued to the pane edge.
HEADER_OFFSET = 12

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


class TableWidget(ctk.CTkFrame):
    """A real, bordered table.

    ``tk.Text`` cannot draw grids, so tables are built from actual frames and
    labels. That gives proper column alignment, a shaded header and zebra
    striping instead of pipes on a single line.
    """

    def __init__(self, master, rows, max_width=980):
        super().__init__(master, fg_color=TABLE_BG, corner_radius=0)
        self.rows = rows
        columns = max(len(row) for row in rows)
        widths = self._compute_widths(rows, columns, max_width)

        for column in range(columns):
            self.columnconfigure(column, weight=1, minsize=widths[column])

        for row_index, row in enumerate(rows):
            is_header = row_index == 0
            background = TABLE_HEADING_BG if is_header else (
                TABLE_BG if row_index % 2 else TABLE_STRIPE)
            for column in range(columns):
                text = row[column] if column < len(row) else ""
                tk.Label(
                    self, text=text, background=background,
                    foreground="#ffffff" if is_header else FG,
                    font=("Segoe UI", 10, "bold") if is_header else ("Segoe UI", 10),
                    justify="left", anchor="w", wraplength=0,
                    padx=10, pady=6, borderwidth=0,
                    highlightthickness=1, highlightbackground=BORDER
                ).grid(row=row_index, column=column, sticky="ew")

    @staticmethod
    def _compute_widths(rows, columns, max_width):
        """Give wide columns more room, then scale to fit the pane."""
        longest = [0] * columns
        for row in rows:
            for column, cell in enumerate(row):
                longest[column] = max(longest[column], len(str(cell)))
        if sum(longest) == 0:
            longest = [80] * columns
        scale = min(1.0, max_width / max(sum(longest), 1))
        return [max(90, int(value * scale)) for value in longest]


class LearningWindow(ctk.CTkToplevel):
    """The popup study guide.

    Opens in its own window so the main DocKube layout keeps its vertical
    space for commands. A sidebar lists every chapter; clicking one scrolls
    the content pane to that section.
    """

    def __init__(self, master, chapters):
        super().__init__(master)
        self.chapters = chapters
        self.title("DocKube Learning Centre")
        self.geometry("1250x820")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self._section_marks = []
        self._toc_buttons = {}
        self._build()
        self.show_chapter(0)

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

        toc = ctk.CTkScrollableFrame(sidebar, fg_color="transparent",
                                     scrollbar_button_color="#30363d",
                                     scrollbar_button_hover_color="#484f58")
        toc.grid(row=1, column=0, sticky="nsew", padx=(6, 2), pady=(0, 4))
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

        # Tables are embedded as real child widgets inside this frame so they
        # scroll together with the surrounding text.
        self.outer = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.outer.grid(row=1, column=1, sticky="nsew", padx=16, pady=4)
        self.outer.grid_columnconfigure(0, weight=1)

        self._render()

    def _clear(self):
        for child in self.outer.winfo_children():
            child.destroy()

    def _render(self):
        """Render every chapter into the scroll pane."""
        self._clear()
        self._section_marks = []
        row = 0
        for index, (title, body) in enumerate(self.chapters):
            row = self._render_chapter(index, title, body, row)


    def _render_chapter(self, index, title, body, row):
        banner = ctk.CTkFrame(self.outer, fg_color="#0d1117", corner_radius=6)
        banner.grid(row=row, column=0, sticky="ew", pady=(10, 6), padx=2)
        banner.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(banner, text=f"{index + 1}. {title}", anchor="w",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ACCENT).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        self._section_marks.append((index, banner))
        row += 1

        for block in parse_content(body):
            row = self._render_block(block, row)
        return row

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
        label = ctk.CTkLabel(
            self.outer, text=text, anchor="w", justify="left", wraplength=900,
            font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"),
            text_color=color)
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
        holder = ctk.CTkFrame(self.outer, fg_color="transparent")
        holder.grid(row=row, column=0, sticky="ew", pady=8, padx=4)
        TableWidget(holder, rows).pack(fill="x", expand=True)
        return row + 1

    def _scroll_to(self, widget):
        """Scroll so ``widget`` sits near the top of the content pane.

        ``yview_moveto`` takes a fraction of the **whole** document, so the
        target pixel offset has to be divided by the full scrollregion height.
        Subtracting the current offset instead (an earlier mistake) only works
        when jumping from the very top, which made the sidebar highlight one
        chapter while the pane showed another.
        """
        self.update_idletasks()
        canvas = getattr(self.outer, "_parent_canvas", None)
        if canvas is None:
            return
        canvas.update_idletasks()
        try:
            total = float(canvas.cget("scrollregion").split()[3])
        except (IndexError, ValueError):
            return
        if total <= 0:
            return
        target = widget.winfo_y()
        fraction = (target - HEADER_OFFSET) / total
        canvas.yview_moveto(min(1.0, max(0.0, fraction)))

    def show_chapter(self, index):
        """Scroll the content pane so the requested chapter is in view."""
        for number, button in self._toc_buttons.items():
            button.configure(
                fg_color="#1f6feb" if number == index else "transparent")
        for number, widget in self._section_marks:
            if number == index:
                self._scroll_to(widget)
                self.status.configure(
                    text=f"Chapter {index + 1} of {len(self.chapters)}")
                return