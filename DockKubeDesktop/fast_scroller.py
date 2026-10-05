"""A scrollable region built from a plain tkinter canvas.

CustomTkinter's ``CTkScrollableFrame`` bundles a ``CTkScrollbar``, which draws
its thumb with rounded shapes on its own canvas. Profiling the DocKube dashboard
showed two of those cost roughly 120 ms to construct and redraw, and made every
category switch noticeably sluggish.

This does the same job with plain tk widgets: one canvas holding an inner frame,
plus a thin scrollbar drawn as a single canvas rectangle that only appears when
the content actually overflows.

The inner frame is exposed as ``.body`` so callers keep adding children to a
single object, and ``yview``/``yview_moveto`` are proxied so existing callers
that scrolled a CustomTkinter frame keep working.
"""

import tkinter as tk


class FastScroller(tk.Frame):
    """A vertically scrollable container.

    Add children to ``self.body``; this widget only handles scrolling.
    """

    def __init__(self, master, bg=None, width=16):
        if bg is None:
            try:
                bg = master.cget("background")
            except Exception:
                bg = "#2b2b2b"
        super().__init__(master, background=bg)
        self._bg = bg

        # A tk.Canvas asks for 378 px if its width is left unset, which made the
        # sidebar balloon to that width even though the nav is only meant to be
        # SIDEBAR_WIDTH. width=1 says "whatever the container gives me"; the
        # column minsize then sets the real size.
        self.canvas = tk.Canvas(self, background=bg, highlightthickness=0, bd=0,
                                width=1)
        self._bar = tk.Canvas(self, background=bg, highlightthickness=0, bd=0,
                              width=width)
        self._bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.body = tk.Frame(self.canvas, background=bg)
        self._window = self.canvas.create_window((0, 0), window=self.body,
                                                 anchor="nw")

        self._thumb_drag = None

        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)
        self._bar.bind("<Button-1>", self._bar_press)
        self._bar.bind("<B1-Motion>", self._bar_drag)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _on_body(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._redraw_bar()

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)
        self._redraw_bar()

    # ------------------------------------------------------------------
    # Scrolling
    # ------------------------------------------------------------------
    def _is_inside(self, widget):
        """True when ``widget`` is this scroller or one of its descendants."""
        current = widget
        while current is not None:
            if current is self or current is self.body:
                return True
            current = getattr(current, "master", None)
        return False

    def _bind_wheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.canvas.bind_all("<Button-4>", self._on_wheel, add="+")
        self.canvas.bind_all("<Button-5>", self._on_wheel, add="+")

    def _unbind_wheel(self, _event=None):
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(sequence)

    def _on_wheel(self, event):
        # Nested scrollers all bind globally, so only the one actually under
        # the pointer may react.
        if not self._is_inside(getattr(event, "widget", None)):
            return
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def yview(self):
        return self.canvas.yview()

    def yview_moveto(self, fraction):
        self.canvas.yview_moveto(fraction)

    def see(self, widget):
        """Scroll so ``widget`` is visible, like the scrolled frame API."""
        self.body.update_idletasks()
        top = widget.winfo_rooty() - self.body.winfo_rooty()
        self.canvas.yview_moveto(top / max(1, self.body.winfo_height()))

    # ------------------------------------------------------------------
    # Scrollbar
    # ------------------------------------------------------------------
    def _metrics(self):
        """(first, last) fractions plus the viewport and document heights."""
        first, last = self.canvas.yview()
        total = self.canvas.bbox("all")
        height = (total[3] - total[1]) if total else 0
        view = self.canvas.winfo_height()
        if height <= view or view <= 0:
            return None
        return first, last, view, height

    def _redraw_bar(self):
        self._bar.delete("all")
        metrics = self._metrics()
        if metrics is None:
            # Nothing overflows, so show no scrollbar at all.
            self._bar.pack_forget()
            self.canvas.pack(side="left", fill="both", expand=True)
            return
        self._bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        first, last, _view, _height = metrics
        track_top = 2
        track = max(1, self._bar.winfo_height() - 4)
        top = track_top + int(track * first)
        bottom = track_top + int(track * last)
        self._bar.create_rectangle(
            3, top, max(4, self._bar.winfo_width() - 3),
            max(bottom, top + 18), fill="#4a4a4a", outline="")

    def _bar_press(self, event):
        metrics = self._metrics()
        if not metrics:
            return
        first, last, _view, _height = metrics
        track = max(1, self._bar.winfo_height() - 4)
        fraction = max(0.0, min(1.0, event.y / track))
        middle = (first + last) / 2
        # Clicking clear of the thumb pages the view instead of jumping.
        if abs(fraction - middle) > (last - first) / 2:
            self.canvas.yview_scroll(1 if fraction > middle else -1, "pages")
        else:
            self._thumb_drag = event.y

    def _bar_drag(self, event):
        if self._thumb_drag is None:
            return
        track = max(1, self._bar.winfo_height() - 4)
        self.canvas.yview_moveto(max(0.0, min(1.0, event.y / track)))
        self._thumb_drag = event.y
        self._redraw_bar()