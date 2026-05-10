import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

from models.hole import Hole
from models.process import Process
from models.segment import Segment
from memory.memory_manager import MemoryManager


# ─── Color palette ────────────────────────────────────────────────────────────
BG_DARK       = "#1e1e2e"
BG_PANEL      = "#252535"
BG_CARD       = "#2a2a3e"
BG_INPUT      = "#313145"
FG_PRIMARY    = "#e2e2f0"
FG_SECONDARY  = "#9090b0"
FG_MUTED      = "#5a5a7a"
ACCENT_BLUE   = "#6c8ee8"
ACCENT_GREEN  = "#5dbf8a"
ACCENT_AMBER  = "#e8b45a"
ACCENT_RED    = "#e86c6c"
ACCENT_PURPLE = "#a07ae8"
BORDER_COLOR  = "#3a3a55"

PROCESS_COLORS = [
    ("#6c8ee8", "#c8d6ff"),  # blue
    ("#5dbf8a", "#c2f0d8"),  # green
    ("#e8b45a", "#fce8c2"),  # amber
    ("#e86c8a", "#ffc2d0"),  # pink
    ("#a07ae8", "#ddd0ff"),  # purple
    ("#5bb8d4", "#c0eaf5"),  # cyan
    ("#e8876c", "#ffd4c8"),  # coral
    ("#7ae8b4", "#c2fff0"),  # teal
]
HOLE_COLOR    = ("#4a4a6a", "#9090b0")
UNUSED_COLOR  = ("#2a2a3e", "#5a5a7a")


def get_process_color(index):
    return PROCESS_COLORS[index % len(PROCESS_COLORS)]


# ─── Styled widget helpers ────────────────────────────────────────────────────
def styled_label(parent, text, size=11, color=FG_PRIMARY, bold=False, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, fg=color, bg=parent["bg"],
                    font=("Consolas", size, weight), **kw)


def styled_entry(parent, width=18, **kw):
    e = tk.Entry(parent, width=width, bg=BG_INPUT, fg=FG_PRIMARY,
                 insertbackground=FG_PRIMARY, relief="flat",
                 font=("Consolas", 10), highlightthickness=1,
                 highlightcolor=ACCENT_BLUE, highlightbackground=BORDER_COLOR, **kw)
    return e


def styled_button(parent, text, command, color=ACCENT_BLUE, fg="#ffffff",
                  width=None, padx=10, pady=5, **kw):
    btn = tk.Button(parent, text=text, command=command,
                    bg=color, fg=fg, activebackground=fg,
                    activeforeground=color, relief="flat",
                    font=("Consolas", 10, "bold"), cursor="hand2",
                    padx=padx, pady=pady, **kw)
    if width:
        btn.config(width=width)
    return btn


def styled_frame(parent, **kw):
    return tk.Frame(parent, bg=BG_CARD, relief="flat", **kw)


def card_frame(parent, title, **kw):
    outer = tk.Frame(parent, bg=BG_PANEL, padx=1, pady=1)
    inner = tk.Frame(outer, bg=BG_CARD, padx=12, pady=10)
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title.upper(), fg=FG_MUTED, bg=BG_CARD,
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 6))
    return outer, inner


def separator(parent):
    tk.Frame(parent, bg=BORDER_COLOR, height=1).pack(fill="x", pady=6)


# ─── Main Application ─────────────────────────────────────────────────────────
class MemoryAllocatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Memory Segmentation Allocator")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg=BG_DARK)

        self.manager = None
        self.total_memory = 0
        self.process_color_map = {}
        self.color_counter = 0
        self.operation_log = []
        self.hole_rows = []
        self.seg_rows = []

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Title bar
        title_bar = tk.Frame(self, bg=BG_PANEL, height=48)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="⬡  Memory Segmentation Allocator",
                 fg=ACCENT_BLUE, bg=BG_PANEL,
                 font=("Consolas", 14, "bold")).pack(side="left", padx=16, pady=10)
        styled_label(title_bar, "CSE 335s — Operating Systems",
                     color=FG_MUTED, size=10).pack(side="right", padx=16)

        # Body: sidebar + main
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        self.sidebar = tk.Frame(body, bg=BG_PANEL, width=330)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_area = tk.Frame(body, bg=BG_DARK)
        self.main_area.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        sb = self.sidebar
        canvas = tk.Canvas(sb, bg=BG_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(sb, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=BG_PANEL)
        self.scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_memory_setup(self.scroll_frame)
        self._build_holes_panel(self.scroll_frame)
        self._build_process_panel(self.scroll_frame)
        self._build_dealloc_panel(self.scroll_frame)

    def _build_memory_setup(self, parent):
        outer, f = card_frame(parent, "① memory setup")
        outer.pack(fill="x", padx=8, pady=(10, 4))

        styled_label(f, "Total memory size (K)", color=FG_SECONDARY).pack(anchor="w")
        self.total_mem_var = tk.StringVar(value="1000")
        e = styled_entry(f, textvariable=self.total_mem_var)
        e.pack(fill="x", pady=(3, 8))

        styled_button(f, "▶  Initialize Memory",
                      self._init_memory, color=ACCENT_BLUE, width=26).pack(fill="x")
        self.init_status = styled_label(f, "", color=FG_MUTED, size=9)
        self.init_status.pack(anchor="w", pady=(4, 0))

    def _build_holes_panel(self, parent):
        self.holes_outer, self.holes_frame = card_frame(parent, "② initial holes")
        self.holes_outer.pack(fill="x", padx=8, pady=4)

        # Column headers
        hdr = tk.Frame(self.holes_frame, bg=BG_CARD)
        hdr.pack(fill="x")
        for col, w in [("Start (K)", 9), ("Size (K)", 9), ("", 4)]:
            styled_label(hdr, col, color=FG_MUTED, size=9).pack(side="left", padx=(0, 4))

        self.holes_list_frame = tk.Frame(self.holes_frame, bg=BG_CARD)
        self.holes_list_frame.pack(fill="x", pady=(4, 6))

        btn_row = tk.Frame(self.holes_frame, bg=BG_CARD)
        btn_row.pack(fill="x")
        styled_button(btn_row, "+  Add Hole", self._add_hole_row,
                      color=BG_INPUT, fg=FG_PRIMARY).pack(side="left")
        styled_button(btn_row, "Apply Holes →", self._apply_holes,
                      color=ACCENT_GREEN).pack(side="right")

        self.holes_msg = styled_label(self.holes_frame, "", color=ACCENT_RED, size=9)
        self.holes_msg.pack(anchor="w", pady=(4, 0))

        # Add 3 default rows
        for _ in range(3):
            self._add_hole_row()

    def _add_hole_row(self):
        row = tk.Frame(self.holes_list_frame, bg=BG_CARD)
        row.pack(fill="x", pady=2)
        start_var = tk.StringVar()
        size_var = tk.StringVar()
        e1 = styled_entry(row, textvariable=start_var, width=8)
        e1.pack(side="left", padx=(0, 4))
        e2 = styled_entry(row, textvariable=size_var, width=8)
        e2.pack(side="left", padx=(0, 4))
        del_btn = styled_button(row, "✕", lambda r=row, d=(start_var, size_var, None): self._remove_hole_row(r, d),
                                color=ACCENT_RED, fg="#fff", padx=4, pady=2)
        del_btn.pack(side="left")
        entry = (start_var, size_var, row)
        del_btn.config(command=lambda r=row, e=entry: self._remove_hole_row(r, e))
        self.hole_rows.append(entry)

    def _remove_hole_row(self, row_frame, entry):
        if entry in self.hole_rows:
            self.hole_rows.remove(entry)
        row_frame.destroy()

    def _build_process_panel(self, parent):
        self.proc_outer, self.proc_frame = card_frame(parent, "③ add process")
        self.proc_outer.pack(fill="x", padx=8, pady=4)

        styled_label(self.proc_frame, "Process name", color=FG_SECONDARY).pack(anchor="w")
        self.proc_name_var = tk.StringVar()
        styled_entry(self.proc_frame, textvariable=self.proc_name_var).pack(fill="x", pady=(3, 8))

        styled_label(self.proc_frame, "Segments (Name + Size)", color=FG_SECONDARY).pack(anchor="w")

        hdr = tk.Frame(self.proc_frame, bg=BG_CARD)
        hdr.pack(fill="x")
        for col in ["Name", "Size (K)", ""]:
            styled_label(hdr, col, color=FG_MUTED, size=9).pack(side="left", padx=(0, 10))

        self.segs_list_frame = tk.Frame(self.proc_frame, bg=BG_CARD)
        self.segs_list_frame.pack(fill="x", pady=(4, 6))

        btn_row = tk.Frame(self.proc_frame, bg=BG_CARD)
        btn_row.pack(fill="x", pady=(0, 6))
        styled_button(btn_row, "+  Add Segment", self._add_seg_row,
                      color=BG_INPUT, fg=FG_PRIMARY).pack(side="left")

        separator(self.proc_frame)

        styled_label(self.proc_frame, "Allocation strategy", color=FG_SECONDARY).pack(anchor="w")
        self.strategy_var = tk.StringVar(value="first_fit")
        strat_frame = tk.Frame(self.proc_frame, bg=BG_CARD)
        strat_frame.pack(fill="x", pady=(3, 8))
        for text, val, color in [("First-Fit", "first_fit", ACCENT_BLUE),
                                  ("Best-Fit", "best_fit", ACCENT_PURPLE)]:
            rb = tk.Radiobutton(strat_frame, text=text, variable=self.strategy_var,
                                value=val, fg=color, bg=BG_CARD,
                                selectcolor=BG_INPUT, activebackground=BG_CARD,
                                activeforeground=color,
                                font=("Consolas", 10, "bold"))
            rb.pack(side="left", padx=(0, 14))

        styled_button(self.proc_frame, "▶  Allocate Process",
                      self._allocate_process, color=ACCENT_BLUE, width=26).pack(fill="x")
        self.proc_msg = styled_label(self.proc_frame, "", color=ACCENT_RED, size=9)
        self.proc_msg.pack(anchor="w", pady=(4, 0))

        for _ in range(2):
            self._add_seg_row()

    def _add_seg_row(self):
        row = tk.Frame(self.segs_list_frame, bg=BG_CARD)
        row.pack(fill="x", pady=2)
        name_var = tk.StringVar()
        size_var = tk.StringVar()
        e1 = styled_entry(row, textvariable=name_var, width=8)
        e1.pack(side="left", padx=(0, 4))
        e2 = styled_entry(row, textvariable=size_var, width=8)
        e2.pack(side="left", padx=(0, 4))
        del_btn = styled_button(row, "✕", lambda: None,
                                color=ACCENT_RED, fg="#fff", padx=4, pady=2)
        del_btn.pack(side="left")
        entry = (name_var, size_var, row)
        del_btn.config(command=lambda r=row, e=entry: self._remove_seg_row(r, e))
        self.seg_rows.append(entry)

    def _remove_seg_row(self, row_frame, entry):
        if entry in self.seg_rows:
            self.seg_rows.remove(entry)
        row_frame.destroy()

    def _build_dealloc_panel(self, parent):
        self.dealloc_outer, self.dealloc_frame = card_frame(parent, "④ deallocate process")
        self.dealloc_outer.pack(fill="x", padx=8, pady=(4, 10))

        styled_label(self.dealloc_frame, "Select process to remove",
                     color=FG_SECONDARY).pack(anchor="w")
        self.dealloc_var = tk.StringVar()
        self.dealloc_combo = ttk.Combobox(self.dealloc_frame, textvariable=self.dealloc_var,
                                          state="readonly", font=("Consolas", 10))
        self._style_combobox()
        self.dealloc_combo.pack(fill="x", pady=(4, 8))

        styled_button(self.dealloc_frame, "✕  Deallocate Process",
                      self._deallocate_process, color=ACCENT_RED, width=26).pack(fill="x")
        self.dealloc_msg = styled_label(self.dealloc_frame, "", color=ACCENT_GREEN, size=9)
        self.dealloc_msg.pack(anchor="w", pady=(4, 0))

    def _style_combobox(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT,
                        foreground=FG_PRIMARY, selectbackground=ACCENT_BLUE,
                        selectforeground="#ffffff", bordercolor=BORDER_COLOR,
                        lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR)

    # ── Main area ────────────────────────────────────────────────────────────
    def _build_main(self):
        ma = self.main_area

        # Top stats bar
        self.stats_bar = tk.Frame(ma, bg=BG_PANEL, height=36)
        self.stats_bar.pack(fill="x")
        self.stats_bar.pack_propagate(False)
        self.stats_label = styled_label(self.stats_bar, "No memory initialized",
                                        color=FG_SECONDARY, size=9)
        self.stats_label.pack(side="left", padx=12, pady=8)
        styled_button(self.stats_bar, "↺  Reset All", self._reset_all,
                      color=BG_INPUT, fg=FG_PRIMARY).pack(side="right", padx=8, pady=4)

        # Split: memory bar (left) + tables/log (right)
        content = tk.Frame(ma, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=8, pady=8)

        # Memory visualizer column
        left = tk.Frame(content, bg=BG_DARK, width=180)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        styled_label(left, "Memory Layout", color=FG_SECONDARY,
                     size=9, bold=True).pack(anchor="w", pady=(0, 4))

        # Canvas for memory bar
        self.mem_canvas = tk.Canvas(left, bg=BG_CARD, width=160,
                                    highlightthickness=1,
                                    highlightbackground=BORDER_COLOR)
        self.mem_canvas.pack(fill="both", expand=True)

        # Legend
        self.legend_frame = tk.Frame(left, bg=BG_DARK)
        self.legend_frame.pack(fill="x", pady=(6, 0))

        # Right column: tables + log
        right = tk.Frame(content, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        # Tables row
        tables_row = tk.Frame(right, bg=BG_DARK)
        tables_row.pack(fill="both", expand=True)

        # Allocated table
        alloc_outer, alloc_f = card_frame(tables_row, "Allocated partitions")
        alloc_outer.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.alloc_tree = self._make_tree(alloc_f,
            ("Process", "Segment", "Base (K)", "Limit (K)", "Size (K)"),
            (60, 70, 65, 70, 60))

        # Holes table
        holes_outer, holes_f = card_frame(tables_row, "Free partitions (holes)")
        holes_outer.pack(side="left", fill="both", expand=True)
        self.holes_tree = self._make_tree(holes_f,
            ("Hole", "Start (K)", "End (K)", "Size (K)"),
            (40, 65, 65, 65))

        separator(right)

        # Segment tables per process
        seg_outer, self.seg_tables_frame = card_frame(right, "Segment tables by process")
        seg_outer.pack(fill="both", expand=True, pady=(0, 4))

        # Log
        log_outer, log_f = card_frame(right, "Operation log")
        log_outer.pack(fill="x")
        self.log_text = tk.Text(log_f, height=5, bg=BG_INPUT, fg=FG_PRIMARY,
                                font=("Consolas", 9), relief="flat",
                                state="disabled", wrap="word")
        self.log_text.pack(fill="x")
        self.log_text.tag_config("ok",   foreground=ACCENT_GREEN)
        self.log_text.tag_config("fail", foreground=ACCENT_RED)
        self.log_text.tag_config("info", foreground=ACCENT_BLUE)
        self.log_text.tag_config("warn", foreground=ACCENT_AMBER)

    def _make_tree(self, parent, columns, widths):
        style = ttk.Style()
        style.configure("Dark.Treeview",
                         background=BG_CARD, foreground=FG_PRIMARY,
                         fieldbackground=BG_CARD, rowheight=22,
                         font=("Consolas", 9))
        style.configure("Dark.Treeview.Heading",
                         background=BG_INPUT, foreground=FG_SECONDARY,
                         font=("Consolas", 9, "bold"), relief="flat")
        style.map("Dark.Treeview",
                   background=[("selected", ACCENT_BLUE)],
                   foreground=[("selected", "#ffffff")])

        frame = tk.Frame(parent, bg=BG_CARD)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings",
                             style="Dark.Treeview", height=6)
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=w, anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    # ── Logic handlers ────────────────────────────────────────────────────────
    def _init_memory(self):
        try:
            total = int(self.total_mem_var.get())
            if total <= 0:
                raise ValueError
        except ValueError:
            self._show_msg(self.init_status, "Enter a valid positive integer", ACCENT_RED)
            return

        self.total_memory = total
        self.manager = MemoryManager(total)
        self.process_color_map = {}
        self.color_counter = 0
        self.operation_log = []

        self._show_msg(self.init_status, f"✓ {total}K memory initialized", ACCENT_GREEN)
        self._log(f"Memory initialized: {total}K total", "info")
        self._render()

    def _apply_holes(self):
        if not self.manager:
            self._show_msg(self.holes_msg, "Initialize memory first", ACCENT_RED)
            return

        self.manager.holes_table.holes.clear()
        valid = []
        for (start_var, size_var, _) in self.hole_rows:
            s = start_var.get().strip()
            sz = size_var.get().strip()
            if not s and not sz:
                continue
            try:
                start = int(s)
                size = int(sz)
                if size <= 0 or start < 0:
                    raise ValueError
                if start + size > self.total_memory:
                    self._show_msg(self.holes_msg,
                                   f"Hole [{start}+{size}] exceeds memory {self.total_memory}K",
                                   ACCENT_RED)
                    return
                valid.append((start, size))
            except ValueError:
                self._show_msg(self.holes_msg, "Invalid hole values", ACCENT_RED)
                return

        valid.sort(key=lambda x: x[0])
        for i in range(len(valid) - 1):
            if valid[i][0] + valid[i][1] > valid[i+1][0]:
                self._show_msg(self.holes_msg, "Holes overlap — check addresses", ACCENT_RED)
                return

        for start, size in valid:
            self.manager.holes_table.add_hole(Hole(start, size))

        self._show_msg(self.holes_msg, f"✓ {len(valid)} hole(s) applied", ACCENT_GREEN)
        self._log(f"Holes applied: {[f'[{s}–{s+sz-1}]' for s,sz in valid]}", "info")
        self._render()

    def _allocate_process(self):
        if not self.manager:
            self._show_msg(self.proc_msg, "Initialize memory first", ACCENT_RED)
            return

        name = self.proc_name_var.get().strip()
        if not name:
            self._show_msg(self.proc_msg, "Enter a process name", ACCENT_RED)
            return

        if any(p.name == name for p in self.manager.processes):
            self._show_msg(self.proc_msg, f"{name} is already allocated", ACCENT_RED)
            return

        segments = []
        for (name_var, size_var, _) in self.seg_rows:
            n = name_var.get().strip()
            s = size_var.get().strip()
            if not n and not s:
                continue
            try:
                sz = int(s)
                if sz <= 0 or not n:
                    raise ValueError
                segments.append(Segment(name=n, size=sz, process_name=name))
            except ValueError:
                self._show_msg(self.proc_msg, "Invalid segment values", ACCENT_RED)
                return

        if not segments:
            self._show_msg(self.proc_msg, "Add at least one segment", ACCENT_RED)
            return

        process = Process(name=name, segments=segments)
        strategy = self.strategy_var.get()

        success = self.manager.allocate_process(process, strategy)

        if success:
            if name not in self.process_color_map:
                self.process_color_map[name] = self.color_counter
                self.color_counter += 1
            strat_label = "first-fit" if strategy == "first_fit" else "best-fit"
            segs_desc = ", ".join(f"{s.name}={s.size}K" for s in segments)
            self._show_msg(self.proc_msg,
                           f"✓ {name} allocated ({len(segments)} segments)", ACCENT_GREEN)
            self._log(f"[{strat_label}] {name} allocated: {segs_desc}", "ok")
            # clear inputs
            self.proc_name_var.set("")
            for (nv, sv, _) in self.seg_rows:
                nv.set(""); sv.set("")
        else:
            self._show_msg(self.proc_msg,
                           f"✗ {name} cannot fit — not enough space in any hole", ACCENT_RED)
            self._log(f"[{strategy.replace('_','-')}] {name} FAILED: no hole fits all segments",
                      "fail")

        self._render()

    def _deallocate_process(self):
        if not self.manager:
            return
        name = self.dealloc_var.get().strip()
        if not name:
            self._show_msg(self.dealloc_msg, "Select a process", ACCENT_RED)
            return

        success = self.manager.deallocate_process(name)
        if success:
            self.process_color_map.pop(name, None)
            self._show_msg(self.dealloc_msg,
                           f"✓ {name} deallocated, holes merged", ACCENT_GREEN)
            self._log(f"Deallocated {name} — memory released and holes merged", "warn")
            self.dealloc_var.set("")
        else:
            self._show_msg(self.dealloc_msg, f"{name} not found", ACCENT_RED)

        self._render()

    def _reset_all(self):
        self.manager = None
        self.total_memory = 0
        self.process_color_map = {}
        self.color_counter = 0
        self.operation_log = []
        self.total_mem_var.set("1000")
        self.proc_name_var.set("")
        self.dealloc_var.set("")
        self.hole_rows.clear()
        self.seg_rows.clear()
        for w in self.holes_list_frame.winfo_children():
            w.destroy()
        for w in self.segs_list_frame.winfo_children():
            w.destroy()
        for _ in range(3):
            self._add_hole_row()
        for _ in range(2):
            self._add_seg_row()
        self._show_msg(self.init_status, "", ACCENT_GREEN)
        self._log("Reset — all state cleared", "info")
        self._render()

    # ── Rendering ─────────────────────────────────────────────────────────────
    def _render(self):
        self._render_memory_bar()
        self._render_tables()
        self._render_seg_tables()
        self._update_stats()
        self._update_dealloc_combo()

    def _render_memory_bar(self):
        canvas = self.mem_canvas
        canvas.delete("all")

        if not self.manager:
            canvas.create_text(80, 300, text="Initialize\nmemory first",
                               fill=FG_MUTED, font=("Consolas", 9), justify="center")
            return

        total = self.total_memory
        canvas.update_idletasks()
        H = canvas.winfo_height() or 500
        W = canvas.winfo_width() or 160

        alloc = self.manager.allocated_table.segments
        holes = self.manager.holes_table.holes

        # Build regions
        events = set([0, total])
        for s in alloc:
            if s.base is not None:
                events.add(s.base)
                events.add(s.base + s.size)
        for h in holes:
            events.add(h.start_address)
            events.add(h.start_address + h.size)
        points = sorted(events)

        regions = []
        for i in range(len(points) - 1):
            s, e = points[i], points[i+1]
            seg_match = next((seg for seg in alloc
                              if seg.base is not None and seg.base <= s < seg.base + seg.size), None)
            hole_match = next((h for h in holes
                               if h.start_address <= s < h.start_address + h.size), None)
            if seg_match:
                regions.append(("alloc", s, e, seg_match.process_name, seg_match.name))
            elif hole_match:
                regions.append(("hole", s, e, None, None))
            else:
                regions.append(("unused", s, e, None, None))

        # Draw
        for kind, s, e, proc, seg_name in regions:
            y0 = (s / total) * H
            y1 = (e / total) * H
            h_px = max(y1 - y0, 1)

            if kind == "alloc":
                idx = self.process_color_map.get(proc, 0)
                bg, fg = get_process_color(idx)
            elif kind == "hole":
                bg, fg = HOLE_COLOR
            else:
                bg, fg = UNUSED_COLOR

            canvas.create_rectangle(2, y0, W-2, y1, fill=bg, outline=BORDER_COLOR, width=0.5)

            if h_px > 14:
                label = f"{proc}·{seg_name}" if kind == "alloc" else ("hole" if kind == "hole" else "unused")
                canvas.create_text(W//2, (y0+y1)//2 - (4 if h_px > 26 else 0),
                                   text=label, fill=fg,
                                   font=("Consolas", 8, "bold"), width=W-8)
            if h_px > 26:
                canvas.create_text(W//2, (y0+y1)//2 + 8,
                                   text=f"{s}–{e-1} ({e-s}K)",
                                   fill=fg, font=("Consolas", 7), width=W-8)

        # Address axis ticks (right side)
        ticks = 6
        for i in range(ticks + 1):
            addr = round(total * i / ticks)
            y = (addr / total) * H
            canvas.create_line(W-8, y, W-2, y, fill=BORDER_COLOR)
            canvas.create_text(W-10, y, text=str(addr), fill=FG_MUTED,
                               font=("Consolas", 7), anchor="e")

        # Legend
        for w in self.legend_frame.winfo_children():
            w.destroy()
        seen = set()
        for kind, s, e, proc, seg_name in regions:
            if kind == "alloc" and proc not in seen:
                seen.add(proc)
                idx = self.process_color_map.get(proc, 0)
                bg, fg = get_process_color(idx)
                row = tk.Frame(self.legend_frame, bg=BG_DARK)
                row.pack(anchor="w", pady=1)
                tk.Label(row, bg=bg, width=2, relief="flat").pack(side="left", padx=(0, 4))
                styled_label(row, proc, color=fg, size=9).pack(side="left")
        for label, color in [("hole", HOLE_COLOR[1]), ("unused", FG_MUTED)]:
            row = tk.Frame(self.legend_frame, bg=BG_DARK)
            row.pack(anchor="w", pady=1)
            dot_color = HOLE_COLOR[0] if label == "hole" else UNUSED_COLOR[0]
            tk.Label(row, bg=dot_color, width=2, relief="flat").pack(side="left", padx=(0, 4))
            styled_label(row, label, color=color, size=9).pack(side="left")

    def _render_tables(self):
        # Allocated
        for row in self.alloc_tree.get_children():
            self.alloc_tree.delete(row)
        if self.manager:
            for seg in self.manager.allocated_table.segments:
                if seg.base is not None:
                    self.alloc_tree.insert("", "end", values=(
                        seg.process_name, seg.name,
                        seg.base, seg.end_address, seg.size
                    ))
        # Holes
        for row in self.holes_tree.get_children():
            self.holes_tree.delete(row)
        if self.manager:
            for i, h in enumerate(sorted(self.manager.holes_table.holes,
                                         key=lambda x: x.start_address)):
                self.holes_tree.insert("", "end", values=(
                    f"H{i+1}", h.start_address, h.end_address, h.size
                ))

    def _render_seg_tables(self):
        for w in self.seg_tables_frame.winfo_children():
            w.destroy()

        if not self.manager or not self.manager.processes:
            styled_label(self.seg_tables_frame, "No processes allocated",
                         color=FG_MUTED, size=9).pack(anchor="w")
            return

        procs_frame = tk.Frame(self.seg_tables_frame, bg=BG_CARD)
        procs_frame.pack(fill="x")

        for process in self.manager.processes:
            idx = self.process_color_map.get(process.name, 0)
            bg, fg = get_process_color(idx)

            col = tk.Frame(procs_frame, bg=BG_CARD, padx=6)
            col.pack(side="left", fill="y", padx=(0, 8))

            # Process header badge
            hdr = tk.Frame(col, bg=bg, padx=8, pady=3)
            hdr.pack(fill="x", pady=(0, 4))
            tk.Label(hdr, text=process.name, fg=fg, bg=bg,
                     font=("Consolas", 10, "bold")).pack(side="left")
            tk.Label(hdr, text=f"  {process.no_segments} segs  {process.total_size}K",
                     fg=fg, bg=bg, font=("Consolas", 8)).pack(side="left")

            # Segment table
            cols = ("#", "Segment", "Base", "Limit", "Size")
            widths = (22, 55, 45, 50, 45)
            tree = ttk.Treeview(col, columns=cols, show="headings",
                                 style="Dark.Treeview", height=min(len(process.segments), 5))
            for c, w in zip(cols, widths):
                tree.heading(c, text=c)
                tree.column(c, width=w, anchor="center")
            for i, seg in enumerate(process.segments):
                tree.insert("", "end", values=(
                    i, seg.name,
                    seg.base if seg.base is not None else "—",
                    seg.end_address if seg.end_address is not None else "—",
                    seg.size
                ))
            tree.pack(fill="x")

    def _update_stats(self):
        if not self.manager:
            self.stats_label.config(text="No memory initialized")
            return
        total = self.total_memory
        used = sum(s.size for s in self.manager.allocated_table.segments if s.base is not None)
        hole_sz = sum(h.size for h in self.manager.holes_table.holes)
        unused = total - used - hole_sz
        procs = len(self.manager.processes)
        self.stats_label.config(
            text=f"{total}K total  ·  {used}K allocated  ·  {hole_sz}K in holes  ·  {unused}K unused  ·  {procs} process(es)"
        )

    def _update_dealloc_combo(self):
        names = [p.name for p in self.manager.processes] if self.manager else []
        self.dealloc_combo["values"] = names

    def _update_stats(self):
        if not self.manager:
            self.stats_label.config(text="No memory initialized")
            return
        total = self.total_memory
        used = sum(s.size for s in self.manager.allocated_table.segments if s.base is not None)
        hole_sz = sum(h.size for h in self.manager.holes_table.holes)
        unused = total - used - hole_sz
        procs = len(self.manager.processes)
        self.stats_label.config(
            text=(f"{total}K total  ·  {used}K used  ·  {hole_sz}K holes  ·"
                  f"  {unused}K unused  ·  {procs} process(es)")
        )

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _show_msg(self, label_widget, text, color):
        label_widget.config(text=text, fg=color)
        if text:
            label_widget.after(5000, lambda: label_widget.config(text=""))

    def _log(self, msg, tag="info"):
        import datetime
        t = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("1.0", f"[{t}] {msg}\n", tag)
        self.log_text.config(state="disabled")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MemoryAllocatorApp()
    app.mainloop()