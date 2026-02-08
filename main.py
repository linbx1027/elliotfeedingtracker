import flet as ft
import os
from datetime import datetime
from supabase import create_client, Client

# --- SUPABASE CONFIG (REPLIT VERSION) ---
# Pulls directly from the Secrets tool (🔒) in the Replit sidebar
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if secrets are missing to prevent a crash
if not SUPABASE_URL or not SUPABASE_KEY:
    def main(page):
        page.add(ft.Text("Error: Please set SUPABASE_URL and SUPABASE_KEY in Replit Secrets!", color="red"))
    if __name__ == "__main__":
        ft.app(target=main)
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_data():
        weight_res = supabase.table("settings").select("value").eq("key", "weight").execute()
        weight = float(weight_res.data[0]['value']) if weight_res.data else 4.5
        
        today = datetime.now().strftime("%Y-%m-%d")
        feeds_res = supabase.table("feeds").select("*").eq("date", today).order("id", desc=True).execute()
        
        feeds = [(f['amount'], f['type'], f['time'], f['id']) for f in feeds_res.data]
        return weight, feeds

    def main(page):
        page.title = "Elliot's Baby Tracker"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.scroll = ft.ScrollMode.AUTO
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        FAMILY_PASSWORD = "Elliot" 

        # --- UI COMPONENTS ---
        weight_text = ft.Text(size=28, weight="bold")
        weight_edit_field = ft.TextField(label="New Weight", width=120, visible=False, suffix_text="kg")
        advice_text = ft.Text(color=ft.Colors.BLUE_GREY_600)
        total_text = ft.Text(size=18, weight="bold", color="blue")
        history_list = ft.Column(spacing=10)
        
        ml_input = ft.TextField(label="Amount (ml)", keyboard_type=ft.KeyboardType.NUMBER, width=150)
        time_input = ft.TextField(label="Time", value=datetime.now().strftime("%H:%M"), width=150)
        type_dropdown = ft.Dropdown(
            label="Milk Type", width=310, value="Formula",
            options=[ft.dropdown.Option("Formula"), ft.dropdown.Option("Breastmilk")]
        )

        def on_edit_weight(e):
            current_weight = weight_text.value.split(" ")[0]
            weight_edit_field.value = current_weight
            weight_text.visible = False
            edit_btn.visible = False
            weight_edit_field.visible = True
            save_weight_btn.visible = True
            page.update()

        def on_save_weight(e):
            if weight_edit_field.value:
                supabase.table("settings").update({"value": weight_edit_field.value}).eq("key", "weight").execute()
                weight_text.visible = True
                edit_btn.visible = True
                weight_edit_field.visible = False
                save_weight_btn.visible = False
                refresh_ui()

        edit_btn = ft.IconButton(icon=ft.Icons.EDIT, on_click=on_edit_weight, icon_size=20)
        save_weight_btn = ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, icon_color="green", on_click=on_save_weight, visible=False)

        def refresh_ui():
            weight, feeds = get_data()
            weight_text.value = f"{weight} kg"
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
                            ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, fid=f[3]: delete_feed(fid))
                        ]),
                        padding=10, bgcolor=ft.Colors.BLUE_50, border_radius=10
                    )
                )
            page.update()

        def delete_feed(feed_id):
            supabase.table("feeds").delete().eq("id", feed_id).execute()
            refresh_ui()

        def on_save_click(e):
            if ml_input.value:
                supabase.table("feeds").insert({
                    "amount": int(ml_input.value), "type": type_dropdown.value,
                    "time": time_input.value, "date": datetime.now().strftime("%Y-%m-%d")
                }).execute()
                ml_input.value = ""
                refresh_ui()
                page.show_snack_bar(ft.SnackBar(ft.Text("Feeding Logged!")))

        # --- LOGIN LOGIC ---
        pass_field = ft.TextField(label="Password", password=True, can_reveal_password=True, width=250)
        login_screen = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_PERSON, size=50, color="blue"),
                ft.Text("Say My Name", size=20, weight="bold"),
                pass_field,
                ft.ElevatedButton("Enter", on_click=lambda e: login_click())
            ], horizontal_alignment="center", spacing=20), padding=50
        )

        def login_click():
            if pass_field.value == FAMILY_PASSWORD:
                login_screen.visible = False
                main_app_screen.visible = True
                refresh_ui()
                page.update()
            else:
                pass_field.error_text = "Wrong Password"
                page.update()

        main_app_screen = ft.Column(visible=False, horizontal_alignment="center", controls=[
            ft.Text("Elliot's Tracker", size=24, weight="bold"),
            ft.Card(content=ft.Container(padding=20, content=ft.Column([
                ft.Row([weight_text, weight_edit_field, edit_btn, save_weight_btn], alignment="center"),
                ft.Row([advice_text], alignment="center"),
                ft.Row([total_text], alignment="center"),
            ]))),
            ft.Row([ml_input, time_input], alignment="center"),
            type_dropdown,
            ft.ElevatedButton("Save Entry", on_click=on_save_click, width=310, height=50, bgcolor="blue", color="white"),
            ft.Divider(),
            history_list
        ])

        page.add(login_screen, main_app_screen)

    if __name__ == "__main__":
        # Critical for Replit deployment
        ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.getenv("PORT", 8080)))
