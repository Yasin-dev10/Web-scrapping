# -*- coding: utf-8 -*-
"""
db_dashboard.py — Xogta Database-ka (Xogta la Eego, la Sareeyo, CSV la soo Daajiso)
======================================================================================
Run:  python db_dashboard.py
"""
import os, sys, threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import shared_db

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Colors ────────────────────────────────────────────────────────────────────
BG          = "#0d1117"
SURFACE     = "#161b22"
CARD        = "#1c2230"
ACCENT      = "#58a6ff"
ACCENT2     = "#1f6feb"
GREEN       = "#3fb950"
RED         = "#f85149"
YELLOW      = "#d29922"
TEXT        = "#cdd9e5"
MUTED       = "#768390"
BORDER      = "#30363d"
FONT_FAMILY = "Segoe UI"

# ── Badge colors by category ──────────────────────────────────────────────────
CAT_COLORS = {
    "crime-related":     RED,
    "not crime-related": GREEN,
}

# ── Source badge colors ───────────────────────────────────────────────────────
SRC_COLORS = {
    "Facebook-Scraper": "#3b82f6",
    "CrimeFilter":      RED,
    "NotCrimeFilter":   GREEN,
    "SplitTool-Crime":  "#f97316",
    "SplitTool-NotCrime": "#22d3ee",
}


class DBDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🗄️  Xogta Database — Dhamaan Barnaamijyada")
        self.geometry("1280x780")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._all_data = []       # list of dict
        self._filtered_data = []  # currently shown

        self._build_ui()
        self._load_data()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI Construction
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        self._header()
        self._toolbar()
        self._stats_bar()
        self._table_area()
        self._statusbar()

    def _header(self):
        hdr = tk.Frame(self, bg=SURFACE, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=ACCENT, width=5).pack(side="left", fill="y")
        tk.Label(hdr, text="  🗄️  Database Dashboard",
                 font=(FONT_FAMILY, 16, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left", pady=12, padx=8)
        tk.Label(hdr, text="— Dhammaan xogta barnaamijyada meel ka hel",
                 font=(FONT_FAMILY, 10), bg=SURFACE, fg=MUTED).pack(side="left")

        # Refresh button
        tk.Button(hdr, text="🔄  Cusboonaysii", bg=ACCENT2, fg="white",
                  font=(FONT_FAMILY, 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=6, command=self._load_data).pack(side="right", padx=16, pady=10)

    def _toolbar(self):
        bar = tk.Frame(self, bg=CARD, padx=16, pady=10)
        bar.pack(fill="x")

        # ── Search ────────────────────────────────────────────────────────
        tk.Label(bar, text="🔍 Raadi:", bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 9)).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._apply_filter())
        tk.Entry(bar, textvariable=self._search_var,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=(FONT_FAMILY, 10),
                 highlightthickness=1, highlightbackground=BORDER,
                 width=28).pack(side="left", ipady=5, padx=(4, 20))

        # ── Category filter ───────────────────────────────────────────────
        tk.Label(bar, text="Category:", bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 9)).pack(side="left")
        self._cat_var = tk.StringVar(value="Dhamaan")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=SURFACE, background=CARD,
                        foreground=TEXT, bordercolor=BORDER, arrowcolor=TEXT)
        ttk.Combobox(bar, textvariable=self._cat_var,
                     values=["Dhamaan", "crime-related", "not crime-related"],
                     state="readonly", font=(FONT_FAMILY, 9), width=18
                     ).pack(side="left", padx=(4, 20), ipady=3)
        self._cat_var.trace_add("write", lambda *a: self._apply_filter())

        # ── Source filter ─────────────────────────────────────────────────
        tk.Label(bar, text="Source:", bg=CARD, fg=MUTED,
                 font=(FONT_FAMILY, 9)).pack(side="left")
        self._src_var = tk.StringVar(value="Dhamaan")
        self._src_cb = ttk.Combobox(bar, textvariable=self._src_var,
                                    values=["Dhamaan"],
                                    state="readonly", font=(FONT_FAMILY, 9), width=22)
        self._src_cb.pack(side="left", padx=(4, 20), ipady=3)
        self._src_var.trace_add("write", lambda *a: self._apply_filter())

        # ── Export ────────────────────────────────────────────────────────
        tk.Button(bar, text="📥  Soo Daaji CSV",
                  bg=GREEN, fg="#0d1117",
                  font=(FONT_FAMILY, 9, "bold"), relief="flat",
                  cursor="hand2", padx=12, pady=6,
                  command=self._export_csv).pack(side="right", padx=(0, 6))

        tk.Button(bar, text="🗑️  Tirtir DB",
                  bg="#30363d", fg=RED,
                  font=(FONT_FAMILY, 9, "bold"), relief="flat",
                  cursor="hand2", padx=12, pady=6,
                  command=self._clear_db).pack(side="right", padx=(0, 6))

    def _stats_bar(self):
        bar = tk.Frame(self, bg=BG, padx=16, pady=8)
        bar.pack(fill="x")

        self._stat_frames = {}
        stats_defs = [
            ("total",     "Dhammaan",      TEXT),
            ("crime",     "Crime",         RED),
            ("not_crime", "Not Crime",     GREEN),
            ("showing",   "La Muujinayaa", ACCENT),
        ]
        for key, label, color in stats_defs:
            f = tk.Frame(bar, bg=CARD, padx=18, pady=8)
            f.pack(side="left", padx=(0, 10))
            num = tk.Label(f, text="0", font=(FONT_FAMILY, 20, "bold"),
                           bg=CARD, fg=color)
            num.pack()
            tk.Label(f, text=label, font=(FONT_FAMILY, 8),
                     bg=CARD, fg=MUTED).pack()
            self._stat_frames[key] = num

    def _table_area(self):
        outer = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        inner = tk.Frame(outer, bg=BG)
        inner.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("DB.Treeview",
                        background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, borderwidth=0,
                        font=(FONT_FAMILY, 9), rowheight=26)
        style.map("DB.Treeview", background=[("selected", ACCENT2)])
        style.configure("DB.Treeview.Heading",
                        background=CARD, foreground=TEXT,
                        borderwidth=0, font=(FONT_FAMILY, 9, "bold"))

        cols = ("id", "category", "source", "scraped_at", "url", "text")
        self._tree = ttk.Treeview(inner, columns=cols, show="headings",
                                  style="DB.Treeview")

        col_config = [
            ("id",         "ID",          50,  "center"),
            ("category",   "Category",   120,  "center"),
            ("source",     "Source",     160,  "center"),
            ("scraped_at", "Wakhtiga",   130,  "center"),
            ("url",        "URL",        200,  "w"),
            ("text",       "Qoraalka",   600,  "w"),
        ]
        for col_id, heading, width, anchor in col_config:
            self._tree.heading(col_id, text=heading,
                               command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, anchor=anchor,
                              minwidth=40)

        # Tag colors
        self._tree.tag_configure("crime",     foreground=RED)
        self._tree.tag_configure("not_crime", foreground=GREEN)

        vsb = ttk.Scrollbar(inner, orient="vertical",     command=self._tree.yview)
        hsb = ttk.Scrollbar(inner, orient="horizontal",   command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        inner.rowconfigure(0, weight=1)
        inner.columnconfigure(0, weight=1)

        # Double-click → full text popup
        self._tree.bind("<Double-1>", self._show_full_text)

    def _statusbar(self):
        bar = tk.Frame(self, bg=SURFACE, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._lbl_status = tk.Label(
            bar, text="  Diyaar", bg=SURFACE, fg=MUTED,
            font=(FONT_FAMILY, 8), anchor="w")
        self._lbl_status.pack(side="left", fill="x", expand=True)
        self._lbl_db = tk.Label(
            bar, text="", bg=SURFACE, fg=MUTED,
            font=(FONT_FAMILY, 8), anchor="e")
        self._lbl_db.pack(side="right", padx=10)

    # ══════════════════════════════════════════════════════════════════════════
    #  Data Loading / Filtering
    # ══════════════════════════════════════════════════════════════════════════
    def _load_data(self):
        self._lbl_status.configure(text="  Soo raraya xogta...")
        self.update()
        try:
            self._all_data = shared_db.get_all_posts()
            stats = shared_db.get_stats()

            # Update stat boxes
            self._stat_frames["total"].configure(text=str(stats["total"]))
            self._stat_frames["crime"].configure(text=str(stats["crime"]))
            self._stat_frames["not_crime"].configure(text=str(stats["not_crime"]))

            # Update source dropdown
            sources = ["Dhamaan"] + sorted(stats["sources"].keys())
            self._src_cb.configure(values=sources)

            self._apply_filter()
            self._lbl_db.configure(text=f"DB: {shared_db.DB_PATH}")
            self._lbl_status.configure(text=f"  ✅ {stats['total']} xog ayaa la soo raray")
        except Exception as e:
            messagebox.showerror("Cillad", f"Database error: {e}")
            self._lbl_status.configure(text=f"  ❌ {e}")

    def _apply_filter(self):
        search  = self._search_var.get().lower().strip()
        cat     = self._cat_var.get()
        src     = self._src_var.get()

        result = []
        for row in self._all_data:
            if cat != "Dhamaan" and row.get("category") != cat:
                continue
            if src != "Dhamaan" and row.get("source") != src:
                continue
            if search:
                combined = (str(row.get("text","")) + str(row.get("url",""))).lower()
                if search not in combined:
                    continue
            result.append(row)

        self._filtered_data = result
        self._render_table(result)
        self._stat_frames["showing"].configure(text=str(len(result)))

    def _render_table(self, data):
        self._tree.delete(*self._tree.get_children())
        for row in data:
            cat = row.get("category", "")
            tag = "crime" if cat == "crime-related" else "not_crime"
            vals = (
                row.get("id", ""),
                cat,
                row.get("source", ""),
                row.get("scraped_at", "")[:16],   # YYYY-MM-DD HH:MM
                (row.get("url", "") or "")[:80],
                (row.get("text","") or "").replace("\n", " ")[:120],
            )
            self._tree.insert("", "end", values=vals, tags=(tag,))

    def _sort_by(self, col):
        """Sort table by column."""
        reverse = getattr(self, "_sort_reverse", False)
        self._sort_reverse = not reverse
        self._filtered_data.sort(
            key=lambda r: str(r.get(col, "") or ""),
            reverse=reverse)
        self._render_table(self._filtered_data)

    # ══════════════════════════════════════════════════════════════════════════
    #  Actions
    # ══════════════════════════════════════════════════════════════════════════
    def _export_csv(self):
        if not self._filtered_data:
            messagebox.showwarning("Ogeysiis", "Xog la muujin maayo!")
            return

        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        cat = self._cat_var.get().replace(" ", "_").replace("/", "-")
        src = self._src_var.get().replace(" ", "_")
        default_name = f"export_{cat}_{src}_{ts}.csv"

        path = filedialog.asksaveasfilename(
            title="Keydi CSV-ga",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        try:
            df = pd.DataFrame(self._filtered_data)
            cols = [c for c in ["id","url","text","category","source","scraped_at"] if c in df.columns]
            df[cols].to_csv(path, index=False, encoding="utf-8-sig")
            count = len(df)
            messagebox.showinfo("Guul ✅",
                f"CSV waa la keydiyey!\n\n"
                f"Tirada rows-ka: {count}\n"
                f"Meeshii: {path}")
            self._lbl_status.configure(text=f"  ✅ CSV: {count} rows → {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Cillad", f"Keydinta ayaa fashilantay: {e}")

    def _clear_db(self):
        ans = messagebox.askyesno(
            "Hubin (Confirm)",
            "Ma hubtaa inaad tirtirayso DHAMMAAN xogta database-ka?\n\n"
            "Tani waa aan la noqon karin!")
        if ans:
            try:
                shared_db.clear_all()
                self._load_data()
                messagebox.showinfo("Guul", "Database-ka waa la nadiifiyey.")
            except Exception as e:
                messagebox.showerror("Cillad", str(e))

    def _show_full_text(self, event):
        """Double-click → popup with full text."""
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        if idx >= len(self._filtered_data):
            return
        row = self._filtered_data[idx]

        popup = tk.Toplevel(self)
        popup.title(f"Qoraalka Buuxa — ID {row.get('id','')} | {row.get('category','')}")
        popup.geometry("700x400")
        popup.configure(bg=BG)

        info = tk.Frame(popup, bg=SURFACE, padx=12, pady=8)
        info.pack(fill="x")
        tk.Label(info, text=f"Source: {row.get('source','')}   |   Category: {row.get('category','')}   |   {row.get('scraped_at','')}",
                 bg=SURFACE, fg=MUTED, font=(FONT_FAMILY, 9)).pack(anchor="w")
        tk.Label(info, text=f"URL: {row.get('url','')[:100]}",
                 bg=SURFACE, fg=ACCENT, font=(FONT_FAMILY, 9)).pack(anchor="w")

        txt = tk.Text(popup, bg=SURFACE, fg=TEXT, font=(FONT_FAMILY, 10),
                      wrap="word", relief="flat", padx=12, pady=10)
        txt.pack(fill="both", expand=True)
        txt.insert("end", row.get("text", ""))
        txt.configure(state="disabled")

        sb = ttk.Scrollbar(txt, command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.configure(yscrollcommand=sb.set)


if __name__ == "__main__":
    app = DBDashboard()
    app.mainloop()
