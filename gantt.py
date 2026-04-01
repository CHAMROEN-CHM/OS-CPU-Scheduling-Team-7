import tkinter as tk
from tkinter import ttk
from typing import List, Tuple

COLORS = ["#4ECDC4","#FF6B6B","#FFE66D","#A8E6CF","#C3B1E1",
          "#FFA07A","#87CEEB","#DDA0DD","#98FB98","#F08080"]
BG   = "#1E1E2E"
IDLE = "#2E3250"
RUL  = "#7777AA"
WHT  = "#FFFFFF"
LBL  = "#CCCCDD"

H_BAR   = 42
Y_BAR   = 44
Y_RUL   = 16
MARGIN  = 58
SCALE   = 30
TOTAL_H = Y_BAR + H_BAR + 38   # 124px


class GanttCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        kw.setdefault("bg", BG)
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("height", TOTAL_H)
        super().__init__(parent, **kw)
        self._colors = {}
        self._idx = 0

    def _color(self, pid):
        if pid == "IDLE": return IDLE
        if pid not in self._colors:
            self._colors[pid] = COLORS[self._idx % len(COLORS)]
            self._idx += 1
        return self._colors[pid]

    def draw(self, gantt: List[Tuple[str, int, int]]):
        self.delete("all")
        self._colors = {}
        self._idx = 0

        if not gantt:
            self.config(scrollregion=(0, 0, 800, TOTAL_H))
            self.create_rectangle(0, 0, 800, TOTAL_H, fill=BG, outline="")
            self.create_text(400, TOTAL_H // 2,
                text="Click ▶ RUN SIMULATION to see results.",
                fill=RUL, font=("Consolas", 11))
            return

        max_t   = max(e for _, _, e in gantt)
        total_w = max(800, MARGIN + max_t * SCALE + 50)
        self.config(scrollregion=(0, 0, total_w, TOTAL_H))
        self.create_rectangle(0, 0, total_w, TOTAL_H, fill=BG, outline="")

        # ruler
        self.create_line(MARGIN, Y_RUL + 8,
                         MARGIN + max_t * SCALE, Y_RUL + 8,
                         fill=RUL, width=1)
        step = max(1, max_t // 20)
        for t in sorted(set(range(0, max_t + 1, step)) | {max_t}):
            x = MARGIN + t * SCALE
            self.create_line(x, Y_RUL + 4, x, Y_RUL + 13, fill=RUL)
            self.create_text(x, Y_RUL, text=str(t),
                             fill=RUL, font=("Consolas", 8))
        self.create_text(MARGIN // 2, Y_RUL + 6,
                         text="Time\u2192", fill=RUL, font=("Consolas", 7))

        # bars  — NO 8-digit hex colours (Windows Tkinter doesn't support alpha)
        y1, y2 = Y_BAR, Y_BAR + H_BAR
        for pid, s, e in gantt:
            c  = self._color(pid)
            x1 = MARGIN + s * SCALE
            x2 = MARGIN + e * SCALE
            w  = x2 - x1

            # main bar
            self.create_rectangle(x1, y1, x2, y2,
                                  fill=c, outline="#FFFFFF", width=1)
            # shine strip (solid lighter colour — no alpha)
            if w > 4:
                self.create_rectangle(x1 + 1, y1 + 1, x2 - 1,
                                      y1 + H_BAR // 3,
                                      fill="#FFFFFF", outline="",
                                      stipple="gray25")   # dithered transparency
            # label
            if w > 10:
                lbl = pid if pid != "IDLE" else "..."
                fs  = 8 if w < 28 else 10
                self.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                 text=lbl, fill="#000000" if c in ("#FFE66D","#A8E6CF","#87CEEB") else WHT,
                                 font=("Consolas", fs, "bold"))

        # legend
        seen = list(dict.fromkeys(p for p, _, _ in gantt))
        lx = MARGIN
        ly = Y_BAR + H_BAR + 16
        self.create_text(lx, ly, text="Legend:", anchor="w",
                         fill=LBL, font=("Consolas", 8, "bold"))
        lx += 58
        for pid in seen:
            c = self._color(pid)
            self.create_rectangle(lx, ly - 6, lx + 12, ly + 6,
                                  fill=c, outline="")
            self.create_text(lx + 16, ly, text=pid, anchor="w",
                             fill=LBL, font=("Consolas", 8))
            lx += 48


class GanttFrame(ttk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.canvas = GanttCanvas(self)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hsb.set)
        self.canvas.pack(fill="x")
        hsb.pack(fill="x")

    def draw(self, gantt):
        self.canvas.draw(gantt)