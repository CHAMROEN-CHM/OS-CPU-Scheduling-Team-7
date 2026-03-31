import tkinter as tk
from tkinter import ttk

from process import Process
from scheduler import fcfs, sjf, srt, rr
from metrics import calculate_metrics


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduling Simulator")
        self.root.geometry("1000x600")
        self.root.configure(bg="#0f172a")

        self.processes = []

        # ===== INPUT =====
        frame = tk.Frame(root, bg="#0f172a")
        frame.pack(pady=10)

        self.pid = tk.Entry(frame, width=5)
        self.at = tk.Entry(frame, width=5)
        self.bt = tk.Entry(frame, width=5)

        self.pid.grid(row=0, column=0)
        self.at.grid(row=0, column=1)
        self.bt.grid(row=0, column=2)

        tk.Button(frame, text="Add", command=self.add).grid(row=0, column=3)

        # ===== LIST =====
        self.listbox = tk.Listbox(root)
        self.listbox.pack()

        # ===== OPTIONS =====
        opt = tk.Frame(root, bg="#0f172a")
        opt.pack()

        self.algo = ttk.Combobox(opt, values=["FCFS","SJF","SRT","RR"])
        self.algo.set("FCFS")
        self.algo.grid(row=0, column=0)

        self.quantum = tk.Entry(opt, width=5)
        self.quantum.grid(row=0, column=1)

        tk.Button(opt, text="Run", command=self.run).grid(row=0, column=2)

        # ===== GANTT =====
        self.canvas = tk.Canvas(root, height=100, bg="#111827")
        self.canvas.pack(fill="x")

        # ===== TABLE =====
        cols = ("PID","AT","BT","Start","Finish","WT","TAT","RT")
        self.tree = ttk.Treeview(root, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=80)

        self.tree.pack(fill="both", expand=True)

    def add(self):
        p = Process(
            self.pid.get(),
            int(self.at.get()),
            int(self.bt.get())
        )
        self.processes.append(p)
        self.listbox.insert(tk.END, f"{p.pid} AT={p.arrival} BT={p.burst}")

    def run(self):
        for p in self.processes:
            p.reset()

        algo = self.algo.get()

        if algo == "FCFS":
            gantt = fcfs(self.processes)
        elif algo == "SJF":
            gantt = sjf(self.processes)
        elif algo == "SRT":
            gantt = srt(self.processes)
        else:
            gantt = rr(self.processes, int(self.quantum.get()))

        results, avg = calculate_metrics(self.processes)

        self.draw_gantt(gantt)
        self.fill_table(results)

    def draw_gantt(self, gantt):
        self.canvas.delete("all")

        x = 10
        scale = 30

        for pid, start, end in gantt:
            w = (end - start) * scale
            self.canvas.create_rectangle(x, 20, x+w, 60, fill="cyan")
            self.canvas.create_text(x+w/2, 40, text=pid)
            self.canvas.create_text(x, 70, text=str(start))
            x += w

        self.canvas.create_text(x, 70, text=str(gantt[-1][2]))

    def fill_table(self, results):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in results:
            self.tree.insert("", "end", values=r)


root = tk.Tk()
app = App(root)
root.mainloop()