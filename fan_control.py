import ctypes
import sys

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

run_as_admin()

import customtkinter as ctk
import subprocess
import winreg
import sys
import os
import threading
from PIL import Image, ImageDraw
import pystray

# ── Güç Planı GUIDleri (Windows varsayılanları) ──────────────────────────────
POWER_PLANS = {
    "quiet":      "a1841308-3541-4fab-bc81-f71556f20b4a",  # Güç tasarrufu
    "balanced":   "381b4222-f694-41f0-9685-ff5bb260df2e",  # Dengeli
    "performance":"8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",  # Yüksek performans
}

# İşlemci maks. kullanım oranları (%)
CPU_MAX = {"quiet": 50, "balanced": 80, "performance": 100}

APP_NAME = "FanControl"
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# ── Güç Yönetimi ─────────────────────────────────────────────────────────────

def set_power_mode(mode: str):
    """Güç planını ve işlemci limitini ayarla."""

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE

    guid = POWER_PLANS.get(mode)
    if guid:
        subprocess.run(["powercfg", "/setactive", guid], capture_output=True, startupinfo=si)

    cpu_max = CPU_MAX.get(mode, 100)
    # AC (prize takılı)
    subprocess.run([
        "powercfg", "/setacvalueindex", "SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "bc5038f7-23e0-4960-96da-33abaf5935ec",
        str(cpu_max)
    ], capture_output=True, startupinfo=si)
    # DC (pil)
    subprocess.run([
        "powercfg", "/setdcvalueindex", "SCHEME_CURRENT",
        "54533251-82be-4824-96c1-47b60b740d00",
        "bc5038f7-23e0-4960-96da-33abaf5935ec",
        str(cpu_max)
    ], capture_output=True, startupinfo=si)
    subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], capture_output=True, startupinfo=si)

# ── Başlangıç Ayarı ───────────────────────────────────────────────────────────

def set_startup(enable: bool):
    exe_path = sys.executable if getattr(sys, "frozen", False) else f'"{sys.executable}" "{os.path.abspath(__file__)}"'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def is_startup_enabled() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

# ── Tray İkonu ────────────────────────────────────────────────────────────────

def create_tray_icon(app_ref):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 60, 60], fill="#4ECDC4")
    d.polygon([(32,14),(44,50),(32,42),(20,50)], fill="white")

    def show_window(icon, item):
        app_ref.after(0, app_ref.deiconify)

    def quit_app(icon, item):
        icon.stop()
        app_ref.after(0, app_ref.destroy)

    menu = pystray.Menu(
        pystray.MenuItem("Aç", show_window, default=True),
        pystray.MenuItem("Sessiz Mod",    lambda i, it: app_ref.after(0, lambda: app_ref.apply_mode("quiet"))),
        pystray.MenuItem("Dengeli Mod",   lambda i, it: app_ref.after(0, lambda: app_ref.apply_mode("balanced"))),
        pystray.MenuItem("Performans",    lambda i, it: app_ref.after(0, lambda: app_ref.apply_mode("performance"))),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Çıkış", quit_app),
    )
    icon = pystray.Icon(APP_NAME, img, "Fan Kontrolü", menu)
    return icon

# ── Ana Pencere ───────────────────────────────────────────────────────────────

class FanControlApp(ctk.CTk):
    MODES = {
        "quiet":       {"label": "Sessiz",      "icon": "🔇", "desc": "Yavaş fan, düşük ısı\nGünlük ofis kullanımı için ideal", "color": "#4ECDC4", "cpu": "≤%50"},
        "balanced":    {"label": "Dengeli",     "icon": "⚖️",  "desc": "Performans ve sessizlik arasında denge", "color": "#45B7D1", "cpu": "≤%80"},
        "performance": {"label": "Performans",  "icon": "🚀", "desc": "Tam güç, maksimum hız\nAğır işler için: Render, Oyun vb.", "color": "#FF6B6B", "cpu": "%100"},
    }

    def __init__(self):
        super().__init__()
        self.current_mode = "balanced"
        self.mode_buttons = {}

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Fan Kontrolü")
        x = 420
        y = 650
        ekran_genislik = self.winfo_screenwidth()
        ekran_yukseklik = self.winfo_screenheight()
        self.geometry(f"{x}x{y}+{ekran_genislik-x-10}+{ekran_yukseklik-y-90}")
        self.resizable(False, False)
        self.configure(fg_color="#0F0F1A")

        # Pencere kapatılınca tray'e gizle
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        self._build_ui()

        # Tray thread
        self.tray_icon = create_tray_icon(self)
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

        # Başlangıç modu uygula
        self.apply_mode("balanced")

    # ── UI Yapısı ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Başlık
        header = ctk.CTkFrame(self, fg_color="#161628", corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="⚡  Fan Kontrolü",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#E0E0FF"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Mod Kartları
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=20)

        for mode_key, info in self.MODES.items():
            self._build_mode_card(cards_frame, mode_key, info)

        # Durum çubuğu
        self.status_frame = ctk.CTkFrame(self, fg_color="#161628", corner_radius=0, height=50)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Dengeli mod aktif",
            font=ctk.CTkFont(size=12),
            text_color="#45B7D1"
        )
        self.status_label.place(relx=0.5, rely=0.5, anchor="center")

        # Başlangıç toggle
        startup_frame = ctk.CTkFrame(self, fg_color="#1A1A2E", corner_radius=12)
        startup_frame.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            startup_frame, text="Windows başlangıcında çalış",
            font=ctk.CTkFont(size=13),
            text_color="#AAAACC"
        ).pack(side="left", padx=15, pady=10)

        self.startup_var = ctk.BooleanVar(value=is_startup_enabled())
        self.startup_switch = ctk.CTkSwitch(
            startup_frame, text="",
            variable=self.startup_var,
            command=self._toggle_startup,
            button_color="#4ECDC4",
            progress_color="#2A6B68"
        )
        self.startup_switch.pack(side="right", padx=15)

    def _build_mode_card(self, parent, mode_key, info):
        card = ctk.CTkFrame(
            parent,
            height=120,
            fg_color="#1A1A2E",
            corner_radius=16,
            border_width=2,
            border_color="#2A2A4A",
            cursor="hand2"
        )
        card.pack_propagate(False)
        card.pack(fill="x", pady=6)

        # Sol renk şeridi
        accent = ctk.CTkFrame(card, fg_color=info["color"], corner_radius=8, width=6)
        accent.pack(side="left", fill="y", padx=(8, 0), pady=8)
        accent.pack_propagate(False)

        # İkon
        ctk.CTkLabel(
            card, text=info["icon"],
            font=ctk.CTkFont(size=30)
        ).pack(side="left", padx=(10, 0), pady=15)

        # Metin grubu
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            text_frame, text=info["label"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#E0E0FF",
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            text_frame, text=info["desc"],
            font=ctk.CTkFont(size=11),
            text_color="#7070A0",
            anchor="w",
            justify="left"
        ).pack(fill="x")

        # CPU etiketi
        ctk.CTkLabel(
            card, text=f"CPU\n{info['cpu']}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=info["color"],
            justify="center"
        ).pack(side="right", padx=14)

        # Tıklama
        for widget in [card, accent, text_frame]:
            widget.bind("<Button-1>", lambda e, m=mode_key: self.apply_mode(m))
        for child in text_frame.winfo_children():
            child.bind("<Button-1>", lambda e, m=mode_key: self.apply_mode(m))

        self.mode_buttons[mode_key] = card

    # ── Mod Uygula ────────────────────────────────────────────────────────────

    def apply_mode(self, mode: str):
        self.current_mode = mode
        info = self.MODES[mode]

        # Kart görünümlerini güncelle
        for key, card in self.mode_buttons.items():
            if key == mode:
                card.configure(
                    border_color=self.MODES[key]["color"],
                    fg_color="#242440"
                )
            else:
                card.configure(border_color="#2A2A4A", fg_color="#1A1A2E")

        # Durum çubuğu
        self.status_label.configure(
            text=f"● {info['label']} mod aktif",
            text_color=info["color"]
        )

        # Arka planda güç ayarını uygula
        threading.Thread(target=set_power_mode, args=(mode,), daemon=True).start()

    # ── Yardımcılar ───────────────────────────────────────────────────────────

    def _hide_to_tray(self):
        self.withdraw()

    def _toggle_startup(self):
        set_startup(self.startup_var.get())


# ── Başlat ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = FanControlApp()
    app.mainloop()
