import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import sqlite3
from datetime import datetime

import requests

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.text = ""

    def show(self, text, x, y):
        self.text = text
        if self.tipwindow or not text:
            return

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # no window chrome
        tw.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            tw,
            text=text,
            justify="left",
            padding=(8, 6),
            relief="solid",
            borderwidth=1
        )
        label.pack()

    def hide(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


DB_FILE = "tools.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            tool_id TEXT PRIMARY KEY,
            borrower TEXT NOT NULL,
            borrowed_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_all_loans():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT tool_id, borrower FROM loans")
    rows = cur.fetchall()
    conn.close()
    return {tool_id: borrower for tool_id, borrower in rows}


def borrow_tool(tool_id: str, borrower: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO loans (tool_id, borrower, borrowed_at) VALUES (?, ?, ?)",
        (tool_id, borrower, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def return_tool(tool_id: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM loans WHERE tool_id = ?", (tool_id,))
    conn.commit()
    conn.close()


# --- Fake in-memory data (Milestone #1 friendly) ---
TOOLS = [
    {"id": "T001", "name": "Cordless Drill", "description": "Battery-powered drill for drilling holes and driving screws into wood or metal."},
    {"id": "T002", "name": "Hammer", "description": "General-purpose claw hammer for driving nails and removing them."},
    {"id": "T003", "name": "Screwdriver Set", "description": "Set of Phillips and flathead screwdrivers in multiple sizes."},
    {"id": "T004", "name": "Tape Measure", "description": "Retractable tape for measuring length and distance (imperial/metric markings)."},
    {"id": "T005", "name": "Hex Key Set", "description": "Allen key set for hex socket screws; includes multiple sizes."},
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Workshop Tool Tracker")
        self.geometry("900x520")
        self.minsize(750, 450)

        # store login info
        self.access_token = None
        self.username = None

        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for Page in (LoginPage, CreateAccountPage, HomePage, ToolsPage):
            frame = Page(parent=container, controller=self)
            self.frames[Page.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.show_frame("LoginPage")

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.tkraise()
        # Let pages refresh themselves on entry if they want
        if hasattr(frame, "on_show"):
            frame.on_show()


class LoginPage(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Login", font=("Segoe UI", 18, "bold")).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var, width=25).grid(row=0, column=1)

        ttk.Label(form, text="Password").grid(row=1, column=0, sticky="w")
        self.password_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.password_var, show="*", width=25).grid(row=1, column=1)

        ttk.Button(self, text="Login", command=self.login).pack(pady=10)

        ttk.Button(
            self,
            text="Create Account",
            command=lambda: controller.show_frame("CreateAccountPage"),
        ).pack()

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var).pack(pady=5)

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            self.status_var.set("Enter username and password.")
            return

        try:
            resp = requests.post(
                "http://127.0.0.1:6900/login",
                json={"username": username, "password": password},
                timeout=5
            )

            data = resp.json()

            if resp.status_code == 200 and data.get("ok"):
                self.controller.access_token = data["access_token"]
                self.controller.username = username
                self.controller.show_frame("HomePage")
            else:
                self.status_var.set("Login failed.")

        except Exception:
            self.status_var.set("Account service not reachable.")


class CreateAccountPage(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Create Account", font=("Segoe UI", 18, "bold")).pack(pady=10)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Username").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var, width=25).grid(row=0, column=1)

        ttk.Label(form, text="Password").grid(row=1, column=0, sticky="w")
        self.password_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.password_var, show="*", width=25).grid(row=1, column=1)

        ttk.Button(self, text="Create Account", command=self.create_account).pack(pady=10)

        ttk.Button(
            self,
            text="Back to Login",
            command=lambda: controller.show_frame("LoginPage"),
        ).pack()

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var).pack(pady=5)

    def create_account(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            self.status_var.set("Enter username and password.")
            return

        try:
            resp = requests.post(
                "http://127.0.0.1:6900/accounts",
                json={"username": username, "password": password},
                timeout=5
            )

            data = resp.json()

            if resp.status_code == 201 and data.get("ok"):
                messagebox.showinfo("Success", "Account created. Please login.")
                self.controller.show_frame("LoginPage")
            else:
                self.status_var.set("Account creation failed.")

        except Exception:
            self.status_var.set("Account service not reachable.")


class HomePage(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        title = ttk.Label(self, text="Workshop Tool Checkout", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        desc = ttk.Label(
            self,
            text=(
                "Track which tools are available and who borrowed them.\n"
                "Step 1: View tools. Step 2: Select a tool and click Borrow (if available)."
            ),
            justify="left",
        )
        desc.pack(anchor="w", pady=(0, 16))

        btn = ttk.Button(
            self,
            text="View available tools",
            command=lambda: controller.show_frame("ToolsPage"),
        )
        btn.pack(anchor="w")

        quit_btn = ttk.Button(self, text="Quit", command=self.controller.destroy)
        quit_btn.pack(anchor="w", pady=(16, 0))


class ToolsPage(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        header_row = ttk.Frame(self)
        header_row.pack(fill="x", pady=(0, 10))

        title = ttk.Label(header_row, text="Tools", font=("Segoe UI", 16, "bold"))
        title.pack(side="left")

        instructions = ttk.Frame(self, padding=(8, 6))
        instructions.pack(fill="x", pady=(0, 10))
        instructions_text = (
            "How to borrow or return a tool\n\n"
            "1. Browse the list below to see which tools are available or currently borrowed.\n"
            "2. Click a tool to select it.\n"
            "3. Use the 'Borrow selected tool' or 'Return selected tool' buttons, "
            "or double-click a tool to quickly borrow or return it.\n\n"
            "A confirmation will appear before any change is made."
        )

        instructions_label = ttk.Label(
            instructions,
            text=instructions_text,
            justify="left",
            wraplength=760
        )
        instructions_label.pack(anchor="w")

        back_btn = ttk.Button(header_row, text="Back", command=lambda: controller.show_frame("HomePage"))
        back_btn.pack(side="right")

        # Actions row
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 8))

        ttk.Label(actions, text="Borrower name (for demo):").pack(side="left")
        self.borrower_var = tk.StringVar(value="Lawrence")
        borrower_entry = ttk.Entry(actions, textvariable=self.borrower_var, width=20)
        borrower_entry.pack(side="left", padx=(8, 16))

        self.borrow_btn = ttk.Button(actions, text="Borrow selected tool", command=self.borrow_selected)
        self.borrow_btn.pack(side="left")

        self.return_btn = ttk.Button(actions, text="Return selected tool", command=self.return_selected)
        self.return_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Select a tool to see its status.")
        status_lbl = ttk.Label(actions, textvariable=self.status_var)
        status_lbl.pack(side="left", padx=(16, 0))

        # Table container
        table_frame = ttk.Frame(self, padding=8, relief="groove")
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "details", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Tool")
        self.tree.heading("status", text="Status")
        self.tree.heading("details", text="Details")
        self.tree.column("name", width=400, anchor="w")
        self.tree.column("status", width=200, anchor="w")
        self.tree.column("details", width=90, anchor="center")

        self.tooltip = ToolTip(self.tree)
        self._tooltip_open_for = None  # track which tool_id is currently showing

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Events
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.bind_all("<Return>", self.on_enter_key)  # keyboard interaction (helpful for IH#7)
        self.tree.bind("<Motion>", self.on_tree_hover)
        self.tree.bind("<Leave>", self.on_tree_leave)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Initial population
        self.refresh_table()

    def on_show(self):
        # Refresh in case data changed while away
        self.refresh_table()

    def refresh_table(self):
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)

        borrowed = get_all_loans()

        # Insert tools (alphabetical by name)
        for tool in sorted(TOOLS, key=lambda t: t["name"].lower()):
            tool_id = tool["id"]
            name = tool["name"]
            if tool_id in borrowed:
                status = f"Currently borrowed ({borrowed[tool_id]})"
            else:
                status = "Available"
            self.tree.insert("", "end", iid=tool_id, values=(name, "View", status))

        # Update button state based on current selection
        self.update_borrow_button_state()

    def get_selected_tool_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return sel[0]

    def on_select(self, _event=None):
        tool_id = self.get_selected_tool_id()
        if tool_id is None:
            self.status_var.set("Select a tool to see its status.")
            self.update_borrow_button_state()
            return

        tool_name = next((t["name"] for t in TOOLS if t["id"] == tool_id), tool_id)
        borrowed = get_all_loans()
        if tool_id in borrowed:
            self.status_var.set(f"'{tool_name}' is currently borrowed.")
        else:
            self.status_var.set(f"'{tool_name}' is available.")
        self.update_borrow_button_state()

    def update_borrow_button_state(self):
        tool_id = self.get_selected_tool_id()
        if tool_id is None:
            self.borrow_btn.state(["disabled"])
            self.return_btn.state(["disabled"])
            return

        borrowed = get_all_loans()
        if tool_id in borrowed:
            self.borrow_btn.state(["disabled"])
            self.return_btn.state(["!disabled"])
        else:
            self.borrow_btn.state(["!disabled"])
            self.return_btn.state(["disabled"])

    def borrow_selected(self):
        tool_id = self.get_selected_tool_id()
        tool_name = next((t["name"] for t in TOOLS if t["id"] == tool_id), tool_id)

        confirmed = messagebox.askyesno(
            title="Confirm Checkout",
            message=(
                f"Are you sure you want to check out the {tool_name}?\n"
                "This action will mark the tool as checked out and require you to return it."
            ),
        )
        if not confirmed:
            self.status_var.set("Checkout cancelled.")
            return

        if tool_id is None:
            self.status_var.set("No tool selected.")
            return

        borrower = self.borrower_var.get().strip() or "Unknown"

        try:
            borrow_tool(tool_id, borrower)
        except sqlite3.IntegrityError:
            self.status_var.set("Cannot borrow: tool is already borrowed.")
            self.refresh_table()
            self.update_borrow_button_state()
            return

        tool_name = next((t["name"] for t in TOOLS if t["id"] == tool_id), tool_id)
        self.status_var.set(f"Borrowed! You borrowed '{tool_name}'.")
        self.refresh_table()
        self.tree.selection_set(tool_id)
        self.tree.focus(tool_id)
        self.update_borrow_button_state()

    def return_selected(self):
        tool_id = self.get_selected_tool_id()
        if tool_id is None:
            self.status_var.set("No tool selected.")
            return

        borrowed = get_all_loans()
        if tool_id not in borrowed:
            self.status_var.set("Cannot return: tool is not currently borrowed.")
            self.refresh_table()
            self.update_borrow_button_state()
            return

        tool_name = next((t["name"] for t in TOOLS if t["id"] == tool_id), tool_id)

        confirmed = messagebox.askyesno(
            title="Confirm Return",
            message=(
                f"Are you sure you want to return the {tool_name}?\n"
                "This action will mark the tool as returned. If you wish to use it again, "
                "you will need to check it out again."
            ),
        )
        if not confirmed:
            self.status_var.set("Return cancelled.")
            return

        return_tool(tool_id)

        tool_name = next((t["name"] for t in TOOLS if t["id"] == tool_id), tool_id)
        self.status_var.set(f"Returned '{tool_name}'.")
        self.refresh_table()
        self.tree.selection_set(tool_id)
        self.tree.focus(tool_id)
        self.update_borrow_button_state()

    def on_enter_key(self, _event=None):
        # Press Enter to borrow selected tool (if enabled)
        if "disabled" not in self.borrow_btn.state():
            self.borrow_selected()

    def on_tree_leave(self, _event=None):
        self.tooltip.hide()
        self._tooltip_open_for = None

    def on_tree_hover(self, event):
        # Identify which row/column the mouse is over
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)  # e.g. "#1", "#2", "#3"

        # We only show tooltip when hovering over the "Details" column (3rd column => "#3")
        if not row_id or col_id != "#2":
            self.tooltip.hide()
            self._tooltip_open_for = None
            return

        # Avoid recreating tooltip repeatedly while hovering the same cell
        if self._tooltip_open_for == row_id:
            return

        tool = next((t for t in TOOLS if t["id"] == row_id), None)
        desc = tool["description"] if tool else ""
        if not desc:
            self.tooltip.hide()
            self._tooltip_open_for = None
            return

        # Show tooltip near the cursor (use root coordinates)
        x = event.x_root + 12
        y = event.y_root + 12
        self.tooltip.hide()
        self.tooltip.show(desc, x, y)
        self._tooltip_open_for = row_id

    def on_tree_double_click(self, event):
        # Only act if a real row was double-clicked
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        # Select the row the user double-clicked (so UI stays consistent)
        self.tree.selection_set(row_id)
        self.tree.focus(row_id)

        borrowed = get_all_loans()
        if row_id in borrowed:
            # Double-click returns if currently borrowed
            self.return_selected()
        else:
            # Double-click borrows if available
            self.borrow_selected()


if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
