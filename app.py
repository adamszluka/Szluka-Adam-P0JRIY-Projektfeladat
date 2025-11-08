import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from concurrent.futures import ThreadPoolExecutor
from sa_module_SA import SADataStore, calculate_stats_SA

class SAChartCanvas(tk.Canvas):
    def __init__(self, master, days, distances, stats, **kwargs):
        super().__init__(master, **kwargs)
        self.days = days
        self.distances = distances
        self.stats = stats
        self.bind("<Configure>", self.redraw)

    def redraw(self, event=None):
        self.delete("all")
        if not self.distances:
            self.create_text(10, 10, anchor="nw", text="Nincs adat")
            return
        width = self.winfo_width()
        height = self.winfo_height()
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 50
        plot_width = max(1, width - margin_left - margin_right)
        plot_height = max(1, height - margin_top - margin_bottom)
        if plot_width <= 0 or plot_height <= 0:
            return
        max_dist = max(self.distances)
        if max_dist <= 0:
            max_dist = 1.0
        self.create_line(margin_left, margin_top, margin_left, margin_top + plot_height)
        self.create_line(margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height)
        n = len(self.distances)
        if n == 1:
            step_x = plot_width
        else:
            step_x = plot_width / (n - 1)
        scaled_points = []
        for i, dist in enumerate(self.distances):
            x = margin_left + i * step_x
            y = margin_top + plot_height - (dist / max_dist) * plot_height
            scaled_points.append((x, y))
        for i in range(len(scaled_points) - 1):
            x1, y1 = scaled_points[i]
            x2, y2 = scaled_points[i + 1]
            self.create_line(x1, y1, x2, y2, fill="blue", width=2)
        for i, (x, y) in enumerate(scaled_points):
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")
        for i, day in enumerate(self.days):
            x, _ = scaled_points[i]
            self.create_text(x, margin_top + plot_height + 15, text=str(day), anchor="n", font=("Arial", 8))
        for i in range(5):
            y_val = max_dist * i / 4
            y = margin_top + plot_height - (y_val / max_dist) * plot_height
            self.create_line(margin_left - 5, y, margin_left, y)
            self.create_text(margin_left - 10, y, text=f"{y_val:.1f}", anchor="e", font=("Arial", 8))
        info_text = f"Összesen: {self.stats['total']:.2f} km | Átlag: {self.stats['mean']:.2f} km | Medián: {self.stats['median']:.2f} km | Szórás: {self.stats['stdev']:.2f}"
        self.create_text(margin_left, margin_top + plot_height + 30, anchor="w", text=info_text, font=("Arial", 9, "bold"))

class SAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Napi futás tracker - Szluka Ádám P0JRIY")
        self.data_store = SADataStore()
        self.ask_before_overwrite = True
        self.build_ui()

    def build_ui(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Megnyitás", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Mentés", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Kilépés", accelerator="Ctrl+Q", command=self.root.quit)
        menubar.add_cascade(label="Fájl", menu=file_menu)
        options_menu = tk.Menu(menubar, tearoff=0)
        self.ask_var = tk.BooleanVar(value=True)
        options_menu.add_checkbutton(label="Kérdezz, mielőtt felülírnád a listát", onvalue=True, offvalue=False, variable=self.ask_var, command=self.toggle_ask)
        menubar.add_cascade(label="Beállítások", menu=options_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Diagram + statisztika", accelerator="Ctrl+D", command=self.show_chart)
        menubar.add_cascade(label="Nézet", menu=view_menu)
        self.root.config(menu=menubar)
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())
        self.root.bind_all("<Control-q>", lambda e: self.root.quit())
        self.root.bind_all("<Control-d>", lambda e: self.show_chart())
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(top_frame, text="Nap:").grid(row=0, column=0, sticky="w")
        self.entry_day = tk.Entry(top_frame, width=10)
        self.entry_day.grid(row=0, column=1, padx=5)
        tk.Label(top_frame, text="Távolság (km):").grid(row=0, column=2, sticky="w")
        self.entry_distance = tk.Entry(top_frame, width=10)
        self.entry_distance.grid(row=0, column=3, padx=5)
        self.btn_add = tk.Button(top_frame, text="Hozzáadás", command=self.add_entry)
        self.btn_add.grid(row=0, column=4, padx=5)
        self.btn_delete = tk.Button(top_frame, text="Kijelölt törlése", command=self.delete_selected)
        self.btn_delete.grid(row=0, column=5, padx=5)
        mid_frame = tk.Frame(self.root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        columns = ("day", "distance")
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("day", text="Nap")
        self.tree.heading("distance", text="Távolság (km)")
        self.tree.column("day", width=100, anchor="center")
        self.tree.column("distance", width=120, anchor="e")
        vsb = ttk.Scrollbar(mid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        mid_frame.rowconfigure(0, weight=1)
        mid_frame.columnconfigure(0, weight=1)
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        self.lbl_status = tk.Label(bottom_frame, text="0 mérés", anchor="w")
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_stats = tk.Label(bottom_frame, text="", anchor="e")
        self.lbl_stats.pack(side=tk.RIGHT)

    def toggle_ask(self):
        self.ask_before_overwrite = self.ask_var.get()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        days = self.data_store.get_days()
        distances = self.data_store.get_distances()
        for d, dist in zip(days, distances):
            self.tree.insert("", tk.END, values=(d, f"{dist:.2f}"))
        self.lbl_status.config(text=f"{len(days)} mérés")

    def add_entry(self):
        day_text = self.entry_day.get().strip()
        distance_text = self.entry_distance.get().strip()
        if not day_text or not distance_text:
            messagebox.showwarning("Hiba", "Minden mezőt ki kell tölteni.")
            return
        try:
            day = int(day_text)
        except ValueError:
            messagebox.showerror("Hiba", "A napnak egész számnak kell lennie.")
            return
        try:
            distance = float(distance_text.replace(",", "."))
        except ValueError:
            messagebox.showerror("Hiba", "A távolságnak számnak kell lennie.")
            return
        if distance < 0:
            messagebox.showerror("Hiba", "A távolság nem lehet negatív.")
            return
        ok = self.data_store.add_entry(day, distance)
        if not ok:
            messagebox.showwarning("Hiba", "Ehhez a naphoz már van mérés.")
            return
        self.entry_day.delete(0, tk.END)
        self.entry_distance.delete(0, tk.END)
        self.refresh_tree()

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        indices = []
        all_ids = list(self.tree.get_children())
        for item_id in selection:
            idx = all_ids.index(item_id)
            indices.append(idx)
        self.data_store.delete_indices(indices)
        self.refresh_tree()

    def save_file(self):
        if not self.data_store.entries:
            messagebox.showinfo("Info", "Nincs mit menteni.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Szövegfájl", "*.txt"), ("Minden fájl", "*.*")])
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                for day, dist in self.data_store.entries:
                    f.write(f"{day};{dist}\n")
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba mentés közben: {e}")

    def open_file(self):
        if self.data_store.entries and self.ask_before_overwrite:
            ans = messagebox.askyesno("Megerősítés", "Felülírod a jelenlegi listát?")
            if not ans:
                return
        filename = filedialog.askopenfilename(filetypes=[("Szövegfájl", "*.txt"), ("Minden fájl", "*.*")])
        if not filename:
            return
        new_entries = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.replace(",", ".").split(";")
                    if len(parts) < 2:
                        continue
                    try:
                        day = int(parts[0])
                        dist = float(parts[1])
                    except ValueError:
                        continue
                    if dist < 0:
                        continue
                    exists = False
                    for d, _ in new_entries:
                        if d == day:
                            exists = True
                            break
                    if not exists:
                        new_entries.append((day, dist))
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba megnyitás közben: {e}")
            return
        new_entries.sort(key=lambda x: x[0])
        self.data_store.clear()
        for d, dist in new_entries:
            self.data_store.add_entry(d, dist)
        self.refresh_tree()

    def show_chart(self):
        days = self.data_store.get_days()
        distances = self.data_store.get_distances()
        if not days:
            messagebox.showinfo("Info", "Nincs egyetlen mérés sem.")
            return
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(calculate_stats_SA, distances)
            stats = future.result()
        self.lbl_stats.config(text=f"Összesen: {stats['total']:.2f} km, átlag: {stats['mean']:.2f} km")
        win = tk.Toplevel(self.root)
        win.title("Diagram")
        win.geometry("800x400")
        canvas = SAChartCanvas(win, days, distances, stats, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)
