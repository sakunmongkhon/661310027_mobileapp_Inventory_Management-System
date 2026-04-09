import flet as ft
import httpx
from datetime import date
import os

API_URL = "http://192.168.0.105:8000"

# ==================== COLORS ====================
PRIMARY = "#1B6B4A"
PRIMARY_LIGHT = "#2E8B57"
PRIMARY_SOFT = "#E8F5EE"
ACCENT = "#FF6B35"
DANGER = "#E53935"
WARNING = "#F9A825"
SUCCESS = "#2E7D32"
BG = "#F0F7F4"
CARD_BG = "#FFFFFF"
TEXT_DARK = "#1A2B22"
TEXT_SECONDARY = "#4A6B5A"
TEXT_GRAY = "#8CA89A"
BORDER = "#D4E8DC"
DARK_GREEN = "#0D3B24"

# ==================== GLOBAL STATE ====================
token = None
user_role = None
user_name = None
user_profile_image = None

# ==================== API ====================
def api_headers():
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def api_get(path):
    try:
        r = httpx.get(f"{API_URL}{path}", headers=api_headers(), timeout=10)
        if r.status_code == 401: return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[GET ERROR] {path}: {e}")
        return None

def api_post(path, json=None, data=None, files=None):
    try:
        r = httpx.post(f"{API_URL}{path}", headers=api_headers(), json=json, data=data, files=files, timeout=10)
        if r.status_code == 401: return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[POST ERROR] {path}: {e}")
        return None

def api_put(path, json=None):
    try:
        r = httpx.put(f"{API_URL}{path}", headers=api_headers(), json=json, timeout=10)
        if r.status_code == 401:
            print(f"[PUT ERROR 401] {path}: Unauthorized")
            return None
        try:
            r.raise_for_status()
        except Exception as ex:
            print(f"[PUT ERROR] {path}: {ex}")
            print(f"[PUT ERROR BODY] {r.text}")
            return None
        return r.json()
    except Exception as e:
        print(f"[PUT ERROR EXCEPTION] {path}: {e}")
        return None

def api_delete(path):
    try:
        r = httpx.delete(f"{API_URL}{path}", headers=api_headers(), timeout=10)
        if r.status_code == 401: return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[DELETE ERROR] {path}: {e}")
        return None

# ==================== COMPONENTS ====================
def make_card(content, padding=16, radius=20, on_click=None, ink=False):
    return ft.Container(
        content=content,
        bgcolor=CARD_BG,
        border_radius=radius,
        padding=padding,
        shadow=ft.BoxShadow(blur_radius=12, color="#0D000000", offset=ft.Offset(0, 3)),
        margin=ft.margin.only(bottom=12),
        on_click=on_click,
        ink=ink,
    )

def pill_button(text, on_click, icon=None, bgcolor=PRIMARY, text_color="white", width=None, height=48):
    controls = []
    if icon:
        controls.append(ft.Icon(icon, color=text_color, size=18))
    controls.append(ft.Text(text, color=text_color, size=14, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(controls, spacing=8, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bgcolor,
        border_radius=14,
        padding=ft.padding.symmetric(vertical=12, horizontal=24),
        width=width,
        height=height,
        on_click=on_click,
        ink=True,
    )

def outlined_button(text, on_click, icon=None, color=PRIMARY):
    controls = []
    if icon:
        controls.append(ft.Icon(icon, color=color, size=16))
    controls.append(ft.Text(text, color=color, size=13, weight=ft.FontWeight.W_500))
    return ft.Container(
        content=ft.Row(controls, spacing=6, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        border=ft.border.all(1.5, color),
        border_radius=12,
        padding=ft.padding.symmetric(vertical=8, horizontal=16),
        on_click=on_click,
        ink=True,
    )

def dark_button(text, on_click, icon=None, width=None):
    """ปุ่มสีดำแบบในรูป"""
    controls = []
    if icon:
        controls.append(ft.Icon(icon, color="white", size=14))
    controls.append(ft.Text(text, color="white", size=12, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(controls, spacing=6, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=TEXT_DARK,
        border_radius=18,
        padding=ft.padding.symmetric(vertical=7, horizontal=14),
        width=width,
        on_click=on_click,
        ink=True,
    )

def outline_dark_button(text, on_click, icon=None, width=None):
    """ปุ่มขอบดำแบบในรูป"""
    controls = []
    if icon:
        controls.append(ft.Icon(icon, color=TEXT_DARK, size=14))
    controls.append(ft.Text(text, color=TEXT_DARK, size=12, weight=ft.FontWeight.W_600))
    return ft.Container(
        content=ft.Row(controls, spacing=6, tight=True, alignment=ft.MainAxisAlignment.CENTER),
        border=ft.border.all(1.2, TEXT_DARK),
        border_radius=18,
        padding=ft.padding.symmetric(vertical=7, horizontal=14),
        width=width,
        on_click=on_click,
        ink=True,
    )

def input_field(label, value="", password=False, hint="", multiline=False, prefix_icon=None):
    return ft.TextField(
        label=label,
        value=value,
        password=password,
        can_reveal_password=password,
        hint_text=hint,
        multiline=multiline,
        min_lines=1,
        max_lines=3 if multiline else 1,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=14,
        prefix_icon=prefix_icon,
        content_padding=ft.padding.symmetric(vertical=14, horizontal=16),
        text_size=14,
    )

def expiry_badge(days):
    if days is None:
        bg, text, color = TEXT_GRAY, "-", "white"
    elif days < 0:
        bg, text, color = DANGER, "หมดอายุ", "white"
    elif days <= 30:
        bg, text, color = WARNING, f"{days} วัน", "white"
    else:
        bg, text, color = SUCCESS, f"{days} วัน", "white"
    return ft.Container(
        content=ft.Text(text, size=11, color=color, weight=ft.FontWeight.BOLD),
        bgcolor=bg, border_radius=20,
        padding=ft.padding.symmetric(vertical=4, horizontal=10)
    )

def show_snack(page, message, success=True):
    page.snack_bar = ft.SnackBar(
        ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE if success else ft.Icons.ERROR, color="white", size=20),
            ft.Text(message, color="white", size=13),
        ], spacing=8),
        bgcolor=SUCCESS if success else DANGER,
    )
    page.snack_bar.open = True
    page.update()

def close_dialog(page, dlg):
    dlg.open = False
    page.update()

# ==================== MEDICINE GRID CARD ====================
def medicine_grid_card(m, on_tap):
    total = m.get("total_stock", 0)
    img_path = m.get("image_path")
    stock_color = DANGER if total < m["min_stock"] else TEXT_DARK

    if img_path:
        image_widget = ft.Image(
            src=f"{API_URL}{img_path}",
            fit="cover",
            expand=1,
            height=150,
        )
    else:
        image_widget = ft.Container(
            content=ft.Icon(ft.Icons.MEDICATION, color=PRIMARY, size=44),
            bgcolor=PRIMARY_SOFT,
            border_radius=12, expand=1,
        )

    # Expiry badge มุมบนซ้าย (days left)
    expiry_days = m.get("expiry_days")
    badge = expiry_badge(expiry_days) if expiry_days is not None else None

    # Badge overlays directly on image, not gray area
    stack_content = [
        ft.Container(
            content=image_widget,
            expand=1,
        )
    ]
    if badge:
        stack_content.append(
            ft.Container(
                content=badge,
                left=0, top=0,
                alignment=ft.alignment.top_left,
                padding=ft.padding.only(left=4, top=4)
            )
        )

    return ft.Container(
        content=ft.Column([
            # ส่วนรูปภาพ
            ft.Container(
                content=ft.Stack(stack_content),
                bgcolor="#F5F5F5",
                border_radius=ft.border_radius.only(top_left=18, top_right=18),
                height=150,
                padding=0,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
            # ส่วนข้อมูล
            ft.Container(
                content=ft.Column([
                    ft.Text(m["name"], size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(m.get("category_name") or "ทั่วไป", size=12, color=TEXT_GRAY),
                    ft.Container(height=4),
                    ft.Text(f"คงเหลือ {total} {m.get('unit', 'เม็ด')}", size=13, color=stock_color, weight=ft.FontWeight.W_600),
                ], spacing=2),
                padding=ft.padding.only(left=10, right=10, bottom=14, top=10),
            ),
        ], spacing=0),
        bgcolor=CARD_BG,
        border_radius=18,
        shadow=ft.BoxShadow(blur_radius=10, color="#0A000000", offset=ft.Offset(0, 2)),
        on_click=on_tap,
        ink=True,
        expand=1,
        height=250,
    )

# ==================== LOGIN PAGE ====================
# ==================== LOGIN PAGE ====================
def login_page(page: ft.Page):
    global token, user_role, user_name
    page.controls.clear()

    username_field = ft.TextField(
        hint_text="Username",
        hint_style=ft.TextStyle(color="#999999", size=16),
        bgcolor="#FFFFFFCC", border_radius=30,
        border_color="transparent", focused_border_color="transparent",
        content_padding=ft.padding.symmetric(vertical=14, horizontal=20),
        text_size=16, width=300,
    )
    password_field = ft.TextField(
        hint_text="Password", password=True, can_reveal_password=True,
        hint_style=ft.TextStyle(color="#999999", size=16),
        bgcolor="#FFFFFFCC", border_radius=30,
        border_color="transparent", focused_border_color="transparent",
        content_padding=ft.padding.symmetric(vertical=14, horizontal=20),
        text_size=16, width=300,
    )
    error_text = ft.Text("", color="#FF5555", size=13, text_align=ft.TextAlign.CENTER)

    def do_login(e):
        global token, user_role, user_name
        un = username_field.value.strip()
        pw = password_field.value.strip()
        if not un or not pw:
            error_text.value = "กรุณากรอกข้อมูลให้ครบ"; page.update(); return
        try:
            r = httpx.post(f"{API_URL}/auth/login", data={"username": un, "password": pw}, timeout=10)
            if r.status_code == 200:
                d = r.json()
                token = d["access_token"]; user_role = d["role"]; user_name = d["full_name"]
                main_page(page)
            else:
                error_text.value = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"; page.update()
        except Exception:
            error_text.value = "ไม่สามารถเชื่อมต่อ Server ได้"; page.update()

    def admin_login(e):
        global token, user_role, user_name
        try:
            r = httpx.post(f"{API_URL}/auth/admin-login", timeout=10)
            if r.status_code == 200:
                d = r.json()
                token = d["access_token"]; user_role = d["role"]; user_name = d["full_name"]
                main_page(page)
            else:
                error_text.value = "Admin login ล้มเหลว"; page.update()
        except Exception:
            error_text.value = "ไม่สามารถเชื่อมต่อ Server ได้"; page.update()

    login_btn = ft.Container(
        content=ft.Text("Login", size=18, weight=ft.FontWeight.BOLD,
                        color="white", text_align=ft.TextAlign.CENTER),
        width=160, height=48,
        border=ft.border.all(2, "white"), border_radius=30,
        alignment=ft.alignment.Alignment(0, 0),
        on_click=do_login, ink=True,
    )

    bg = ft.Image(
        src=f"{API_URL}/image/login_register.png",
        fit="cover",
        expand=True,
        width=420,
        height=900,
    )

    content = ft.Container(
        content=ft.Column([
            ft.Container(expand=5),
            username_field,
            ft.Container(height=12),
            password_field,
            ft.Container(height=6),
            error_text,
            ft.Container(height=16),
            login_btn,
            ft.Container(height=24),
            ft.Container(
                content=ft.Text("register", size=14, color="white", weight=ft.FontWeight.W_500),
                on_click=lambda e: register_page(page), ink=True,
            ),
            ft.Container(height=4),
            ft.Container(
                content=ft.Text("เข้าสู่ระบบโดย admin", size=14, color="#FFFFFFAA"),
                on_click=admin_login, ink=True,
            ),
            ft.Container(height=20),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        expand=True,
        padding=ft.padding.symmetric(horizontal=40),
    )

    page.add(ft.Stack([bg, content], expand=True))
    page.update()


# ==================== REGISTER PAGE ====================
def register_page(page: ft.Page):
    page.controls.clear()

    fullname_f = ft.TextField(
        hint_text="Full Name",
        hint_style=ft.TextStyle(color="#999999", size=16),
        bgcolor="#FFFFFFCC", border_radius=30,
        border_color="transparent", focused_border_color="transparent",
        content_padding=ft.padding.symmetric(vertical=14, horizontal=20),
        text_size=16, width=300,
    )
    username_f = ft.TextField(
        hint_text="Username",
        hint_style=ft.TextStyle(color="#999999", size=16),
        bgcolor="#FFFFFFCC", border_radius=30,
        border_color="transparent", focused_border_color="transparent",
        content_padding=ft.padding.symmetric(vertical=14, horizontal=20),
        text_size=16, width=300,
    )
    password_f = ft.TextField(
        hint_text="Password", password=True, can_reveal_password=True,
        hint_style=ft.TextStyle(color="#999999", size=16),
        bgcolor="#FFFFFFCC", border_radius=30,
        border_color="transparent", focused_border_color="transparent",
        content_padding=ft.padding.symmetric(vertical=14, horizontal=20),
        text_size=16, width=300,
    )
    error_t = ft.Text("", color="#FF5555", size=13, text_align=ft.TextAlign.CENTER)

    def do_register(e):
        un = username_f.value.strip()
        pw = password_f.value.strip()
        fn = fullname_f.value.strip()
        if not un or not pw or not fn:
            error_t.value = "กรุณากรอกข้อมูลให้ครบ"; page.update(); return
        try:
            r = httpx.post(f"{API_URL}/auth/register",
                           json={"username": un, "password": pw, "full_name": fn}, timeout=10)
            if r.status_code == 201:
                show_snack(page, "สมัครสมาชิกสำเร็จ"); login_page(page)
            else:
                try: detail = r.json().get("detail", "สมัครไม่สำเร็จ")
                except: detail = "สมัครไม่สำเร็จ"
                error_t.value = detail; page.update()
        except Exception as ex:
            error_t.value = f"เกิดข้อผิดพลาด: {ex}"; page.update()

    register_btn = ft.Container(
        content=ft.Text("Register", size=18, weight=ft.FontWeight.BOLD,
                        color="white", text_align=ft.TextAlign.CENTER),
        width=160, height=48,
        border=ft.border.all(2, "white"), border_radius=30,
        alignment=ft.alignment.Alignment(0, 0),
        on_click=do_register, ink=True,
    )

    bg = ft.Image(
        src=f"{API_URL}/image/login_register.png",
        fit="cover",
        expand=True,
        width=420,
        height=900,
    )
    content = ft.Container(
        content=ft.Column([
            ft.Container(expand=5),
            fullname_f,
            ft.Container(height=12),
            username_f,
            ft.Container(height=12),
            password_f,
            ft.Container(height=6),
            error_t,
            ft.Container(height=16),
            register_btn,
            ft.Container(height=24),
            ft.Container(
                content=ft.Text("กลับไปหน้า Login", size=14, color="white", weight=ft.FontWeight.W_500),
                on_click=lambda e: login_page(page), ink=True,
            ),
            ft.Container(height=20),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        expand=True,
        padding=ft.padding.symmetric(horizontal=40),
    )

    page.add(ft.Stack([bg, content], expand=True))
    page.update()
# ==================== PROFILE PAGE ====================
NAVY = "#1A2250"
NAVY_LIGHT = "#2A3270"


def profile_menu_item(icon, label, on_click=None):
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, color=NAVY, size=22),
            ft.Text(label, size=15, weight=ft.FontWeight.W_500, color=TEXT_DARK, expand=True),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_GRAY, size=20),
        ], spacing=14),
        padding=ft.padding.symmetric(vertical=14, horizontal=6),
        on_click=on_click,
        ink=True,
    )


def profile_page(page: ft.Page):
    global token, user_role, user_name, user_profile_image
    page.controls.clear()

    def do_logout(e):
        global token, user_role, user_name
        token = None; user_role = None; user_name = None
        login_page(page)

    def go_edit(e):
        edit_profile_page(page)

    if user_profile_image:
        avatar = ft.CircleAvatar(foreground_image_src=user_profile_image, radius=48)
    else:
        avatar = ft.CircleAvatar(
            content=ft.Text((user_name or "?")[0].upper(), size=30, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor=PRIMARY, radius=48,
        )

    menu_items = ft.Container(
        content=ft.Column([
            profile_menu_item(ft.Icons.SETTINGS_OUTLINED, "Settings"),
            ft.Divider(height=1, color=BORDER),
            profile_menu_item(ft.Icons.SHOPPING_BAG_OUTLINED, "My Orders"),
            ft.Divider(height=1, color=BORDER),
            profile_menu_item(ft.Icons.LOCATION_ON_OUTLINED, "Address"),
            ft.Divider(height=1, color=BORDER),
            profile_menu_item(ft.Icons.LOCK_OUTLINE, "Change Password"),
            ft.Container(height=16),
            ft.Divider(height=1, color=BORDER),
            profile_menu_item(ft.Icons.HELP_OUTLINE, "Help & Support"),
            ft.Divider(height=1, color=BORDER),
            profile_menu_item(ft.Icons.LOGOUT, "Log out", on_click=do_logout),
        ], spacing=0),
        padding=ft.padding.symmetric(horizontal=20),
    )

    page.add(ft.Container(
        content=ft.Column([
            ft.Container(height=10),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color=TEXT_DARK, icon_size=20,
                              on_click=lambda e: main_page(page)),
                ft.Text("Profile", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK,
                         expand=True, text_align=ft.TextAlign.CENTER),
                ft.Container(width=40),
            ]),
            ft.Container(height=16),
            ft.Column([
                avatar,
                ft.Container(height=8),
                ft.Text(user_name or "-", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.Text(f"@{(user_name or 'user').lower().replace(' ', '')}", size=13, color=TEXT_GRAY),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "Edit Profile", bgcolor=NAVY, color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                    height=36, on_click=go_edit,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            ft.Container(height=24),
            ft.Divider(height=1, color=BORDER),
            menu_items,
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD_BG, expand=True, padding=ft.padding.only(top=20),
    ))
    page.update()


# ==================== EDIT PROFILE PAGE ====================
def edit_profile_page(page: ft.Page):
    page.controls.clear()

    full_name = ft.TextField(
        label="Full name", value=user_name or "", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    gender = ft.TextField(
        label="Gender", value="", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    birthdate = ft.TextField(
        label="Birthdate", value="", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    number = ft.TextField(
        label="Number", value="", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    email = ft.TextField(
        label="Email", value="", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    username = ft.TextField(
        label="Username", value=(user_name or "").lower().replace(" ", ""), border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))
    profile_img_field = ft.TextField(
        label="Profile Image Path/URL", value=user_profile_image or "", border_color=NAVY,
        focused_border_color=NAVY, label_style=ft.TextStyle(color=NAVY, size=12),
        border_radius=12, content_padding=ft.padding.symmetric(horizontal=14, vertical=12))

    if user_profile_image:
        avatar_edit = ft.CircleAvatar(
            foreground_image_src=user_profile_image, bgcolor=PRIMARY, radius=44)
    else:
        avatar_edit = ft.CircleAvatar(
            content=ft.Text((user_name or "?")[0].upper(), size=26, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor=PRIMARY, radius=44)

    def save_click(e):
        global user_name, user_profile_image
        if full_name.value.strip():
            user_name = full_name.value.strip()
        if profile_img_field.value.strip():
            user_profile_image = profile_img_field.value.strip()
        show_snack(page, "บันทึกสำเร็จ", success=True)
        profile_page(page)

    page.add(ft.Container(
        content=ft.Column([
            ft.Container(height=10),
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color=TEXT_DARK, icon_size=20,
                              on_click=lambda e: profile_page(page)),
                ft.Text("Edit Profile", size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK,
                         expand=True, text_align=ft.TextAlign.CENTER),
                ft.Container(width=40),
            ]),
            ft.Container(height=16),
            ft.Row([avatar_edit], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            profile_img_field,
            ft.Container(height=10),
            full_name,
            ft.Row([
                ft.Container(content=gender, expand=True),
                ft.Container(content=birthdate, expand=True),
            ], spacing=12),
            number, email, username,
            ft.Container(expand=True),
            ft.Container(
                content=ft.ElevatedButton(
                    "Save", bgcolor=NAVY, color="white", width=360, height=50,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=save_click,
                ),
                padding=ft.padding.only(bottom=24),
                alignment=ft.alignment.Alignment(0, 0),
            ),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD_BG, expand=True,
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
    ))
    page.update()

# ==================== MAIN PAGE ====================
def main_page(page: ft.Page):
    try:
        page.controls.clear()
        body = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

        # ======= หน้าหลัก: การ์ด grid =======
        # --- State for search ---
        search_value = ft.Ref[ft.TextField]()
        all_medicines = []

        def filter_medicines():
            q = (search_value.current.value or "").strip().lower()
            if not q:
                return all_medicines
            return [m for m in all_medicines if q in m["name"].lower() or (m.get("generic_name") or "").lower().find(q) != -1]

        def update_grid():
            medicines = filter_medicines()
            # Sort by expiry_days ascending (expired/close first, None last)
            def expiry_sort_key(m):
                days = m.get("expiry_days")
                if days is None:
                    return (1, 9999)
                return (0, days)
            medicines.sort(key=expiry_sort_key)

            grid_rows = []
            for i in range(0, len(medicines), 2):
                row_cards = []
                for j in range(2):
                    if i + j < len(medicines):
                        med = medicines[i + j]
                        def on_tap(e, m=med):
                            show_medicine_detail(page, m, load_dashboard)
                        row_cards.append(medicine_grid_card(med, on_tap))
                    else:
                        row_cards.append(ft.Container(expand=1))
                grid_rows.append(
                    ft.Container(
                        content=ft.Row(row_cards, spacing=14),
                        margin=ft.margin.only(bottom=14),
                    )
                )
            # Remove old grid and add new
            # body.controls[4:] = ...
            # Find index after search bar
            idx = 4
            while len(body.controls) > idx:
                body.controls.pop()
            body.controls.extend([
                *grid_rows,
                *([] if grid_rows else [
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.MEDICATION_OUTLINED, color=TEXT_GRAY, size=48),
                            ft.Text("ยังไม่มีรายการยา", color=TEXT_GRAY, size=14),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        padding=40,
                    )
                ]),
            ])
            page.update()

        def on_search_change(e):
            update_grid()

        def load_dashboard():
            body.controls.clear()
            nonlocal all_medicines
            all_medicines = api_get("/medicines") or []

            header = ft.Row([
                ft.Column([
                    ft.Text("PHAMACY", size=22, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text("จัดการสต็อกยาอย่างง่ายดาย", size=12, color=TEXT_GRAY),
                ], expand=True, spacing=2),
                ft.Container(
                    content=ft.Text((user_name or "?")[0].upper(), size=16, weight=ft.FontWeight.BOLD, color="white"),
                    bgcolor=PRIMARY, border_radius=22, width=44, height=44,
                ),
            ])

            banner = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("จัดการคลังยา", size=15, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text("ตรวจสอบสต็อกและวันหมดอายุ", size=11, color="#FFFFFFCC"),
                        ft.Container(height=8),
                        ft.Container(
                            content=ft.Text("+ เพิ่มยาใหม่", size=12, color=PRIMARY, weight=ft.FontWeight.W_600),
                            bgcolor="white", border_radius=10,
                            padding=ft.padding.symmetric(vertical=8, horizontal=16),
                            on_click=lambda e: show_medicine_dialog(page, None, load_dashboard),
                            ink=True,
                        ),
                    ], expand=True, spacing=2),
                    ft.Icon(ft.Icons.INVENTORY_2, color="#FFFFFF44", size=56),
                ], spacing=12),
                bgcolor=DARK_GREEN, border_radius=20, padding=20,
                margin=ft.margin.only(top=12, bottom=16),
            )

            search_bar = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SEARCH, color=TEXT_GRAY, size=20),
                    ft.TextField(
                        ref=search_value,
                        hint_text="ค้นหายา...",
                        border_color=BORDER,
                        focused_border_color=PRIMARY,
                        border_radius=14,
                        content_padding=ft.padding.symmetric(vertical=0, horizontal=8),
                        text_size=14,
                        on_change=on_search_change,
                        expand=True,
                    ),
                ], spacing=10),
                bgcolor=CARD_BG, border=ft.border.all(1, BORDER),
                border_radius=14, padding=ft.padding.symmetric(vertical=10, horizontal=16),
                margin=ft.margin.only(bottom=16),
            )

            body.controls.extend([
                ft.Container(height=8),
                header, banner, search_bar,
                ft.Container(height=14),
            ])
            update_grid()
            page.update()

        # ======= แจ้งเตือน + สถิติ =======
# ======= แจ้งเตือน + สถิติ =======
        def load_notifications():
            body.controls.clear()
            data = api_get("/dashboard") or {}
            noti_grouped = api_get("/notifications/grouped") or {"unresolved": [], "resolved": []}
            data = api_get("/dashboard") or {}
            noti_grouped = api_get("/notifications/grouped") or {"unresolved": [], "resolved": []}
            medicines = api_get("/medicines") or []
            med_map = {m["id"]: m for m in medicines}

            # ── Stat Box ──
            def stat_box(label, value, icon):
                return ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(icon, color="white", size=18),
                            bgcolor=ft.Colors.with_opacity(0.18, "white"),
                            border_radius=10,
                            width=36, height=36,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color="white"),
                        ft.Text(label, size=9,
                                color=ft.Colors.with_opacity(0.75, "white"),
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=ft.Colors.with_opacity(0.15, "white"),
                    border_radius=14,
                    padding=ft.padding.symmetric(vertical=12, horizontal=4),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.12, "white")),
                    expand=1,
                )

            # ── Noti Card ──
            def make_noti_card(n):
                med = med_map.get(n.get("medicine_id")) if n.get("medicine_id") else None
                msg = n.get("message", "")
                is_resolved = n.get("is_resolved", False)

                if med and med.get("image_path"):
                    img_content = ft.Image(
                        src=f"{API_URL}{med['image_path']}",
                        width=62, height=62, fit="cover",
                    )
                    img_bg = "#F5F5F5"
                elif "หมดอายุ" in msg and "ใกล้" not in msg:
                    img_content = ft.Icon(ft.Icons.CANCEL_OUTLINED, color=DANGER, size=30)
                    img_bg = "#FFEBEE"
                elif "ใกล้" in msg or "อายุ" in msg:
                    img_content = ft.Icon(ft.Icons.SCHEDULE, color=WARNING, size=30)
                    img_bg = "#FFF3E0"
                elif "สต็อก" in msg or "ต่ำ" in msg:
                    img_content = ft.Icon(ft.Icons.SHOW_CHART, color=ACCENT, size=30)
                    img_bg = "#FFF3E0"
                else:
                    img_content = ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, color=PRIMARY, size=30)
                    img_bg = PRIMARY_SOFT

                def on_tap(e, n=n, med=med):
                    if n.get("medicine_id") and med:
                        show_medicine_detail(page, med, load_notifications)
                    else:
                        show_snack(page, "ไม่พบข้อมูลยา", success=False)

                return ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=img_content,
                            bgcolor=img_bg,
                            border_radius=12,
                            width=62, height=62,
                            clip_behavior=ft.ClipBehavior.HARD_EDGE,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(
                                msg,
                                size=12, weight=ft.FontWeight.W_600,
                                color=TEXT_DARK if not is_resolved else TEXT_GRAY,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Container(height=3),
                            ft.Text(n["created_at"][:16], size=10, color=TEXT_GRAY),
                        ], expand=True, spacing=0),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_GRAY, size=18),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=CARD_BG,
                    border_radius=16,
                    padding=ft.padding.symmetric(vertical=10, horizontal=12),
                    shadow=ft.BoxShadow(blur_radius=6, color="#08000000", offset=ft.Offset(0, 2)),
                    margin=ft.margin.only(bottom=8),
                    on_click=on_tap if n.get("medicine_id") else None,
                    ink=True,
                    opacity=0.6 if is_resolved else 1.0,
                )

            unresolved_items = [make_noti_card(n) for n in noti_grouped.get("unresolved", [])]
            resolved_items   = [make_noti_card(n) for n in noti_grouped.get("resolved", [])]

            def do_sync(e=None):
                api_delete("/notifications/delete-all")
                api_post("/notifications/sync")
                load_notifications()

            from datetime import datetime
            today_str = datetime.now().strftime("%d %b %Y")

            # ── Header สีเขียว + 4 stat ──
            header_card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text("การแจ้งเตือน", size=20,
                                    weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text(f"อัปเดตล่าสุด {today_str}",
                                    size=11,
                                    color=ft.Colors.with_opacity(0.7, "white")),
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.REFRESH, color="white", size=14),
                                ft.Text("Sync", color="white", size=12,
                                        weight=ft.FontWeight.W_600),
                            ], spacing=5, tight=True),
                            bgcolor=ft.Colors.with_opacity(0.18, "white"),
                            border_radius=20,
                            padding=ft.padding.symmetric(vertical=7, horizontal=14),
                            border=ft.border.all(1, ft.Colors.with_opacity(0.25, "white")),
                            on_click=do_sync, ink=True,
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=14),
                    ft.Row([
                        stat_box("ใกล้หมดอายุ", data.get("expiring_soon", 0),
                                 ft.Icons.SCHEDULE),
                        stat_box("หมดอายุแล้ว", data.get("expired", 0),
                                 ft.Icons.CANCEL),
                        stat_box("สต็อกต่ำ",    data.get("low_stock", 0),
                                 ft.Icons.NOTIFICATIONS_ACTIVE),
                        stat_box("ทั้งหมด",      data.get("unresolved_notifications", 0),
                                 ft.Icons.NOTIFICATIONS),
                    ], spacing=8),
                ], spacing=0),
                bgcolor=PRIMARY,
                border_radius=20,
                padding=ft.padding.only(left=16, right=16, top=18, bottom=16),
                margin=ft.margin.only(bottom=14),
                shadow=ft.BoxShadow(
                    blur_radius=14,
                    color=ft.Colors.with_opacity(0.18, PRIMARY),
                    offset=ft.Offset(0, 4),
                ),
            )

            controls = [
                ft.Container(height=4),
                header_card,
                ft.Text("แจ้งเตือนที่ยังไม่ได้แก้ไข", size=13,
                        weight=ft.FontWeight.W_600, color=TEXT_DARK),
                ft.Container(height=8),
            ]

            if unresolved_items:
                controls.extend(unresolved_items)
            else:
                controls.append(ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Icon(ft.Icons.NOTIFICATIONS_OFF_OUTLINED,
                                            color=PRIMARY, size=40),
                            bgcolor=PRIMARY_SOFT,
                            border_radius=20,
                            width=72, height=72,
                            alignment=ft.alignment.Alignment(0, 0),
                        ),
                        ft.Container(height=8),
                        ft.Text("ไม่มีการแจ้งเตือนค้างอยู่",
                                color=TEXT_DARK, size=15,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "ระบบจะแจ้งเตือนอัตโนมัติเมื่อยาใกล้หมดอายุ\nหรือสต็อกต่ำกว่าที่กำหนด",
                            color=TEXT_GRAY, size=12,
                            text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    bgcolor=CARD_BG,
                    border_radius=20,
                    padding=ft.padding.symmetric(vertical=28, horizontal=20),
                    margin=ft.margin.only(bottom=12),
                    shadow=ft.BoxShadow(blur_radius=8, color="#0A000000",
                                        offset=ft.Offset(0, 2)),
                ))

            if resolved_items:
                controls.append(ft.Container(
                    content=ft.Text("แจ้งเตือนที่แก้ไขแล้ว", size=13,
                                    weight=ft.FontWeight.W_600, color=TEXT_GRAY),
                    padding=ft.padding.only(top=20, bottom=8),
                ))
                controls.extend(resolved_items)

            body.controls.extend(controls)
            page.update()

            
        # ======= NAV 3 แท็บ =======
        def on_nav(e):
            idx = e.control.selected_index
            if idx == 0: load_dashboard()
            elif idx == 1: load_notifications()
            elif idx == 2: profile_page(page)

        page.add(ft.Column([
            ft.Container(content=body, expand=True, padding=ft.padding.only(left=16, right=16, top=12, bottom=8), bgcolor=BG),
            ft.NavigationBar(
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="หน้าหลัก"),
                    ft.NavigationBarDestination(icon=ft.Icons.NOTIFICATIONS_OUTLINED, selected_icon=ft.Icons.NOTIFICATIONS, label="แจ้งเตือน"),
                    ft.NavigationBarDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="โปรไฟล์"),
                ],
                bgcolor=CARD_BG, on_change=on_nav,
            ),
        ], expand=True, spacing=0))
        load_dashboard()

    except Exception as ex:
        import traceback
        page.controls.clear()
        page.add(ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR, color=DANGER, size=48),
                ft.Text("เกิดข้อผิดพลาด", color=DANGER, size=18, weight=ft.FontWeight.BOLD),
                ft.Text(str(ex), color=TEXT_GRAY, size=12),
                ft.Text(traceback.format_exc(), color=TEXT_GRAY, size=9, selectable=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=40,
        ))
        page.update()

# ==================== MEDICINE DETAIL POPUP (สีขาว ตามรูป) ====================
def show_medicine_detail(page, medicine, on_done):
    m = medicine
    total = m.get("total_stock", 0)
    batches = m.get("batches", [])
    stock_color = DANGER if total < m["min_stock"] else SUCCESS
    img_path = m.get("image_path")
    description = m.get("description") or ""

    # รูปภาพยา + ปุ่มกล้องมุมขวาล่าง
    if img_path:
        img_widget = ft.Image(src=f"{API_URL}{img_path}", fit="contain", border_radius=16)
    else:
        img_widget = ft.Icon(ft.Icons.IMAGE_OUTLINED, color="#AAAAAA", size=64)

    img_section = ft.Container(
        content=ft.Stack([
            ft.Container(
                content=img_widget,
                bgcolor="#EEEEEE",
                border_radius=16,
                width=360, height=200,
            ),
            # ปุ่มกล้อง มุมขวาล่าง
            ft.Container(
                content=ft.Container(
                    content=ft.Icon(ft.Icons.CAMERA_ALT, color=TEXT_DARK, size=20),
                    bgcolor=CARD_BG, border_radius=20, width=40, height=40,
                    shadow=ft.BoxShadow(blur_radius=6, color="#20000000", offset=ft.Offset(0, 2)),
                ),
                right=8, bottom=8,
                on_click=lambda e: (close_dialog(page, dlg), show_image_upload_dialog(page, m["id"], on_done)),
            ),
        ]),
    )

    # ข้อมูล 3 กล่อง: คงเหลือ / หน่วย / Batch
    info_boxes = ft.Row([
        ft.Container(
            content=ft.Column([
                ft.Text("คงเหลือ", size=11, color=TEXT_GRAY),
                ft.Text(str(total), size=20, weight=ft.FontWeight.BOLD, color=stock_color),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            border=ft.border.all(1, BORDER), border_radius=12,
            padding=ft.padding.symmetric(vertical=10, horizontal=14), expand=1,
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("หน่วย", size=11, color=TEXT_GRAY),
                ft.Text(m.get("unit", "เม็ด"), size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            border=ft.border.all(1, BORDER), border_radius=12,
            padding=ft.padding.symmetric(vertical=10, horizontal=14), expand=1,
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Batch", size=11, color=TEXT_GRAY),
                ft.Text(str(len(batches)), size=20, weight=ft.FontWeight.BOLD, color=PRIMARY),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            border=ft.border.all(1, BORDER), border_radius=12,
            padding=ft.padding.symmetric(vertical=10, horizontal=14), expand=1,
        ),
    ], spacing=10)

    # Batch list — แบบในรูป (ขอบมน แต่ละแถว)
    batch_widgets = []
    for b in batches:
        days = b.get("days_until_expire", 0)
        def on_edit_b(e, batch=b):
            close_dialog(page, dlg)
            show_batch_dialog(page, medicine_id=m["id"], batch=batch, on_done=on_done)
        def on_del_b(e, bid=b["id"]):
            close_dialog(page, dlg)
            confirm_delete_batch(page, bid, on_done)
        batch_widgets.append(ft.Container(
            content=ft.Row([
                ft.Text(b["batch_number"], size=13, color=TEXT_DARK, weight=ft.FontWeight.W_500, expand=True),
                ft.Text(f"{b['quantity']} {m['unit']}", size=13, color=TEXT_SECONDARY),
                ft.Container(width=8),
                expiry_badge(days),
                ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=18, icon_color=TEXT_GRAY, on_click=on_edit_b, tooltip="แก้ไข"),
            ], spacing=4),
            border=ft.border.all(1, BORDER),
            border_radius=14,
            padding=ft.padding.symmetric(vertical=6, horizontal=14),
            margin=ft.margin.only(bottom=8),
        ))

    def on_add_batch(e):
        close_dialog(page, dlg)
        show_batch_dialog(page, medicine_id=m["id"], batch=None, on_done=on_done)
    def on_edit_med(e):
        close_dialog(page, dlg)
        # After editing, return to detail popup, not dashboard
        show_medicine_dialog(page, m, lambda: show_medicine_detail(page, m, on_done))
    def on_delete_med(e):
        close_dialog(page, dlg)
        confirm_delete_medicine(page, m, on_done)

    # ปุ่มด้านล่าง — 3 ปุ่มสีดำ/ขอบดำ แบบในรูป
    bottom_buttons = ft.Row([
        dark_button("แก้ไข", on_edit_med, icon=ft.Icons.EDIT),
        outline_dark_button("+ Batch", on_add_batch, icon=None),
        dark_button("ลบ", on_delete_med, icon=ft.Icons.DELETE),
    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER, wrap=False)

    # สร้าง dialog สีขาว
    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=CARD_BG,
        shape=ft.RoundedRectangleBorder(radius=24),
        content_padding=0,
        content=ft.Container(
            content=ft.Column([
                # Header bar
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_size=18, icon_color=TEXT_DARK, on_click=lambda e: close_dialog(page, dlg)),
                        ft.Text("รายละเอียดยา", size=18, weight=ft.FontWeight.BOLD, color=TEXT_DARK, expand=True),
                    ], spacing=0),
                    padding=ft.padding.only(left=4, right=16, top=8),
                ),
                # Content (static info)
                ft.Container(
                    content=ft.Column([
                        img_section,
                        ft.Container(height=12),
                        # ชื่อยา
                        ft.Text(m["name"], size=20, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                        ft.Text(m.get("generic_name") or "-", size=14, color=TEXT_GRAY),
                        ft.Container(height=8),
                        # รายละเอียด
                        ft.Text("รายละเอียด", size=14, weight=ft.FontWeight.W_600, color=TEXT_DARK) if description else ft.Container(),
                        ft.Text(description, size=12, color=TEXT_SECONDARY) if description else ft.Container(),
                        ft.Container(height=10),
                        # กล่องข้อมูล
                        info_boxes,
                        ft.Container(height=16),
                        # Batch header
                        ft.Text("Batch ทั้งหมด", size=15, weight=ft.FontWeight.W_600, color=TEXT_DARK),
                        ft.Container(height=6),
                        # Batch list (not scrollable here)
                        ft.Container(
                            content=ft.Column(
                                batch_widgets if batch_widgets else [
                                    ft.Text("ยังไม่มี Batch", size=13, color=TEXT_GRAY, italic=True),
                                ],
                                spacing=0,
                            ),
                            padding=ft.padding.only(left=0, right=0),
                        ),
                        ft.Container(height=12),
                        # ปุ่มด้านล่าง
                        bottom_buttons,
                        ft.Container(height=8),
                    ], spacing=2),
                    padding=ft.padding.only(left=20, right=20),
                ),
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            width=380, height=620,
        ),
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

# ==================== IMAGE UPLOAD (ใช้ URL แทน FilePicker) ====================
def show_image_upload_dialog(page, medicine_id, on_done):
    """ให้กรอก path ไฟล์รูปภาพ แล้วอัพโหลด — ไม่ใช้ FilePicker"""
    path_field = input_field("Path รูปภาพ", hint=r"เช่น C:\images\medicine.jpg หรือ URL", prefix_icon=ft.Icons.IMAGE)
    error_t = ft.Text("", color=DANGER, size=12)

    def upload(e):
        path = path_field.value.strip()
        if not path:
            error_t.value = "กรุณากรอก path รูปภาพ"; page.update(); return

        # ถ้าเป็นไฟล์ local
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    files = {"file": (os.path.basename(path), f, "image/jpeg")}
                    r = httpx.post(f"{API_URL}/medicines/{medicine_id}/image", headers=api_headers(), files=files, timeout=15)
                    if r.status_code == 200:
                        show_snack(page, "อัพโหลดรูปภาพสำเร็จ")
                        dlg.open = False; page.update(); on_done()
                    else:
                        error_t.value = f"อัพโหลดไม่สำเร็จ ({r.status_code})"; page.update()
            except Exception as ex:
                error_t.value = f"เกิดข้อผิดพลาด: {ex}"; page.update()
        else:
            # ถ้าเป็น URL — ดาวน์โหลดแล้วอัพโหลด
            try:
                r_img = httpx.get(path, timeout=15)
                r_img.raise_for_status()
                filename = path.split("/")[-1].split("?")[0] or "image.jpg"
                files = {"file": (filename, r_img.content, "image/jpeg")}
                r = httpx.post(f"{API_URL}/medicines/{medicine_id}/image", headers=api_headers(), files=files, timeout=15)
                if r.status_code == 200:
                    show_snack(page, "อัพโหลดรูปภาพสำเร็จ")
                    dlg.open = False; page.update(); on_done()
                else:
                    error_t.value = f"อัพโหลดไม่สำเร็จ ({r.status_code})"; page.update()
            except Exception as ex:
                error_t.value = f"ไม่พบไฟล์หรือ URL: {ex}"; page.update()

    dlg = ft.AlertDialog(
        bgcolor=CARD_BG,
        shape=ft.RoundedRectangleBorder(radius=20),
        title=ft.Text("เพิ่มรูปภาพยา", color=TEXT_DARK, weight=ft.FontWeight.BOLD, size=18),
        content=ft.Container(ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ADD_A_PHOTO, color=TEXT_GRAY, size=40),
                    ft.Text("กรอก path ไฟล์ หรือ URL รูปภาพ", size=12, color=TEXT_GRAY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                bgcolor="#F5F5F5", border=ft.border.all(2, BORDER), border_radius=16,
                width=300, height=120, padding=20,
            ),
            ft.Container(height=12),
            path_field,
            ft.Container(height=4),
            error_t,
        ], spacing=0), width=320),
        actions=[
            ft.TextButton("ยกเลิก", on_click=lambda e: close_dialog(page, dlg)),
            dark_button("อัพโหลด", upload, icon=ft.Icons.CLOUD_UPLOAD),
        ],
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

# ==================== MEDICINE DIALOG ====================
def show_medicine_dialog(page, medicine, on_done):
    is_edit = medicine is not None
    name_f = input_field("ชื่อยา *", value=medicine["name"] if is_edit else "", prefix_icon=ft.Icons.MEDICATION)
    generic_f = input_field("ชื่อสามัญ", value=medicine.get("generic_name") or "" if is_edit else "")
    unit_f = input_field("หน่วย", value=medicine.get("unit", "เม็ด") if is_edit else "เม็ด")
    unit_f.width = 145
    min_stock_f = input_field("สต็อกขั้นต่ำ", value=str(medicine.get("min_stock", 10)) if is_edit else "10")
    min_stock_f.width = 115
    desc_f = input_field("หมายเหตุ / รายละเอียด", value=medicine.get("description") or "" if is_edit else "", multiline=True)
    error_t = ft.Text("", color=DANGER, size=12)

    def save(e):
        if not name_f.value.strip():
            error_t.value = "กรุณากรอกชื่อยา"; page.update(); return
        try: min_val = int(min_stock_f.value or 10)
        except ValueError: error_t.value = "สต็อกขั้นต่ำต้องเป็นตัวเลข"; page.update(); return
        d = {"name": name_f.value.strip(), "generic_name": generic_f.value.strip() or None, "unit": unit_f.value.strip() or "เม็ด", "min_stock": min_val, "description": desc_f.value.strip() or None}
        result = api_put(f"/medicines/{medicine['id']}", json=d) if is_edit else api_post("/medicines", json=d)
        if result is None: show_snack(page, "เกิดข้อผิดพลาด", success=False); return
        show_snack(page, "บันทึกสำเร็จ"); dlg.open = False; page.update(); on_done()

    dlg = ft.AlertDialog(
        bgcolor=CARD_BG,
        shape=ft.RoundedRectangleBorder(radius=20),
        title=ft.Text("แก้ไขยา" if is_edit else "เพิ่มยาใหม่", color=TEXT_DARK, weight=ft.FontWeight.BOLD, size=18),
        content=ft.Container(ft.Column([
            name_f, ft.Container(height=8),
            generic_f, ft.Container(height=8),
            ft.Row([unit_f, min_stock_f], spacing=8),
            ft.Container(height=8),
            desc_f, error_t,
        ], tight=True, spacing=0), width=320),
        actions=[
            ft.TextButton("ยกเลิก", on_click=lambda e: (close_dialog(page, dlg), on_done())),
            dark_button("บันทึก", save, icon=ft.Icons.SAVE),
        ],
    )
    page.overlay.append(dlg); dlg.open = True; page.update()

# ==================== BATCH ADD / EDIT / DELETE ====================

# --- Batch Dialog (Add/Edit) ---
def show_batch_dialog(page, medicine_id, batch=None, on_done=None):
    is_edit = batch is not None
    batch_f = input_field("Batch Number *", value=batch["batch_number"] if is_edit else "", prefix_icon=ft.Icons.NUMBERS)
    qty_f = input_field("จำนวน *", value=str(batch["quantity"]) if is_edit else "", prefix_icon=ft.Icons.INVENTORY)
    expire_f = input_field("วันหมดอายุ *", value=str(batch["expire_date"]) if is_edit else "", hint="YYYY-MM-DD", prefix_icon=ft.Icons.CALENDAR_TODAY)
    note_f = input_field("หมายเหตุ", value=batch.get("note", "") if is_edit else "", multiline=True)
    error_t = ft.Text("", color=DANGER, size=12)
    import re
    from datetime import datetime
    def save(e):
        # DEBUG print removed
        if not batch_f.value.strip() or not qty_f.value.strip() or not expire_f.value.strip():
            error_t.value = "กรุณากรอกข้อมูลให้ครบ"; page.update(); return
        date_val = expire_f.value.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_val):
            error_t.value = "วันหมดอายุต้องเป็นรูปแบบ YYYY-MM-DD"; page.update(); return
        try:
            datetime.strptime(date_val, "%Y-%m-%d")
        except ValueError:
            error_t.value = "วันหมดอายุไม่ถูกต้องตามปฏิทิน"; page.update(); return
        try:
            qty = int(qty_f.value.strip())
        except ValueError:
            error_t.value = "จำนวนต้องเป็นตัวเลข"; page.update(); return
        d = {"batch_number": batch_f.value.strip(), "quantity": qty, "expire_date": date_val, "note": (note_f.value or "").strip() or None}
        # DEBUG print removed
        if is_edit:
            result = api_put(f"/batches/{batch['id']}", json=d)
            # DEBUG print removed
            if result is None:
                show_snack(page, "เกิดข้อผิดพลาด", success=False); return
            show_snack(page, "แก้ไข Batch สำเร็จ")
        else:
            result = api_post(f"/medicines/{medicine_id}/batches", json=d)
            # DEBUG print removed
            if result is None:
                show_snack(page, "เกิดข้อผิดพลาด", success=False); return
            show_snack(page, "เพิ่ม Batch สำเร็จ")
        dlg.open = False; page.update()
        if on_done: on_done()
    def do_delete(e):
        dlg.open = False; page.update()
        confirm_delete_batch(page, batch["id"], on_done)
    actions = [ft.TextButton("ยกเลิก", on_click=lambda e: close_dialog(page, dlg))]
    if is_edit:
        actions.append(dark_button("ลบ Batch", do_delete, icon=ft.Icons.DELETE))
    actions.append(dark_button("บันทึก", save, icon=ft.Icons.SAVE))
    dlg = ft.AlertDialog(
        bgcolor=CARD_BG, shape=ft.RoundedRectangleBorder(radius=20),
        title=ft.Text("แก้ไข Batch" if is_edit else "เพิ่ม Batch", color=TEXT_DARK, weight=ft.FontWeight.BOLD, size=18),
        content=ft.Container(ft.Column([
            batch_f, ft.Container(height=8),
            qty_f, ft.Container(height=8),
            expire_f, ft.Container(height=8),
            note_f, error_t
        ], tight=True, spacing=0), width=310),
        actions=actions,
    )
    page.overlay.append(dlg); dlg.open = True; page.update()

def confirm_delete_medicine(page, medicine, on_done):
    def do_del(e):
        result = api_delete(f"/medicines/{medicine['id']}")
        if result is None: show_snack(page, "เกิดข้อผิดพลาด", success=False)
        else: show_snack(page, "ลบยาสำเร็จ")
        dlg.open = False; page.update(); on_done()
    dlg = ft.AlertDialog(
        bgcolor=CARD_BG, shape=ft.RoundedRectangleBorder(radius=20),
        title=ft.Row([ft.Icon(ft.Icons.WARNING, color=DANGER, size=24), ft.Text("ยืนยันการลบ", color=DANGER, weight=ft.FontWeight.BOLD)], spacing=8),
        content=ft.Text(f"ต้องการลบยา '{medicine['name']}' ?\nBatch ทั้งหมดจะถูกลบด้วย", size=14),
        actions=[ft.TextButton("ยกเลิก", on_click=lambda e: close_dialog(page, dlg)), dark_button("ลบ", do_del, icon=ft.Icons.DELETE)],
    )
    page.overlay.append(dlg); dlg.open = True; page.update()

def confirm_delete_batch(page, batch_id, on_done):
    def do_del(e):
        result = api_delete(f"/batches/{batch_id}")
        if result is None: show_snack(page, "เกิดข้อผิดพลาด", success=False)
        else: show_snack(page, "ลบ Batch สำเร็จ")
        dlg.open = False; page.update(); on_done()
    dlg = ft.AlertDialog(
        bgcolor=CARD_BG, shape=ft.RoundedRectangleBorder(radius=20),
        title=ft.Row([ft.Icon(ft.Icons.WARNING, color=DANGER, size=24), ft.Text("ยืนยันการลบ Batch", color=DANGER, weight=ft.FontWeight.BOLD)], spacing=8),
        content=ft.Text("ต้องการลบ Batch นี้ใช่หรือไม่?", size=14),
        actions=[ft.TextButton("ยกเลิก", on_click=lambda e: close_dialog(page, dlg)), dark_button("ลบ", do_del, icon=ft.Icons.DELETE)],
    )
    page.overlay.append(dlg); dlg.open = True; page.update()

# ==================== MAIN ====================
def main(page: ft.Page):
    page.title = "ระบบจัดการคลังยา"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.padding = 0
    page.window.width = 420
    page.window.height = 900
    login_page(page)

ft.app(target=main)