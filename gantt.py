"""
Gantt Chart Canvas Widget
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

PROCESS_COLORS = [
    "#4ECDC4", "#FF6B6B", "#FFE66D", "#A8E6CF",
    "#C3B1E1", "#FFA07A", "#87CEEB", "#DDA0DD",
    "#98FB98", "#F08080", "#E0BBFF", "#FFDAB9",
]
IDLE_COLOR  = "#2E3250"
BG_COLOR    = "#1E1E2E"
RULER_COLOR = "#8888AA"
TEXT_COLOR  = "#FFFFFF"
LABEL_COLOR = "#CCCCDD"

BAR_HEIGHT   = 40
BAR_Y        = 46
RULER_Y      = 18
LABEL_MARGIN = 60
TIME_SCALE   = 32
CANVAS_H     = BAR_Y + BAR_HEIGHT + 40   # 126 px total


class GanttCanvas(tk.Canvas):

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_COLOR)
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("height", CANVAS_H)
        super().__init__(parent, **kwargs)
        self._pid_color: dict = {}
        self._idx = 0

    def _color(self, pid):
        if pid == "IDLE":
            return IDLE_COLOR
        if pid not in self._pid_color:
            self._pid_color[pid] = PROCESS_COLORS[self._idx % len(PROCESS_COLORS)]
            self._idx += 1
        return self._pid_color[pid]

    def draw(self, gantt: List[Tuple[str, int, int]]):
        self.delete("all")
        self._pid_color = {}
        self._idx = 0

        if not gantt:
            self.config(scrollregion=(0, 0, 800, CANVAS_H))
            self.create_text(400, CANVAS_H // 2,
                             text="Click ▶ RUN SIMULATION to see results.",
                             fill=RULER_COLOR, font=("Consolas", 11))
            return

        max_time = max(e for _, _, e in gantt)
        total_w  = max(800, LABEL_MARGIN + max_time * TIME_SCALE + 40)
        self.config(scrollregion=(0, 0, total_w, CANVAS_H))
        self.create_rectangle(0, 0, total_w, CANVAS_H, fill=BG_COLOR, outline="")

        # ruler
        self.create_line(LABEL_MARGIN, RULER_Y + 8,
                         LABEL_MARGIN + max_time * TIME_SCALE, RULER_Y + 8,
                         fill=RULER_COLOR, width=1)
        step = max(1, max_time // 20)
        for t in sorted(set(range(0, max_time + 1, step)) | {max_time}):
            x = LABEL_MARGIN + t * TIME_SCALE
            self.create_line(x, RULER_Y + 4, x, RULER_Y + 13, fill=RULER_COLOR)
            self.create_text(x, RULER_Y, text=str(t),
                             fill=RULER_COLOR, font=("Consolas", 8))
        self.create_text(LABEL_MARGIN // 2, RULER_Y + 6,
                         text="Time→", fill=RULER_COLOR, font=("Consolas", 7))

        # bars
        y1, y2 = BAR_Y, BAR_Y + BAR_HEIGHT
        for pid, s, e in gantt:
            color = self._color(pid)
            x1 = LABEL_MARGIN + s * TIME_SCALE
            x2 = LABEL_MARGIN + e * TIME_SCALE
            self.create_rectangle(x1, y1, x2, y2,
                                  fill=color, outline="#FFFFFF22", width=1)
            w = x2 - x1
            if w > 4:
                self.create_rectangle(x1+1, y1+1, x2-1,
                                      y1 + BAR_HEIGHT // 3,
                                      fill="#FFFFFF18", outline="")
            if w > 10:
                lbl = pid if pid != "IDLE" else "···"
                fs  = 8 if w < 26 else 10
                self.create_text((x1+x2)//2, (y1+y2)//2, text=lbl,
                                 fill=TEXT_COLOR, font=("Consolas", fs, "bold"))

        # legend
        seen = list(dict.fromkeys(pid for pid, _, _ in gantt))
        lx = LABEL_MARGIN
        ly = BAR_Y + BAR_HEIGHT + 16
        self.create_text(lx, ly, text="Legend:", anchor="w",
                         fill=LABEL_COLOR, font=("Consolas", 8, "bold"))
        lx += 58
        for pid in seen:
            c = self._color(pid)
            self.create_rectangle(lx, ly-6, lx+12, ly+6, fill=c, outline="")
            self.create_text(lx+16, ly, text=pid, anchor="w",
                             fill=LABEL_COLOR, font=("Consolas", 8))
            lx += 48


class GanttFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = GanttCanvas(self)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hsb.set)
        self.canvas.pack(fill="x")
        hsb.pack(fill="x")

    def draw(self, gantt):
        self.canvas.draw(gantt)
