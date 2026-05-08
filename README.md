# ⚡ CPU Thermal & Power Manager

Ofis laptopları için sessiz / dengeli / performans mod yöneticisi.

Bu uygulama, Windows'un kendi güç yönetim aracı olan `powercfg` komut satırı aracını temel alır. 
- **Mantık:** İşlemcinin "Minimum" ve "Maksimum" çalışma yüzdelerini dinamik olarak değiştirerek, Windows'un işlemciye voltaj/frekans verme profilini manipüle eder.
- **Sonuç:** Sessiz modda işlemci frekansını sabitleyerek fanların devreye girmesine neden olan "Turbo Boost" sıçramalarını engeller.

---

## 🚀 Kurulum

### 1. Gereksinimleri yükle
```bash
pip install -r requirements.txt
```

### 2. Uygulamayı çalıştır (Yönetici olarak!)
```bash
# Sağ tık → "Yönetici olarak çalıştır" seçeneğiyle PowerShell/CMD aç
python fan_control.py
```

> ⚠️ **Önemli:** `powercfg` komutu yönetici yetkisi gerektirir.
> Yönetici olmadan çalıştırırsan mod değişimi çalışmaz.

---

## 🎛️ Modlar

| Mod        | CPU Maks | Kullanım Amacı              |
|------------|----------|-----------------------------|
| 🔇 Sessiz  | %50      | Word, tarayıcı, not alma    |
| ⚖️ Dengeli | %80      | Genel kullanım              |
| 🚀 Performans | %100  | Derleme, video render, vb.  |

---

<<<<<<< Updated upstream
=======
## 🔧 Sorun Giderme

- **Mod değişmiyor:** Yönetici olarak çalıştır
- **Tray ikonu görünmüyor:** Görev çubuğu → Sistem tepsisi ikonlarını göster
- **Başlangıçta açılmıyor:** Uygulamayı bir kez yönetici olarak çalıştır ve toggle'ı aç

---

>>>>>>> Stashed changes
## 📋 Gereksinimler

- Windows 10 / 11
- Python 3.9+
- Yönetici yetkisi
