import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Any, Dict, List, Optional
class UI:
    def __init__(self, api): #There's a little black spot on the sun too deep
        self.api = api #It's the same old place as yesterday
        self.root = tk.Tk() #There's a little black hat on a high tree top
        self.root.title("World Economy Simulator") #There's a flagpole rag and the wind won't stop
        self.root.geometry("900x600") #I have stood here before, inside the pouring rain
        self._current_table_name: Optional[str] = None #With the world turning circles 'running round by brain
        self._current_rows: List[Dict[str, Any]] = [] #I guess I'd always hope that you would end this reign
        top = tk.Frame(self.root) #But it's my destiny to be the king of pain...
        top.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(top, text="Table").pack(side=tk.LEFT)
        self.table_select = ttk.Combobox(top, width=30, state="readonly")
        self.table_select.pack(side=tk.LEFT, padx=(6, 10))
        self.table_select.bind("<<ComboboxSelected>>", lambda e: self.show_selected_table())
        ttk.Button(top, text="Refresh", command=self.show_selected_table).pack(side=tk.LEFT)
        ttk.Separator(top, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.ticker_btn = ttk.Button(top, text="Stop ticker", command=self.toggle_ticker)
        self.ticker_btn.pack(side=tk.LEFT)
        ttk.Button(top, text="Seed DB (2020)", command=self.seed_db_2020).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(top, text="Transaction Failure", command=self.transaction_failure).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(top, text="Transaction Success", command=self.transaction_success).pack(side=tk.LEFT, padx=(6, 0))
        action = tk.Frame(self.root)
        action.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(action, text="Add country", command=self.add_country_dialog).pack(side=tk.LEFT)
        ttk.Button(action, text="Add province", command=self.add_province_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(action, text="Add province pop", command=self.add_province_pop_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(action, text="Add province factory", command=self.add_province_factory_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(action, text="Create market order", command=self.create_market_order_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(action, text="Create trade route", command=self.create_trade_route_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(action, text="Start war", command=self.start_war_dialog).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X, padx=8, pady=(0, 6))
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.table = ttk.Treeview(table_frame, show="headings")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.table.bind("<Double-1>", self.on_double_click_edit)
        self.table.bind("<Delete>", self.on_delete_row)
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(bottom, text="Report", command=self.show_report).pack(side=tk.LEFT)
        ttk.Label(bottom, text="Tip: double-click a cell to edit; Del to delete a row.").pack(side=tk.LEFT, padx=12)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.api.start_ticker(interval=5)
        self._ticker_running = True
        self.load_table_list()
        self.show_countries()
    def clear_table(self): #What is a man? What has he got? If not himself? Then he has naught. To say the things, he truly feels. And not the words, of one who kneels. The record shows, I took the blows. And did it my way.
        self.table.delete(*self.table.get_children())
    def setup_columns(self, columns):
        self.table["columns"] = columns
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=150)
    def populate(self, data):
        if not data:
            self.clear_table()
            return
        self.clear_table()
        columns = list(data[0].keys())
        self.setup_columns(columns)
        self._current_rows = data
        for row in data:
            self.table.insert("", "end", values=list(row.values()))
    def load_table_list(self):
        try:
            tables = self.api.list_tables()
        except Exception as e:
            messagebox.showerror("DB error", str(e))
            tables = []
        self.table_select["values"] = tables
        if tables and self.table_select.get() == "":
            self.table_select.set("Country" if "Country" in tables else tables[0])
    def show_selected_table(self):
        table = self.table_select.get().strip()
        if not table:
            return
        self._current_table_name = table
        data = self.api.get_table_data(table, limit=500)
        self.populate(data)
    def show_countries(self):
        data = self.api.get_all_countries()
        self._current_table_name = "Country"
        if "Country" in (self.table_select["values"] or []):
            self.table_select.set("Country")
        self.populate(data)
    def show_dark_economy(self):
        data = self.api.get_dark_economy_countries()
        self._current_table_name = "DarkEconomy"
        if "DarkEconomy" in (self.table_select["values"] or []):
            self.table_select.set("DarkEconomy")
        self.populate(data)
    def show_trade(self):
        data = self.api.get_trade_between_countries()
        self._current_table_name = "ActiveTradeRoute"
        if "ActiveTradeRoute" in (self.table_select["values"] or []):
            self.table_select.set("ActiveTradeRoute")
        self.populate(data)
    def show_production(self):
        data = self.api.get_countries_with_highest_production()
        self.populate(data)
    def show_wars(self):
        data = self.api.get_countries_with_highest_casualties()
        self.populate(data)
    def show_report(self):
        report = self.api.generate_economy_report()
        formatted = [{"Key": k, "Value": str(v)} for k, v in report.items()]
        self._current_table_name = None
        self.populate(formatted)
    def toggle_ticker(self):
        if self._ticker_running:
            self.api.stop_ticker()
            self._ticker_running = False
            self.ticker_btn.configure(text="Start ticker")
        else:
            self.api.start_ticker(interval=5)
            self._ticker_running = True
            self.ticker_btn.configure(text="Stop ticker")

    def seed_db_2020(self):
        ok = self.api.run_sql_file("seed_2020.sql")
        if not ok:
            messagebox.showerror("Seed failed", "Could not run seed_2020.sql. Check backend.log.")
            return
        self.load_table_list()
        self.show_selected_table()

    def transaction_failure(self):
        res = self.api.demo_trade_transaction(conflict=True)
        if res.get("ok"):
            messagebox.showinfo("Unexpected success", str(res.get("message")))
        else:
            messagebox.showerror("Transaction Failure (expected)", str(res.get("message")))
        if "ActiveTradeRoute" in (self.table_select["values"] or []):
            self.table_select.set("ActiveTradeRoute")
        self.show_selected_table()

    def transaction_success(self):
        res = self.api.demo_trade_transaction(conflict=False)
        if res.get("ok"):
            messagebox.showinfo("Transaction Success", str(res.get("message")))
        else:
            messagebox.showerror("Transaction Failed", str(res.get("message")))
        if "ActiveTradeRoute" in (self.table_select["values"] or []):
            self.table_select.set("ActiveTradeRoute")
        self.show_selected_table()
    def _prompt_int(self, title: str, prompt: str, initial: Optional[int] = None) -> Optional[int]: #Some Python magic to really make it work, pop ups and stuff. Mmhmm, Skinner patented recipe!
        s = simpledialog.askstring(title, prompt, initialvalue="" if initial is None else str(initial), parent=self.root)
        if s is None:
            return None
        s = s.strip()
        if s == "":
            return None
        try:
            return int(s)
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter an integer.")
            return None
    def _prompt_float(self, title: str, prompt: str, initial: Optional[float] = None) -> Optional[float]:
        s = simpledialog.askstring(title, prompt, initialvalue="" if initial is None else str(initial), parent=self.root)
        if s is None:
            return None
        s = s.strip()
        if s == "":
            return None
        try:
            return float(s)
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a number.")
            return None
    def _prompt_str(self, title: str, prompt: str, initial: str = "") -> Optional[str]:
        s = simpledialog.askstring(title, prompt, initialvalue=initial, parent=self.root)
        if s is None:
            return None
        s = s.strip()
        return s if s != "" else None

    def _pick_from_options(self, title: str, prompt: str, options: List[tuple]) -> Optional[Any]:
        if not options:
            messagebox.showerror("No data", f"No options available for {prompt.lower()}.")
            return None
        win = tk.Toplevel(self.root)
        win.title(title)
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text=prompt).pack(anchor="w", padx=10, pady=(10, 4))
        combo = ttk.Combobox(win, width=60, state="readonly")
        combo["values"] = [label for _, label in options]
        combo.pack(fill=tk.X, padx=10)
        combo.current(0)

        result = {"value": None}

        def submit():
            idx = combo.current()
            if idx < 0:
                return
            result["value"] = options[idx][0]
            win.destroy()

        btns = tk.Frame(win)
        btns.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="OK", command=submit).pack(side=tk.RIGHT, padx=(0, 6))
        win.wait_window()
        return result["value"]

    def _pick_country_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_country_options()
        options = [(r["country_id"], f'{r["country_name"]} (id={r["country_id"]})') for r in rows]
        return self._pick_from_options(title, prompt, options)

    def _pick_province_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_province_options()
        options = [
            (
                r["province_id"],
                f'Province {r["province_id"]} | node {r.get("node_id")} | owner {r.get("owner_country_name") or "Unknown"}',
            )
            for r in rows
        ]
        return self._pick_from_options(title, prompt, options)

    def _pick_goods_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_goods_options()
        options = [(r["goods_id"], f'{r["good_name"]} (id={r["goods_id"]})') for r in rows]
        return self._pick_from_options(title, prompt, options)

    def _pick_pop_type_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_population_type_options()
        options = [(r["pop_id"], f'{r["pop_name"]} (id={r["pop_id"]})') for r in rows]
        return self._pick_from_options(title, prompt, options)

    def _pick_factory_type_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_factory_type_options()
        options = [(r["factory_type_id"], f'{r["factory_name"]} (id={r["factory_type_id"]})') for r in rows]
        return self._pick_from_options(title, prompt, options)

    def _pick_node_id(self, title: str, prompt: str) -> Optional[int]:
        rows = self.api.get_map_node_options()
        options = [(r["node_id"], f'{r["node_name"]} ({r["terrain_type"]}) id={r["node_id"]}') for r in rows]
        return self._pick_from_options(title, prompt, options)
    def add_country_dialog(self):
        name = self._prompt_str("Add country", "Country name")
        if not name:
            return
        gdp = self._prompt_float("Add country", "GDP")
        if gdp is None:
            return
        debt = self._prompt_float("Add country", "National debt", initial=0.0)
        if debt is None:
            debt = 0.0
        government_type_id = self._prompt_int("Add country", "Government type id (optional, blank = NULL)")
        currency_id = self._prompt_int("Add country", "Currency id (optional, blank = NULL)")
        ok = self.api.create_country(
            name=name,
            gdp=gdp,
            national_debt=debt,
            government_type_id=government_type_id,
            currency_id=currency_id,
        )
        if not ok:
            messagebox.showerror("Insert failed", "Could not add country. Check backend.log for details.")
            return
        self.show_countries()
    def add_province_dialog(self):
        node_id = self._pick_node_id("Add province", "Select node")
        if node_id is None:
            return
        owner_country_id = self._pick_country_id("Add province", "Select owner country")
        if owner_country_id is None:
            return
        controller_country_id = self._pick_country_id("Add province", "Select controller country")
        if controller_country_id is None:
            return
        ok = self.api.create_province(node_id, owner_country_id, controller_country_id)
        if not ok:
            messagebox.showerror("Insert failed", "Could not add province. Check backend.log.")
            return
        self.table_select.set("Province")
        self.show_selected_table()

    def add_province_pop_dialog(self):
        province_id = self._pick_province_id("Add province pop", "Select province")
        if province_id is None:
            return
        pop_type_id = self._pick_pop_type_id("Add province pop", "Select population type")
        if pop_type_id is None:
            return
        headcount = self._prompt_int("Add province pop", "Headcount")
        if headcount is None:
            return
        wealth = self._prompt_float("Add province pop", "Wealth", initial=0.0)
        if wealth is None:
            wealth = 0.0
        militancy = self._prompt_float("Add province pop", "Militancy (0-100)", initial=0.0)
        if militancy is None:
            militancy = 0.0
        ok = self.api.add_province_population(province_id, pop_type_id, headcount, wealth, militancy)
        if not ok:
            messagebox.showerror("Insert failed", "Could not add province population. Check backend.log.")
            return
        self.table_select.set("ProvincePopulation")
        self.show_selected_table()

    def add_province_factory_dialog(self):
        province_id = self._pick_province_id("Add province factory", "Select province")
        if province_id is None:
            return
        factory_type_id = self._pick_factory_type_id("Add province factory", "Select factory type")
        if factory_type_id is None:
            return
        is_active = messagebox.askyesno("Factory active", "Should the factory be active?")
        ok = self.api.create_province_factory(province_id, factory_type_id, is_active)
        if not ok:
            messagebox.showerror("Insert failed", "Could not add province factory. Check backend.log.")
            return
        self.table_select.set("ProvinceFactory")
        self.show_selected_table()

    def create_market_order_dialog(self):
        country_id = self._pick_country_id("Create market order", "Select country")
        if country_id is None:
            return
        goods_id = self._pick_goods_id("Create market order", "Select goods")
        if goods_id is None:
            return
        is_buy_order = messagebox.askyesno("Order type", "Is this a BUY order?")
        quantity = self._prompt_int("Create market order", "Quantity (>0)")
        if quantity is None:
            return
        tick_submitted = self._prompt_int("Create market order", "Tick submitted")
        if tick_submitted is None:
            return
        ok = self.api.create_market_order(country_id, goods_id, is_buy_order, quantity, tick_submitted)
        if not ok:
            messagebox.showerror("Insert failed", "Could not create market order. Check backend.log.")
            return
        self.table_select.set("MarketOrders")
        self.show_selected_table()

    def create_trade_route_dialog(self):
        buyer_country_id = self._pick_country_id("Create trade route", "Select buyer country")
        if buyer_country_id is None:
            return
        seller_country_id = self._pick_country_id("Create trade route", "Select seller country")
        if seller_country_id is None:
            return
        goods_id = self._pick_goods_id("Create trade route", "Select goods")
        if goods_id is None:
            return
        quantity = self._prompt_int("Create trade route", "Quantity")
        if quantity is None:
            return
        route_efficiency = self._prompt_float("Create trade route", "Route efficiency", initial=1.0)
        if route_efficiency is None:
            route_efficiency = 1.0
        tick_established = self._prompt_int("Create trade route", "Tick established")
        if tick_established is None:
            return
        ok = self.api.create_active_trade_route(
            buyer_country_id,
            seller_country_id,
            goods_id,
            quantity,
            tick_established,
            route_efficiency,
        )
        if not ok:
            messagebox.showerror("Insert failed", "Could not create trade route. Check backend.log.")
            return
        self.table_select.set("ActiveTradeRoute")
        self.show_selected_table()
    def start_war_dialog(self):
        war_name = self._prompt_str("Start war", "War name")
        if not war_name:
            return
        start_tick = self._prompt_int("Start war", "Start tick")
        if start_tick is None:
            return
        participants: List[Dict[str, Any]] = []
        while True:
            cid = self._pick_country_id("War participant", "Select participant country (Cancel to stop)")
            if cid is None:
                break
            if any(p["country_id"] == cid for p in participants):
                messagebox.showerror("Duplicate participant", "This country is already added.")
                continue
            is_attacker = messagebox.askyesno("War participant side", f"Is country {cid} an attacker?")
            participants.append({"country_id": cid, "is_attacker": is_attacker})
        if len(participants) < 2:
            messagebox.showerror("Not enough participants", "Please add at least 2 participant countries.")
            return
        ok = self.api.start_war(war_name, start_tick, participants)
        if not ok:
            messagebox.showerror("Insert failed", "Could not start war. Check backend.log.")
            return
        self.table_select.set("War")
        self.show_selected_table()
    def _get_selected_row_dict(self) -> Optional[Dict[str, Any]]:
        sel = self.table.selection()
        if not sel:
            return None
        item_id = sel[0]
        values = self.table.item(item_id, "values")
        cols = list(self.table["columns"])
        if not cols or len(values) != len(cols):
            return None
        return dict(zip(cols, values))
    def on_double_click_edit(self, event): #This gives us the power to double click on something and edit values on the fly
        if not self._current_table_name:
            return
        region = self.table.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.table.identify_row(event.y)
        col_id = self.table.identify_column(event.x)
        if not row_id or not col_id:
            return
        col_index = int(col_id.replace("#", "")) - 1
        columns = list(self.table["columns"])
        if col_index < 0 or col_index >= len(columns):
            return
        col_name = columns[col_index]
        row = self._get_selected_row_dict()
        if not row:
            self.table.selection_set(row_id)
            row = self._get_selected_row_dict()
        if not row:
            return
        try:
            pk_cols = self.api.get_table_primary_key_columns(self._current_table_name)
        except Exception as e:
            messagebox.showerror("DB error", str(e))
            return
        if not pk_cols:
            messagebox.showerror("Not editable", f"Table '{self._current_table_name}' has no primary key.")
            return
        if col_name in pk_cols:
            messagebox.showerror("Not editable", "Editing primary key columns is disabled.")
            return
        pk_values: Dict[str, Any] = {}
        for pk in pk_cols:
            if pk not in row:
                messagebox.showerror("Cannot edit", f"Selected row missing primary key column '{pk}'.")
                return
            pk_values[pk] = row[pk]
        current_val = row.get(col_name, "")
        new_val = simpledialog.askstring(
            "Edit cell",
            f"{self._current_table_name}.{col_name}\nPK={pk_values}\n\nNew value (blank = NULL):",
            initialvalue=str(current_val),
            parent=self.root,
        )
        if new_val is None:
            return
        new_val = new_val.strip()
        value: Any = None if new_val == "" else new_val
        try:
            ok = self.api.update_cell(self._current_table_name, pk_values, col_name, value)
        except Exception as e:
            messagebox.showerror("Update failed", str(e))
            return
        if not ok:
            messagebox.showerror("Update failed", "Could not update value. Check backend.log.")
            return
        self.show_selected_table()
    def on_delete_row(self, event):
        if not self._current_table_name:
            return
        row = self._get_selected_row_dict()
        if not row:
            return
        try:
            pk_cols = self.api.get_table_primary_key_columns(self._current_table_name)
        except Exception as e:
            messagebox.showerror("DB error", str(e))
            return
        if not pk_cols:
            messagebox.showerror("Cannot delete", f"Table '{self._current_table_name}' has no primary key.")
            return
        pk_values = {pk: row.get(pk) for pk in pk_cols}
        if any(pk_values[pk] is None for pk in pk_cols):
            messagebox.showerror("Cannot delete", "Selected row missing primary key values.")
            return
        if not messagebox.askyesno("Confirm delete", f"Delete from {self._current_table_name} where {pk_values}?"):
            return
        try:
            ok = self.api.delete_row(self._current_table_name, pk_values)
        except Exception as e:
            messagebox.showerror("Delete failed", str(e))
            return
        if not ok:
            messagebox.showerror("Delete failed", "Could not delete row. Check backend.log.")
            return
        self.show_selected_table()
    def on_close(self):
        self.api.cleanup()
        self.root.destroy()