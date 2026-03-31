"""
CPU Scheduling Algorithm Simulator  —  Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from algorithms import Process, fcfs, sjf, srt, round_robin, mlfq, compute_metrics
from gantt      import GanttFrame
from file_io    import load_file, export_results_csv

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK  = "#0F0F1A"
BG_MID   = "#1A1A2E"
BG_PANEL = "#16213E"
BG_CARD  = "#1E2A45"
ACCENT   = "#4ECDC4"
ACCENT2  = "#FF6B6B"
ACCENT3  = "#FFE66D"
TEXT_PRI = "#F0F0FF"
TEXT_SEC = "#A0A8C0"
TEXT_DIM = "#606880"
SEP      = "#2A3050"

FT = ("Segoe UI", 20, "bold")
FH = ("Segoe UI", 13, "bold")
FH3= ("Segoe UI", 11, "bold")
FB = ("Segoe UI", 10)
FS = ("Segoe UI",  9)
FM = ("Consolas", 10)
FMS= ("Consolas",  9)


def _btn(btn, primary=True):
    bg = ACCENT if primary else BG_CARD
    fg = BG_DARK if primary else TEXT_PRI
    btn.configure(bg=bg, fg=fg, relief="flat", bd=0, cursor="hand2",
                  font=FB, padx=12, pady=6,
                  activebackground="#3ABDB5", activeforeground=BG_DARK)


def _entry(parent, width=7):
    return tk.Entry(parent, font=FM, bg=BG_CARD, fg=TEXT_PRI,
                    insertbackground=ACCENT, relief="flat", width=width,
                    highlightthickness=1, highlightcolor=ACCENT,
                    highlightbackground=SEP)


# ── Process input table ───────────────────────────────────────────────────────
class ProcessTable(ttk.Frame):
    COLS = ("PID", "Arrival", "Burst")

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._setup_style()
        self._build()

    def _setup_style(self):
        s = ttk.Style()
        s.configure("PT.Treeview",
                    background=BG_CARD, foreground=TEXT_PRI,
                    fieldbackground=BG_CARD, rowheight=28, font=FM)
        s.configure("PT.Treeview.Heading",
                    background=BG_MID, foreground=ACCENT,
                    font=FH3, relief="flat")
        s.map("PT.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG_DARK)])

    def _build(self):
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings",
                                  style="PT.Treeview", height=8,
                                  selectmode="browse")
        for col, w in zip(self.COLS, [80, 100, 100]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center", minwidth=60)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def add(self, pid, arrival, burst):
        self.tree.insert("", "end", values=(pid, arrival, burst))

    def delete_selected(self):
        for s in self.tree.selection():
            self.tree.delete(s)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def get_processes(self):
        out = []
        for iid in self.tree.get_children():
            v = self.tree.item(iid, "values")
            out.append(Process(str(v[0]), int(v[1]), int(v[2])))
        return out


# ── Metrics table ─────────────────────────────────────────────────────────────
class MetricsTable(ttk.Frame):
    COLS = ("PID", "Arrival", "Burst", "Start", "Finish",
            "Waiting", "Turnaround", "Response")

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._setup_style()
        self._build()

    def _setup_style(self):
        s = ttk.Style()
        s.configure("MT.Treeview",
                    background=BG_CARD, foreground=TEXT_PRI,
                    fieldbackground=BG_CARD, rowheight=26, font=FMS)
        s.configure("MT.Treeview.Heading",
                    background=BG_MID, foreground=ACCENT3,
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("MT.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG_DARK)])

    def _build(self):
        widths = [55, 65, 65, 65, 65, 70, 90, 80]
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings",
                                  style="MT.Treeview", height=6)
        for col, w in zip(self.COLS, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center", minwidth=40)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def populate(self, metrics: dict):
        # clear first
        for row in self.tree.get_children():
            self.tree.delete(row)
        # insert fresh
        for r in metrics["rows"]:
            self.tree.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"],
                r["start"], r["finish"],
                r["waiting"], r["turnaround"], r["response"]
            ))
        self.update_idletasks()

    def clear(self):
        self.tree.delete(*self.tree.get_children())


# ── Main App ──────────────────────────────────────────────────────────────────
class App(tk.Tk):
    ALGOS = ["FCFS", "SJF", "SRT", "Round Robin", "MLFQ"]

    def __init__(self):
        super().__init__()
        self.title("CPU Scheduling Simulator")
        self.geometry("1180x820")
        self.minsize(900, 650)
        self.configure(bg=BG_DARK)
        self._cache: dict = {}
        self._build_ui()
        self._load_sample()
        self.after(250, self._run)   # auto-run FCFS on startup

    # ── layout ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=BG_MID, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  CPU Scheduling Simulator",
                 font=FT, fg=ACCENT, bg=BG_MID).pack(side="left", padx=20)
        tk.Label(hdr, text="OS Project — Python / Tkinter",
                 font=FS, fg=TEXT_DIM, bg=BG_MID).pack(side="left", padx=6)

        # body
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=14, pady=(6, 10))
        body.columnconfigure(0, weight=0, minsize=290)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    def _section(self, parent, title, row):
        f = tk.Frame(parent, bg=BG_PANEL)
        f.grid(row=row, column=0, sticky="ew", padx=10, pady=(10, 2))
        tk.Label(f, text=title, font=FH, fg=ACCENT, bg=BG_PANEL).pack(side="left")
        tk.Frame(f, bg=SEP, height=1).pack(side="left", fill="x", expand=True, padx=8)

    def _build_left(self, parent):
        left = tk.Frame(parent, bg=BG_PANEL)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        left.columnconfigure(0, weight=1)

        # ── Process Input ────────────────────────────────────
        self._section(left, "Process Input", row=0)

        # entry fields row
        ef = tk.Frame(left, bg=BG_PANEL)
        ef.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        for i, lbl in enumerate(["PID", "Arrival", "Burst"]):
            tk.Label(ef, text=lbl, font=FS, fg=TEXT_SEC,
                     bg=BG_PANEL).grid(row=0, column=i*2, padx=(4,2), sticky="e")
        self.e_pid = _entry(ef, 6); self.e_pid.insert(0, "P1")
        self.e_arr = _entry(ef, 5); self.e_arr.insert(0, "0")
        self.e_bst = _entry(ef, 5); self.e_bst.insert(0, "5")
        self.e_pid.grid(row=0, column=1, padx=(0,4))
        self.e_arr.grid(row=0, column=3, padx=(0,4))
        self.e_bst.grid(row=0, column=5, padx=(0,4))
        # bind Enter key
        for e in (self.e_pid, self.e_arr, self.e_bst):
            e.bind("<Return>", lambda _: self._add())

        # buttons
        br = tk.Frame(left, bg=BG_PANEL)
        br.grid(row=2, column=0, sticky="ew", padx=10, pady=(2,6))
        b_add = tk.Button(br, text="＋ Add",    command=self._add)
        b_del = tk.Button(br, text="✕ Delete",  command=self._delete)
        b_clr = tk.Button(br, text="⟳ Clear",   command=self._clear)
        _btn(b_add);  b_add.pack(side="left", padx=(0,6))
        _btn(b_del, False); b_del.pack(side="left", padx=(0,6))
        _btn(b_clr, False); b_clr.pack(side="left")

        # process table
        self.proc_table = ProcessTable(left)
        self.proc_table.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0,6))
        left.rowconfigure(3, weight=1)

        # file row
        fr = tk.Frame(left, bg=BG_PANEL)
        fr.grid(row=4, column=0, sticky="ew", padx=10, pady=(0,8))
        b_load   = tk.Button(fr, text="📂 Load File",   command=self._load_file)
        b_sample = tk.Button(fr, text="📋 Sample Data", command=self._load_sample)
        _btn(b_load,   False); b_load.pack(side="left", padx=(0,6))
        _btn(b_sample, False); b_sample.pack(side="left")

        tk.Frame(left, bg=SEP, height=1).grid(row=5, column=0, sticky="ew", padx=8)

        # ── Algorithm Settings ───────────────────────────────
        self._section(left, "Algorithm Settings", row=6)

        cfg = tk.Frame(left, bg=BG_PANEL)
        cfg.grid(row=7, column=0, sticky="ew", padx=10, pady=4)
        cfg.columnconfigure(1, weight=1)

        tk.Label(cfg, text="Algorithm:",   font=FS, fg=TEXT_SEC, bg=BG_PANEL).grid(row=0, column=0, sticky="w", pady=3)
        tk.Label(cfg, text="RR Quantum:",  font=FS, fg=TEXT_SEC, bg=BG_PANEL).grid(row=1, column=0, sticky="w", pady=3)
        tk.Label(cfg, text="MLFQ (q1,q2):",font=FS, fg=TEXT_SEC, bg=BG_PANEL).grid(row=2, column=0, sticky="w", pady=3)
        tk.Label(cfg, text="MLFQ Aging:",  font=FS, fg=TEXT_SEC, bg=BG_PANEL).grid(row=3, column=0, sticky="w", pady=3)

        self.algo_var = tk.StringVar(value="FCFS")
        self.combo = ttk.Combobox(cfg, textvariable=self.algo_var,
                                   values=self.ALGOS, state="readonly",
                                   font=FB, width=16)
        self.combo.grid(row=0, column=1, sticky="ew", padx=(8,0), pady=3)
        self.combo.bind("<<ComboboxSelected>>", self._on_algo)

        self.e_quantum = _entry(cfg, 6); self.e_quantum.insert(0, "2")
        self.e_mlfq    = _entry(cfg, 8); self.e_mlfq.insert(0, "2,4")
        self.e_aging   = _entry(cfg, 6); self.e_aging.insert(0, "10")
        self.e_quantum.grid(row=1, column=1, sticky="w", padx=(8,0), pady=3)
        self.e_mlfq.grid(   row=2, column=1, sticky="w", padx=(8,0), pady=3)
        self.e_aging.grid(  row=3, column=1, sticky="w", padx=(8,0), pady=3)
        self._on_algo()

        b_run = tk.Button(left, text="▶  RUN SIMULATION", command=self._run)
        _btn(b_run); b_run.configure(font=FH3, pady=10)
        b_run.grid(row=8, column=0, sticky="ew", padx=10, pady=8)

        b_all = tk.Button(left, text="⚡ Run All Algorithms", command=self._run_all)
        _btn(b_all, False)
        b_all.grid(row=9, column=0, sticky="ew", padx=10, pady=(0,8))

    def _build_right(self, parent):
        right = tk.Frame(parent, bg=BG_PANEL)
        right.grid(row=0, column=1, sticky="nsew", pady=4)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        # Gantt
        self._section(right, "Gantt Chart", row=0)
        self.gantt = GanttFrame(right)
        self.gantt.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,4))

        tk.Frame(right, bg=SEP, height=1).grid(row=2, column=0, sticky="ew", padx=8, pady=2)

        # Results
        self._section(right, "Simulation Results", row=3)

        nb_wrap = tk.Frame(right, bg=BG_PANEL)
        nb_wrap.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0,6))
        nb_wrap.columnconfigure(0, weight=1)
        nb_wrap.rowconfigure(0, weight=1)

        s = ttk.Style()
        s.configure("Dark.TNotebook", background=BG_PANEL, tabmargins=0)
        s.configure("Dark.TNotebook.Tab", background=BG_CARD, foreground=TEXT_SEC,
                    font=FS, padding=(10,5))
        s.map("Dark.TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG_DARK)])

        self.nb = ttk.Notebook(nb_wrap, style="Dark.TNotebook")
        self.nb.grid(row=0, column=0, sticky="nsew")

        # Tab 1 — Metrics
        t1 = tk.Frame(self.nb, bg=BG_PANEL)
        self.nb.add(t1, text=" 📊 Metrics Table ")
        t1.columnconfigure(0, weight=1)
        t1.rowconfigure(0, weight=1)

        self.metrics_table = MetricsTable(t1)
        self.metrics_table.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # average cards
        avg_row = tk.Frame(t1, bg=BG_MID)
        avg_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0,4))
        self.avg_lbl = {}
        for key, label, color in [("avg_wt","Avg Waiting",ACCENT),
                                   ("avg_tat","Avg Turnaround",ACCENT3),
                                   ("avg_rt","Avg Response",ACCENT2)]:
            card = tk.Frame(avg_row, bg=BG_CARD, padx=14, pady=8)
            card.pack(side="left", padx=6, pady=6)
            tk.Label(card, text=label, font=FS, fg=TEXT_SEC, bg=BG_CARD).pack()
            lbl = tk.Label(card, text="—", font=("Segoe UI",14,"bold"),
                           fg=color, bg=BG_CARD)
            lbl.pack()
            self.avg_lbl[key] = lbl

        b_exp = tk.Button(t1, text="💾 Export CSV", command=self._export)
        _btn(b_exp, False)
        b_exp.grid(row=2, column=0, sticky="e", padx=8, pady=(0,6))

        # Tab 2 — Compare
        t2 = tk.Frame(self.nb, bg=BG_PANEL)
        self.nb.add(t2, text=" ⚖  Compare All ")
        t2.columnconfigure(0, weight=1)
        t2.rowconfigure(0, weight=1)
        self._build_compare(t2)

        # Tab 3 — Gantt text
        t3 = tk.Frame(self.nb, bg=BG_PANEL)
        self.nb.add(t3, text=" 📋 Gantt Text ")
        t3.columnconfigure(0, weight=1)
        t3.rowconfigure(0, weight=1)
        self.gantt_text = tk.Text(t3, font=FMS, bg=BG_CARD, fg=ACCENT,
                                   wrap="none", relief="flat",
                                   insertbackground=ACCENT, state="disabled")
        gs = ttk.Scrollbar(t3, orient="vertical",   command=self.gantt_text.yview)
        gh = ttk.Scrollbar(t3, orient="horizontal",  command=self.gantt_text.xview)
        self.gantt_text.configure(yscrollcommand=gs.set, xscrollcommand=gh.set)
        self.gantt_text.grid(row=0, column=0, sticky="nsew")
        gs.grid(row=0, column=1, sticky="ns")
        gh.grid(row=1, column=0, sticky="ew")

    def _build_compare(self, parent):
        s = ttk.Style()
        s.configure("Cmp.Treeview",
                    background=BG_CARD, foreground=TEXT_PRI,
                    fieldbackground=BG_CARD, rowheight=26, font=FMS)
        s.configure("Cmp.Treeview.Heading",
                    background=BG_MID, foreground=ACCENT3,
                    font=("Segoe UI",9,"bold"), relief="flat")
        s.map("Cmp.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG_DARK)])

        cols = ("Algorithm","Avg Waiting","Avg Turnaround","Avg Response")
        self.cmp = ttk.Treeview(parent, columns=cols, show="headings",
                                 style="Cmp.Treeview", height=7)
        for col, w in zip(cols, [140,110,130,120]):
            self.cmp.heading(col, text=col)
            self.cmp.column(col, width=w, anchor="center")
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.cmp.yview)
        self.cmp.configure(yscrollcommand=vsb.set)
        self.cmp.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        vsb.grid(row=0, column=1, sticky="ns", pady=4)
        self.cmp_hint = tk.Label(parent,
            text='Click "⚡ Run All Algorithms" to populate the comparison.',
            font=FS, fg=TEXT_DIM, bg=BG_PANEL)
        self.cmp_hint.grid(row=1, column=0, columnspan=2, pady=4)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _on_algo(self, _=None):
        a = self.algo_var.get()
        self.e_quantum.configure(state="normal"   if a == "Round Robin" else "disabled")
        self.e_mlfq.configure(  state="normal"   if a == "MLFQ"         else "disabled")
        self.e_aging.configure( state="normal"   if a == "MLFQ"         else "disabled")

    def _add(self):
        pid = self.e_pid.get().strip()
        try:
            arr = int(self.e_arr.get())
            bst = int(self.e_bst.get())
        except ValueError:
            messagebox.showerror("Input Error", "Arrival and Burst must be integers.")
            return
        if not pid:
            messagebox.showerror("Input Error", "PID cannot be empty.")
            return
        if bst <= 0:
            messagebox.showerror("Input Error", "Burst time must be > 0.")
            return
        if arr < 0:
            messagebox.showerror("Input Error", "Arrival time must be ≥ 0.")
            return
        existing = [p.pid for p in self.proc_table.get_processes()]
        if pid in existing:
            messagebox.showerror("Duplicate", f'PID "{pid}" already exists.')
            return
        self.proc_table.add(pid, arr, bst)
        # suggest next PID
        nums = [int(p[1:]) for p in existing + [pid] if len(p) > 1 and p[1:].isdigit()]
        nxt  = max(nums, default=0) + 1
        self.e_pid.delete(0, "end"); self.e_pid.insert(0, f"P{nxt}")

    def _delete(self):
        self.proc_table.delete_selected()

    def _clear(self):
        if messagebox.askyesno("Clear", "Remove all processes?"):
            self.proc_table.clear()
            self._cache.clear()

    def _load_sample(self):
        self.proc_table.clear()
        for pid, arr, bst in [("P1",0,5),("P2",1,3),("P3",2,8),("P4",3,6)]:
            self.proc_table.add(pid, arr, bst)
        self.e_pid.delete(0,"end"); self.e_pid.insert(0,"P5")

    def _load_file(self):
        fp = filedialog.askopenfilename(
            title="Load Processes",
            filetypes=[("CSV","*.csv"),("JSON","*.json"),("All","*.*")])
        if not fp:
            return
        try:
            procs = load_file(fp)
            self.proc_table.clear()
            for p in procs:
                self.proc_table.add(p.pid, p.arrival_time, p.burst_time)
            messagebox.showinfo("Loaded", f"Loaded {len(procs)} processes.")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _get_cfg(self):
        a = self.algo_var.get()
        try:
            quantum = int(self.e_quantum.get()) if a == "Round Robin" else 2
            aging   = int(self.e_aging.get())   if a == "MLFQ"        else 10
            if a == "MLFQ":
                parts = self.e_mlfq.get().split(",")
                mlfq_q = [int(x.strip()) for x in parts] + [None]
            else:
                mlfq_q = [2, 4, None]
            if quantum <= 0: raise ValueError("Quantum must be > 0")
            if aging   <= 0: raise ValueError("Aging must be > 0")
        except ValueError as e:
            messagebox.showerror("Config Error", str(e))
            return None
        return quantum, mlfq_q, aging

    def _execute(self, algo, procs, quantum, mlfq_q, aging):
        if algo == "FCFS":         return fcfs(procs)
        if algo == "SJF":          return sjf(procs)
        if algo == "SRT":          return srt(procs)
        if algo == "Round Robin":  return round_robin(procs, quantum)
        if algo == "MLFQ":         return mlfq(procs, mlfq_q, aging)
        raise ValueError(f"Unknown: {algo}")

    def _run(self):
        procs = self.proc_table.get_processes()
        if not procs:
            messagebox.showwarning("No Processes", "Add at least one process first.")
            return
        cfg = self._get_cfg()
        if cfg is None:
            return
        quantum, mlfq_q, aging = cfg
        algo = self.algo_var.get()
        try:
            result, gantt = self._execute(algo, procs, quantum, mlfq_q, aging)
        except Exception as e:
            messagebox.showerror("Simulation Error", str(e))
            return
        metrics = compute_metrics(result)
        self._cache[algo] = (result, gantt, metrics)
        self._display(algo, gantt, metrics)

    def _run_all(self):
        procs = self.proc_table.get_processes()
        if not procs:
            messagebox.showwarning("No Processes", "Add at least one process first.")
            return
        cfg = self._get_cfg()
        if cfg is None:
            return
        quantum, mlfq_q, aging = cfg
        for algo in self.ALGOS:
            try:
                result, gantt = self._execute(algo, procs, quantum, mlfq_q, aging)
                self._cache[algo] = (result, gantt, compute_metrics(result))
            except Exception as e:
                print(f"[WARN] {algo}: {e}")
        # show last result
        last = self.ALGOS[-1]
        if last in self._cache:
            _, g, m = self._cache[last]
            self._display(last, g, m)
        self._update_compare()
        self.nb.select(1)

    def _display(self, algo, gantt, metrics):
        # 1. Gantt chart
        self.gantt.draw(gantt)
        # 2. Metrics table  ← force full refresh
        self.metrics_table.clear()
        self.metrics_table.populate(metrics)
        # 3. Average cards
        for key in ("avg_wt", "avg_tat", "avg_rt"):
            self.avg_lbl[key].configure(text=f"{metrics[key]:.2f}")
        # 4. Text gantt
        self._render_text(algo, gantt, metrics)
        # 5. Switch to metrics tab
        self.nb.select(0)
        self.update_idletasks()

    def _render_text(self, algo, gantt, metrics):
        self.gantt_text.configure(state="normal")
        self.gantt_text.delete("1.0", "end")
        lines = [f"Algorithm: {algo}", "=" * 58]
        top = ""; bot = ""
        for pid, s, e in gantt:
            lbl = pid if pid != "IDLE" else "···"
            w   = max((e - s) * 4, len(lbl) + 2)
            top += f"|{lbl.center(w)}"
            bot += f"{str(s):<{w+1}}"
        top += "|"
        bot += str(gantt[-1][2])
        lines += [top, bot, "",
                  f"{'PID':<6} {'Arrival':>7} {'Burst':>6} {'Wait':>6} {'TAT':>6} {'RT':>6}",
                  "-" * 42]
        for r in metrics["rows"]:
            lines.append(f"{r['pid']:<6} {r['arrival']:>7} {r['burst']:>6} "
                         f"{r['waiting']:>6} {r['turnaround']:>6} {r['response']:>6}")
        lines += ["-" * 42,
                  f"{'Avg':<6} {'':>7} {'':>6} "
                  f"{metrics['avg_wt']:>6.2f} {metrics['avg_tat']:>6.2f} {metrics['avg_rt']:>6.2f}"]
        self.gantt_text.insert("end", "\n".join(lines))
        self.gantt_text.configure(state="disabled")

    def _update_compare(self):
        self.cmp.delete(*self.cmp.get_children())
        rows = [(a, *( (m["avg_wt"], m["avg_tat"], m["avg_rt"])
                       for _, _, m in [self._cache[a]] ))
                for a in self.ALGOS if a in self._cache]
        if not rows:
            return
        best_wt  = min(r[1] for r in rows)
        best_tat = min(r[2] for r in rows)
        best_rt  = min(r[3] for r in rows)
        for algo, wt, tat, rt in rows:
            tag = "best" if wt == best_wt or tat == best_tat or rt == best_rt else ""
            self.cmp.insert("", "end",
                            values=(algo, f"{wt:.2f}", f"{tat:.2f}", f"{rt:.2f}"),
                            tags=(tag,))
        self.cmp.tag_configure("best", foreground=ACCENT3)
        self.cmp_hint.configure(
            text="★ Highlighted = best (lowest) value in at least one metric.")

    def _export(self):
        algo = self.algo_var.get()
        if algo not in self._cache:
            messagebox.showwarning("No Results", "Run the simulation first.")
            return
        _, _, metrics = self._cache[algo]
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile=f"{algo}_results.csv")
        if fp:
            export_results_csv(fp, metrics, algo)
            messagebox.showinfo("Exported", f"Saved to:\n{fp}")


if __name__ == "__main__":
    App().mainloop()
