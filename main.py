import flet as ft
import sqlite3
import os
from datetime import datetime

# --- DATABASE LOGIC ---
# Using a specific path for Replit persistence
DB_PATH = "baby_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS feeds (id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER, type TEXT, time TEXT, date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('weight', '3.5')")
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = 'weight'")
    weight = float(cur.fetchone()[0])
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT amount, type, time, id FROM feeds WHERE date = ? ORDER BY id DESC", (today,))
    feeds = cur.fetchall()
    conn.close()
    return weight, feeds

def main(page):
    init_db()
    page.title = "Our Baby Tracker"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- PASSWORD PROTECTION ---
    # Change '1234' to whatever password you want to give the caregiver
    FAMILY_PASSWORD = "Elliot" 

    # --- UI COMPONENTS ---
    weight_display = ft.Text(size=22, weight="bold")
    weight_input_field = ft.TextField(label="Edit Weight (kg)", width=120, visible=False)
    advice_text = ft.Text(color=ft.Colors.BLUE_GREY_600)
    total_text = ft.Text(size=18, weight="bold", color="blue")
    history_list = ft.Column(spacing=10)
    
    ml_input = ft.TextField(label="Amount (ml)", keyboard_type=ft.KeyboardType.NUMBER, width=150)
    time_input = ft.TextField(label="Time", value=datetime.now().strftime("%H:%M"), width=150)
    type_dropdown = ft.Dropdown(
        label="Milk Type",
        width=310,
        options=[ft.dropdown.Option("Formula"), ft.dropdown.Option("Breastmilk")],
        value="Formula"
    )

    log_view = ft.Column(visible=True, horizontal_alignment="center", spacing=20)
    history_view = ft.Column(visible=False, horizontal_alignment="center", spacing=20)

    # --- APP LOGIC ---
    def refresh_ui():
        weight, feeds = get_data()
        weight_display.value = f"{weight} kg"
        advice_text.value = f"Target: {int(weight*150)}ml - {int(weight*200)}ml / day"
        daily_total = sum(f[0] for f in feeds)
        total_text.value = f"Total Today: {daily_total}ml"
        
        history_list.controls.clear()
        for f in feeds:
            history_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.BABY_CHANGING_STATION, color="blue"),
                        ft.Column([ft.Text(f"{f[0]}ml {f[1]}", weight="bold"), ft.Text(f"at {f[2]}", size=12)], expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", 
                                     on_click=lambda e, fid=f[3]: delete_feed(fid))
                    ]),
                    padding=10, bgcolor=ft.Colors.BLUE_50, border_radius=10
                )
            )
        page.update()

    def delete_feed(feed_id):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        conn.commit()
        conn.close()
        refresh_ui()

    def on_save_click(e):
        if ml_input.value:
            conn = sqlite3.connect(DB_PATH)
            today = datetime.now().strftime("%Y-%m-%d")
            conn.execute("INSERT INTO feeds (amount, type, time, date) VALUES (?, ?, ?, ?)", 
                       (int(ml_input.value), type_dropdown.value, time_input.value, today))
            conn.commit()
            conn.close()
            ml_input.value = ""
            refresh_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Feeding Logged!")))

    def toggle_view(e):
        log_view.visible = not log_view.visible
        history_view.visible = not history_view.visible
        view_btn.text = "Back to Log" if history_view.visible else "View History"
        page.update()

    # --- LOGIN LOGIC ---
    def login_click(e):
        if pass_field.value == FAMILY_PASSWORD:
            login_screen.visible = False
            main_app_screen.visible = True
            refresh_ui()
            page.update()
        else:
            pass_field.error_text = "Wrong Password"
            page.update()

    # --- LOGIN UI ---
    pass_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=250)
    login_screen = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.LOCK_PERSON, size=50, color="blue"),
            ft.Text("Caregiver Access", size=20, weight="bold"),
            pass_field,
            ft.ElevatedButton("Enter Tracker", on_click=login_click, width=250)
        ], horizontal_alignment="center", spacing=20),
        padding=50
    )

    # --- MAIN UI STRUCTURE ---
    view_btn = ft.OutlinedButton("View History", icon=ft.Icons.HISTORY, on_click=toggle_view, width=310)
    
    log_view.controls = [
        ft.Card(content=ft.Container(padding=20, content=ft.Column([
            ft.Row([weight_display], alignment="center"),
            ft.Row([advice_text], alignment="center"),
            ft.Row([total_text], alignment="center"),
        ]))),
        ft.Text("New Feeding", size=18, weight="bold"),
        ft.Row([ml_input, time_input], alignment="center"),
        type_dropdown,
        ft.ElevatedButton("Save Entry", on_click=on_save_click, width=310, height=50, bgcolor="blue", color="white"),
    ]
    
    history_view.controls = [ft.Text("Today's History", size=18, weight="bold"), history_list]

    main_app_screen = ft.Column(visible=False, controls=[
        ft.Row([ft.Text("Baby Tracker", size=24, weight="bold")], alignment="center"),
        view_btn,
        ft.Divider(),
        log_view,
        history_view
    ], horizontal_alignment="center")

    page.add(login_screen, main_app_screen)

# WEB LAUNCHER (Critical for Replit)
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.getenv("PORT", 8080)))
