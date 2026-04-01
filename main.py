"""
CPU Scheduling Simulator — Tkinter GUI
Run:  python main.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from algorithms import Process, fcfs, sjf, srt, round_robin, mlfq, compute_metrics
from gantt      import GanttFrame
from file_io    import load_file, export_results_csv

# ─── colours ────────────────────────────────────────────────────────────────
C = dict(
    bg_dark  = "#0F0F1A",
    bg_mid   = "#1A1A2E",
    bg_panel = "#16213E",
    bg_card  = "#1E2A45",
    accent   = "#4ECDC4",
    gold     = "#FFE66D",
    red      = "#FF6B6B",
    txt      = "#F0F0FF",
    dim      = "#A0A8C0",
    sep      = "#2A3050",
)

def btn(widget, primary=True):
    bg = C["accent"] if primary else C["bg_card"]
    fg = C["bg_dark"] if primary else C["txt"]
    widget.configure(bg=bg, fg=fg, relief="flat", bd=0, cursor="hand2",
                     activebackground="#3ABDB5", activeforeground=C["bg_dark"],
                     font=("Segoe UI",10), padx=10, pady=6)

def entry(parent, w=7, val=""):
    e = tk.Entry(parent, width=w, font=("Consolas",10),
                 bg=C["bg_card"], fg=C["txt"], insertbackground=C["accent"],
                 relief="flat", highlightthickness=1,
                 highlightcolor=C["accent"], highlightbackground=C["sep"])
    if val: e.insert(0, val)
    return e

def label(parent, text, fg=None, font=("Segoe UI",9)):
    return tk.Label(parent, text=text, font=font,
                    fg=fg or C["dim"], bg=parent["bg"])

# ─── Process table (input) ───────────────────────────────────────────────────
class ProcTable(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_panel"])
        self._build()

    def _build(self):
        # Use plain tk.Listbox-style layout with a real ttk.Treeview
        # Force theme so colours work on Windows too
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("P.Treeview",
            background=C["bg_card"], foreground=C["txt"],
            fieldbackground=C["bg_card"], rowheight=28,
            font=("Consolas",10))
        style.configure("P.Treeview.Heading",
            background=C["bg_mid"], foreground=C["accent"],
            font=("Segoe UI",10,"bold"), relief="flat")
        style.map("P.Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["bg_dark"])])

        cols = ("PID","Arrival","Burst")
        self.tv = ttk.Treeview(self, columns=cols, show="headings",
                                style="P.Treeview", height=8, selectmode="browse")
        for col, w in zip(cols, [80,100,100]):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="center", minwidth=50)

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def add(self, pid, arr, bst):
        self.tv.insert("", "end", values=(pid, int(arr), int(bst)))

    def delete_sel(self):
        for s in self.tv.selection(): self.tv.delete(s)

    def clear(self):
        self.tv.delete(*self.tv.get_children())

    def get_processes(self):
        out = []
        for iid in self.tv.get_children():
            v = self.tv.item(iid, "values")
            out.append(Process(str(v[0]), int(v[1]), int(v[2])))
        return out


# ─── Metrics table (output) ─────────────────────────────────────────────────
class MetTable(tk.Frame):
    COLS = ("PID","Arrival","Burst","Start","Finish","Waiting","Turnaround","Response")
    WIDTHS = (55, 65, 65, 65, 65, 70, 90, 80)

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_panel"])
        self._build()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("M.Treeview",
            background=C["bg_card"], foreground=C["txt"],
            fieldbackground=C["bg_card"], rowheight=26,
            font=("Consolas",9))
        style.configure("M.Treeview.Heading",
            background=C["bg_mid"], foreground=C["gold"],
            font=("Segoe UI",9,"bold"), relief="flat")
        style.map("M.Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["bg_dark"])])

        self.tv = ttk.Treeview(self, columns=self.COLS, show="headings",
                                style="M.Treeview", height=6)
        for col, w in zip(self.COLS, self.WIDTHS):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="center", minwidth=40)

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def populate(self, metrics):
        # clear
        self.tv.delete(*self.tv.get_children())
        # insert
        for r in metrics["rows"]:
            self.tv.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"],
                r["start"], r["finish"],
                r["waiting"], r["turnaround"], r["response"]
            ))
        self.tv.update()


# ─── Compare table ───────────────────────────────────────────────────────────
class CmpTable(tk.Frame):
    COLS = ("Algorithm","Avg Waiting","Avg Turnaround","Avg Response")

    def __init__(self, parent):
        super().__init__(parent, bg=C["bg_panel"])
        self._build()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("C.Treeview",
            background=C["bg_card"], foreground=C["txt"],
            fieldbackground=C["bg_card"], rowheight=26,
            font=("Consolas",9))
        style.configure("C.Treeview.Heading",
            background=C["bg_mid"], foreground=C["gold"],
            font=("Segoe UI",9,"bold"), relief="flat")
        style.map("C.Treeview",
            background=[("selected", C["accent"])],
            foreground=[("selected", C["bg_dark"])])

        self.tv = ttk.Treeview(self, columns=self.COLS, show="headings",
                                style="C.Treeview", height=7)
        for col, w in zip(self.COLS, [140,110,130,120]):
            self.tv.heading(col, text=col)
            self.tv.column(col, width=w, anchor="center")

        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

    def refresh(self, cache):
        self.tv.delete(*self.tv.get_children())
        algos = ["FCFS","SJF","SRT","Round Robin","MLFQ"]
        rows = [(a, cache[a][2]) for a in algos if a in cache]
        if not rows: return
        bwt  = min(m["avg_wt"]  for _,m in rows)
        btat = min(m["avg_tat"] for _,m in rows)
        brt  = min(m["avg_rt"]  for _,m in rows)
        for algo, m in rows:
            tag = "best" if m["avg_wt"]==bwt or m["avg_tat"]==btat or m["avg_rt"]==brt else ""
            self.tv.insert("", "end", tags=(tag,),
                values=(algo, f"{m['avg_wt']:.2f}",
                        f"{m['avg_tat']:.2f}", f"{m['avg_rt']:.2f}"))
        self.tv.tag_configure("best", foreground=C["gold"])


# ─── Main App ────────────────────────────────────────────────────────────────
class App(tk.Tk):
    ALGOS = ["FCFS","SJF","SRT","Round Robin","MLFQ"]

    def __init__(self):
        super().__init__()
        self.title("CPU Scheduling Simulator")
        self.geometry("1180x830")
        self.minsize(900, 660)
        self.configure(bg=C["bg_dark"])
        self._cache = {}
        self._build()
        self._load_sample()
        self.after(300, self._run)

    # ── layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # header
        hdr = tk.Frame(self, bg=C["bg_mid"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  CPU Scheduling Simulator",
                 font=("Segoe UI",20,"bold"), fg=C["accent"],
                 bg=C["bg_mid"]).pack(side="left", padx=20)
        tk.Label(hdr, text="OS Project — Python / Tkinter",
                 font=("Segoe UI",9), fg=C["dim"],
                 bg=C["bg_mid"]).pack(side="left", padx=6)

        # two-column body
        body = tk.Frame(self, bg=C["bg_dark"])
        body.pack(fill="both", expand=True, padx=12, pady=(6,10))
        body.columnconfigure(0, weight=0, minsize=295)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._left(body)
        self._right(body)

    def _sec(self, parent, title, row):
        f = tk.Frame(parent, bg=C["bg_panel"])
        f.grid(row=row, column=0, sticky="ew", padx=10, pady=(10,2))
        tk.Label(f, text=title, font=("Segoe UI",13,"bold"),
                 fg=C["accent"], bg=C["bg_panel"]).pack(side="left")
        tk.Frame(f, bg=C["sep"], height=1).pack(side="left", fill="x",
                                                  expand=True, padx=8)

    def _left(self, parent):
        L = tk.Frame(parent, bg=C["bg_panel"])
        L.grid(row=0, column=0, sticky="nsew", padx=(0,10), pady=4)
        L.columnconfigure(0, weight=1)

        # ── Process Input ────────────────────
        self._sec(L, "Process Input", 0)

        ef = tk.Frame(L, bg=C["bg_panel"])
        ef.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        label(ef, "PID").grid(row=0, column=0, padx=(4,2))
        label(ef, "Arrival").grid(row=0, column=2, padx=(4,2))
        label(ef, "Burst").grid(row=0, column=4, padx=(4,2))
        self.e_pid = entry(ef, 6, "P1")
        self.e_arr = entry(ef, 5, "0")
        self.e_bst = entry(ef, 5, "5")
        self.e_pid.grid(row=0, column=1, padx=(0,4))
        self.e_arr.grid(row=0, column=3, padx=(0,4))
        self.e_bst.grid(row=0, column=5, padx=(0,4))
        for e in (self.e_pid, self.e_arr, self.e_bst):
            e.bind("<Return>", lambda _: self._add())

        br = tk.Frame(L, bg=C["bg_panel"])
        br.grid(row=2, column=0, sticky="ew", padx=10, pady=(2,6))
        b1 = tk.Button(br, text="＋ Add",   command=self._add)
        b2 = tk.Button(br, text="✕ Delete", command=self._del)
        b3 = tk.Button(br, text="⟳ Clear",  command=self._clr)
        btn(b1); btn(b2,False); btn(b3,False)
        b1.pack(side="left",padx=(0,6))
        b2.pack(side="left",padx=(0,6))
        b3.pack(side="left")

        self.ptable = ProcTable(L)
        self.ptable.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0,6))
        L.rowconfigure(3, weight=1)

        fr = tk.Frame(L, bg=C["bg_panel"])
        fr.grid(row=4, column=0, sticky="ew", padx=10, pady=(0,8))
        b4 = tk.Button(fr, text="📂 Load File",   command=self._load_file)
        b5 = tk.Button(fr, text="📋 Sample Data", command=self._load_sample)
        btn(b4,False); btn(b5,False)
        b4.pack(side="left",padx=(0,6)); b5.pack(side="left")

        tk.Frame(L, bg=C["sep"], height=1).grid(row=5, column=0,
                                                 sticky="ew", padx=8)

        # ── Algorithm Settings ────────────────
        self._sec(L, "Algorithm Settings", 6)

        cfg = tk.Frame(L, bg=C["bg_panel"])
        cfg.grid(row=7, column=0, sticky="ew", padx=10, pady=4)
        cfg.columnconfigure(1, weight=1)

        for row_i, lbl_text in enumerate(["Algorithm:","RR Quantum:","MLFQ (q1,q2):","MLFQ Aging:"]):
            label(cfg, lbl_text).grid(row=row_i, column=0, sticky="w", pady=3)

        self.v_algo = tk.StringVar(value="FCFS")
        self.combo  = ttk.Combobox(cfg, textvariable=self.v_algo,
                                    values=self.ALGOS, state="readonly",
                                    font=("Segoe UI",10), width=16)
        self.combo.grid(row=0, column=1, sticky="ew", padx=(8,0), pady=3)
        self.combo.bind("<<ComboboxSelected>>", self._on_algo)

        self.e_q   = entry(cfg, 6, "2")
        self.e_mq  = entry(cfg, 8, "2,4")
        self.e_age = entry(cfg, 6, "10")
        self.e_q.grid(  row=1, column=1, sticky="w", padx=(8,0), pady=3)
        self.e_mq.grid( row=2, column=1, sticky="w", padx=(8,0), pady=3)
        self.e_age.grid(row=3, column=1, sticky="w", padx=(8,0), pady=3)
        self._on_algo()

        b_run = tk.Button(L, text="▶  RUN SIMULATION", command=self._run)
        btn(b_run); b_run.configure(font=("Segoe UI",11,"bold"), pady=10)
        b_run.grid(row=8, column=0, sticky="ew", padx=10, pady=8)

        b_all = tk.Button(L, text="⚡ Run All Algorithms", command=self._run_all)
        btn(b_all, False)
        b_all.grid(row=9, column=0, sticky="ew", padx=10, pady=(0,8))

    def _right(self, parent):
        R = tk.Frame(parent, bg=C["bg_panel"])
        R.grid(row=0, column=1, sticky="nsew", pady=4)
        R.columnconfigure(0, weight=1)
        R.rowconfigure(4, weight=1)

        # Gantt
        self._sec(R, "Gantt Chart", 0)
        self.gantt = GanttFrame(R)
        self.gantt.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,4))

        tk.Frame(R, bg=C["sep"], height=1).grid(row=2, column=0,
                                                  sticky="ew", padx=8, pady=2)
        self._sec(R, "Simulation Results", 3)

        # notebook
        nb_wrap = tk.Frame(R, bg=C["bg_panel"])
        nb_wrap.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0,6))
        nb_wrap.columnconfigure(0, weight=1)
        nb_wrap.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("N.TNotebook", background=C["bg_panel"], tabmargins=0)
        style.configure("N.TNotebook.Tab", background=C["bg_card"],
                        foreground=C["dim"], font=("Segoe UI",9), padding=(10,5))
        style.map("N.TNotebook.Tab",
                  background=[("selected", C["accent"])],
                  foreground=[("selected", C["bg_dark"])])

        self.nb = ttk.Notebook(nb_wrap, style="N.TNotebook")
        self.nb.grid(row=0, column=0, sticky="nsew")

        # Tab 1 — Metrics
        t1 = tk.Frame(self.nb, bg=C["bg_panel"])
        self.nb.add(t1, text=" 📊 Metrics Table ")
        t1.columnconfigure(0, weight=1)
        t1.rowconfigure(0, weight=1)

        self.mtable = MetTable(t1)
        self.mtable.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        avg_row = tk.Frame(t1, bg=C["bg_mid"])
        avg_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0,4))
        self.avg = {}
        for key, lbl_text, color in [
            ("avg_wt","Avg Waiting", C["accent"]),
            ("avg_tat","Avg Turnaround", C["gold"]),
            ("avg_rt","Avg Response",  C["red"]),
        ]:
            card = tk.Frame(avg_row, bg=C["bg_card"], padx=14, pady=8)
            card.pack(side="left", padx=6, pady=6)
            tk.Label(card, text=lbl_text, font=("Segoe UI",9),
                     fg=C["dim"], bg=C["bg_card"]).pack()
            v = tk.Label(card, text="—", font=("Segoe UI",14,"bold"),
                         fg=color, bg=C["bg_card"])
            v.pack(); self.avg[key] = v

        b_exp = tk.Button(t1, text="💾 Export CSV", command=self._export)
        btn(b_exp, False)
        b_exp.grid(row=2, column=0, sticky="e", padx=8, pady=(0,6))

        # Tab 2 — Compare
        t2 = tk.Frame(self.nb, bg=C["bg_panel"])
        self.nb.add(t2, text=" ⚖  Compare All ")
        t2.columnconfigure(0, weight=1)
        t2.rowconfigure(0, weight=1)
        self.cmptable = CmpTable(t2)
        self.cmptable.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.cmp_hint = label(t2,
            'Click "⚡ Run All Algorithms" to populate comparison.',
            fg=C["dim"])
        self.cmp_hint.grid(row=1, column=0, pady=4)

        # Tab 3 — Text Gantt
        t3 = tk.Frame(self.nb, bg=C["bg_panel"])
        self.nb.add(t3, text=" 📋 Gantt Text ")
        t3.columnconfigure(0, weight=1)
        t3.rowconfigure(0, weight=1)
        self.gtxt = tk.Text(t3, font=("Consolas",9), bg=C["bg_card"],
                             fg=C["accent"], wrap="none", relief="flat",
                             state="disabled")
        gs = ttk.Scrollbar(t3, orient="vertical",   command=self.gtxt.yview)
        gh = ttk.Scrollbar(t3, orient="horizontal",  command=self.gtxt.xview)
        self.gtxt.configure(yscrollcommand=gs.set, xscrollcommand=gh.set)
        self.gtxt.grid(row=0, column=0, sticky="nsew")
        gs.grid(row=0, column=1, sticky="ns")
        gh.grid(row=1, column=0, sticky="ew")

    # ── event handlers ────────────────────────────────────────────────────────
    def _on_algo(self, _=None):
        a = self.v_algo.get()
        self.e_q.configure(  state="normal" if a=="Round Robin" else "disabled")
        self.e_mq.configure( state="normal" if a=="MLFQ"        else "disabled")
        self.e_age.configure(state="normal" if a=="MLFQ"        else "disabled")

    def _add(self):
        pid = self.e_pid.get().strip()
        try:
            arr = int(self.e_arr.get())
            bst = int(self.e_bst.get())
        except ValueError:
            messagebox.showerror("Error","Arrival and Burst must be integers.")
            return
        if not pid:
            messagebox.showerror("Error","PID cannot be empty."); return
        if bst <= 0:
            messagebox.showerror("Error","Burst must be > 0."); return
        if arr < 0:
            messagebox.showerror("Error","Arrival must be ≥ 0."); return
        existing = [p.pid for p in self.ptable.get_processes()]
        if pid in existing:
            messagebox.showerror("Duplicate",f'PID "{pid}" already exists.'); return
        self.ptable.add(pid, arr, bst)
        nums = [int(p[1:]) for p in existing+[pid] if len(p)>1 and p[1:].isdigit()]
        nxt  = max(nums, default=0) + 1
        self.e_pid.delete(0,"end"); self.e_pid.insert(0,f"P{nxt}")

    def _del(self): self.ptable.delete_sel()

    def _clr(self):
        if messagebox.askyesno("Clear","Remove all processes?"):
            self.ptable.clear(); self._cache.clear()

    def _load_sample(self):
        self.ptable.clear()
        for pid,arr,bst in [("P1",0,5),("P2",1,3),("P3",2,8),("P4",3,6)]:
            self.ptable.add(pid,arr,bst)
        self.e_pid.delete(0,"end"); self.e_pid.insert(0,"P5")

    def _load_file(self):
        fp = filedialog.askopenfilename(
            title="Load Processes",
            filetypes=[("CSV","*.csv"),("JSON","*.json"),("All","*.*")])
        if not fp: return
        try:
            procs = load_file(fp)
            self.ptable.clear()
            for p in procs: self.ptable.add(p.pid,p.arrival_time,p.burst_time)
            messagebox.showinfo("Loaded",f"Loaded {len(procs)} processes.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cfg(self):
        a = self.v_algo.get()
        try:
            q   = int(self.e_q.get())   if a=="Round Robin" else 2
            age = int(self.e_age.get()) if a=="MLFQ"        else 10
            mq  = [int(x.strip()) for x in self.e_mq.get().split(",")] + [None] \
                  if a=="MLFQ" else [2,4,None]
            if q   <= 0: raise ValueError("Quantum must be > 0")
            if age <= 0: raise ValueError("Aging must be > 0")
        except ValueError as e:
            messagebox.showerror("Config Error", str(e)); return None
        return q, mq, age

    def _exec(self, algo, procs, q, mq, age):
        if algo=="FCFS":        return fcfs(procs)
        if algo=="SJF":         return sjf(procs)
        if algo=="SRT":         return srt(procs)
        if algo=="Round Robin": return round_robin(procs, q)
        if algo=="MLFQ":        return mlfq(procs, mq, age)
        raise ValueError(f"Unknown algorithm: {algo}")

    def _run(self):
        procs = self.ptable.get_processes()
        if not procs:
            messagebox.showwarning("No Processes","Add at least one process."); return
        cfg = self._cfg()
        if cfg is None: return
        q, mq, age = cfg
        algo = self.v_algo.get()
        try:
            result, gantt = self._exec(algo, procs, q, mq, age)
        except Exception as e:
            messagebox.showerror("Simulation Error", str(e)); return
        m = compute_metrics(result)
        self._cache[algo] = (result, gantt, m)
        self._show(algo, gantt, m)

    def _run_all(self):
        procs = self.ptable.get_processes()
        if not procs:
            messagebox.showwarning("No Processes","Add at least one process."); return
        cfg = self._cfg()
        if cfg is None: return
        q, mq, age = cfg
        for algo in self.ALGOS:
            try:
                result, gantt = self._exec(algo, procs, q, mq, age)
                self._cache[algo] = (result, gantt, compute_metrics(result))
            except Exception as e:
                print(f"[WARN] {algo}: {e}")
        # show last result
        last = self.ALGOS[-1]
        if last in self._cache:
            _, g, m = self._cache[last]
            self._show(last, g, m)
        self.cmptable.refresh(self._cache)
        self.cmp_hint.configure(
            text="★ Highlighted = best (lowest) in at least one metric.")
        self.nb.select(1)

    def _show(self, algo, gantt, metrics):
        # 1. Gantt chart
        self.gantt.draw(gantt)
        # 2. Metrics table — delete then reinsert
        self.mtable.tv.delete(*self.mtable.tv.get_children())
        for r in metrics["rows"]:
            self.mtable.tv.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"],
                r["start"], r["finish"],
                r["waiting"], r["turnaround"], r["response"]
            ))
        # 3. Average cards
        self.avg["avg_wt"].configure( text=f"{metrics['avg_wt']:.2f}")
        self.avg["avg_tat"].configure(text=f"{metrics['avg_tat']:.2f}")
        self.avg["avg_rt"].configure( text=f"{metrics['avg_rt']:.2f}")
        # 4. Text gantt
        self._txt(algo, gantt, metrics)
        # 5. Switch to metrics tab
        self.nb.select(0)
        self.update_idletasks()

    def _txt(self, algo, gantt, metrics):
        self.gtxt.configure(state="normal")
        self.gtxt.delete("1.0","end")
        top = bar = ""
        for pid,s,e in gantt:
            lbl = pid if pid!="IDLE" else "···"
            w   = max((e-s)*4, len(lbl)+2)
            top += f"|{lbl.center(w)}"
            bar += f"{str(s):<{w+1}}"
        top += "|"; bar += str(gantt[-1][2])
        lines = [f"Algorithm: {algo}", "="*56, top, bar, "",
                 f"{'PID':<6}{'Arrival':>8}{'Burst':>7}{'Wait':>7}{'TAT':>7}{'RT':>7}",
                 "-"*44]
        for r in metrics["rows"]:
            lines.append(f"{r['pid']:<6}{r['arrival']:>8}{r['burst']:>7}"
                         f"{r['waiting']:>7}{r['turnaround']:>7}{r['response']:>7}")
        lines += ["-"*44,
                  f"{'Avg':<6}{'':>8}{'':>7}"
                  f"{metrics['avg_wt']:>7.2f}{metrics['avg_tat']:>7.2f}{metrics['avg_rt']:>7.2f}"]
        self.gtxt.insert("end", "\n".join(lines))
        self.gtxt.configure(state="disabled")

    def _export(self):
        algo = self.v_algo.get()
        if algo not in self._cache:
            messagebox.showwarning("No Results","Run simulation first."); return
        _, _, m = self._cache[algo]
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV","*.csv")],
            initialfile=f"{algo}_results.csv")
        if fp:
            export_results_csv(fp, m, algo)
            messagebox.showinfo("Exported",f"Saved to:\n{fp}")


if __name__ == "__main__":
    App().mainloop()