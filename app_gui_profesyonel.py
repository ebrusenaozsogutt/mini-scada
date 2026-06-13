# app_gui_profesyonel.py â€„ Hilal Yeşim Staj Projesi Uygulaması (SON VERSİYON)

import os
import sys
import glob
import time
import sqlite3
import threading
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import math
import matplotlib
matplotlib.use("TkAgg")


# CustomTkinter importu
import customtkinter as ctk
from tkinter import messagebox
import tkinter.ttk as ttk # Standart ttk importu (Treeview stilizasyonu için)

# Ses çalma için winsound (Windows)
try:
    import winsound
    WINSOUND_OK = True
except ImportError:
    WINSOUND_OK = False
    print("winsound bulunamadı. Sesli alarm pasif.")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
sns.set_style('darkgrid')

SENSOR_LIMITS = {
    "temperature_min": 15,
    "temperature_max": 35,
}

#--- YOL ve KAYNAKLAR ---
def find_project_root() -> Path:
    """SensorSimulator.csproj dosyasını bulur ve bulunduğu klasörü döndürür."""
    search_roots = [
        Path(__file__).resolve().parent,
        Path.cwd().resolve(),
    ]

    for root in search_roots:
        p = root
        while True:
            csproj_path = p / "SensorSimulator.csproj"
            if csproj_path.exists():
                return p

            if p == p.parent:
                break
            p = p.parent

    for root in search_roots:
        try:
            matches = list(root.rglob("SensorSimulator.csproj"))
        except Exception:
            continue

        if matches:
            return matches[0].parent

    raise RuntimeError("SensorSimulator.csproj bulunamadı.")

#PROJECT_ROOT = Path("C:/Users/Hilal Yeşim/Desktop/Staj Proje - Kopya") #find_project_root()

PROJECT_ROOT = find_project_root()
CSHARP_SIM_DIR = PROJECT_ROOT

# C# klasör yolunu sizin yapınıza göre kesin olarak ayarlıyoruz
# Sizin yapınız: .../Staj Proje - Kopya/src/csharp/SensorSimulator
#CSHARP_SIM_DIR = PROJECT_ROOT / "src" / "csharp" / "SensorSimulator"
# Eğer kod bu klasörü bulmakta sorun yaşarsa, /src klasörünü çıkarıp deneyebilirsiniz:
# CSHARP_SIM_DIR = PROJECT_ROOT / "csharp" / "SensorSimulator" 

DB_PATH = CSHARP_SIM_DIR / "sensor_data.db"
APP_DIR = Path(__file__).resolve().parent
CSV_COLUMNS = ["Tarih", "Sicaklik", "Basinc", "Akim"]
DATA_COLUMNS = ["Id", "Tarih", "Sicaklik", "Basinc", "Akim", "Anomali"]

RES_DIR = PROJECT_ROOT / "resources" 
RES_DIR.mkdir(parents=True, exist_ok=True)

OUT_DIR = PROJECT_ROOT / "python" / "analytics" / "outputs" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# --- Simülatör Başlat/Durdur (C#) ---
def _find_simulator_exe() -> Path | None:
    """Derlenmiş SensorSimulator.exe dosyasını en güncel .NET sürümü altında bulur."""
    
    # !!! HATA BURADAYDI: publish_base'in tanımlanması gerekiyordu !!!
    publish_base = CSHARP_SIM_DIR / "bin" / "Release" 
    
    # 1. Adım: Eğer publish klasörü yoksa, doğrudan çık
    if not publish_base.exists():
        return None
        
    # 2. Adım: Çoğu modern .NET sürümünü kontrol ediyoruz
    for version in ["net8.0", "net7.0", "net6.0"]:
        # publish_base değişkenini kullanıyoruz
        exe_path = publish_base / version / "win-x64" / "publish" / "SensorSimulator.exe"
        if exe_path.exists():
            print(f"C# Simülatörü EXE yolu bulundu: {exe_path}")
            return exe_path
    
    # 3. Adım: Hiçbiri bulunamazsa
    return None

# KODUN KALANI BURADAN İTİBAREN DEVAM EDER

def start_simulator_process():
    sim_dir = find_project_root()
    csproj_path = sim_dir / "SensorSimulator.csproj"

    logs_dir = sim_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logfile = logs_dir / "simulator.log"

    try:
        log = open(logfile, "a", encoding="utf-8")
    except Exception as e:
        print(f"Log dosyasi acilamadi: {e}")
        log = subprocess.DEVNULL

    def write_log(message: str):
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        print(line)
        try:
            log.write(line + "\n")
            log.flush()
        except Exception:
            pass

    write_log("=== Simulator baslatma denemesi ===")
    write_log(f"sim_dir: {sim_dir}")
    write_log(f"csproj_path: {csproj_path}")
    write_log(f"csproj_exists: {csproj_path.exists()}")

    if not csproj_path.exists():
        write_log("HATA: SensorSimulator.csproj bulunamadi.")
        raise RuntimeError(
            "SensorSimulator.csproj bulunamadi. "
            f"Aranan klasor: {sim_dir}"
        )

    exe = _find_simulator_exe()
    write_log(f"exe_path: {exe if exe else 'bulunamadi'}")

    if exe and exe.exists():
        command = [str(exe)]
        cwd = str(sim_dir)
        write_log(f"subprocess_command: {command}")
        write_log(f"cwd: {cwd}")

        return subprocess.Popen(
            command,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT
        )

    command = ["dotnet", "run", "--project", str(csproj_path)]
    cwd = str(sim_dir)
    write_log(f"subprocess_command: {command}")
    write_log(f"cwd: {cwd}")

    try:
        return subprocess.Popen(
            command,
            cwd=cwd,
            stdout=log,
            stderr=subprocess.STDOUT
        )
    except FileNotFoundError:
        write_log("HATA: dotnet komutu bulunamadi.")
        raise RuntimeError(
            "dotnet komutu bulunamadi. .NET SDK kurulu mu ve PATH'e ekli mi kontrol edin."
        )
    except Exception as e:
        write_log(f"HATA: subprocess baslatilamadi: {e}")
        raise RuntimeError(f"C# simulator baslatilamadi: {e}")

def stop_process(p: subprocess.Popen | None):
    if not p: return
    try:
        p.terminate()
        p.wait(timeout=3)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass

# --- Yardımcılar: Veritabanı Okuma ve PDF Oluşturma ---
def read_latest_df_sqlite_legacy(limit: int = 200, hours_back: int = None) -> pd.DataFrame:
    """DBâ€™den ya son 'limit' kaydı ya da son 'hours_back' saatteki kayıtları alır."""
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["Id", "Tarih", "Sicaklik"])

    query = "SELECT Id, Tarih, Sicaklik FROM SensorData "
    params = []
    
    if hours_back is not None:
        cutoff = datetime.now() - timedelta(hours=hours_back)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        query += "WHERE Tarih >= ? "
        params.append(cutoff_str)

    query += "ORDER BY Id DESC "
    if hours_back is None:
        query += f"LIMIT {int(limit)}"

    conn = None
    try:
        #conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False, isolation_level=None)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)

        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 3000;")
        df = pd.read_sql_query(query, conn, params=params)
    except sqlite3.OperationalError as e:
        print(f"Veritabanı bağlantı/okuma hatası: {e}")
        return pd.DataFrame(columns=["Id", "Tarih", "Sicaklik"])
    finally:
        if conn:
             conn.close()
    
    if not df.empty:
        df = df.sort_values("Id").reset_index(drop=True)
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
        df["Anomali"] = (df["Sicaklik"] < SENSOR_LIMITS["temperature_min"]) | (df["Sicaklik"] > SENSOR_LIMITS["temperature_max"])
        df = df.dropna(subset=["Tarih", "Sicaklik"])
    return df

def find_sensor_csv() -> Path | None:
    """Uygulama klasorune gore olasi sensor CSV yollarini sirayla dener."""
    candidates = [
        APP_DIR / "sensor_data.csv",
        APP_DIR / "bin" / "Debug" / "net8.0" / "sensor_data.csv",
        APP_DIR / "bin" / "Release" / "net8.0" / "sensor_data.csv",
        APP_DIR / "src" / "csharp" / "SensorSimulator" / "sensor_data.csv",
        APP_DIR / "csharp" / "SensorSimulator" / "sensor_data.csv",
        CSHARP_SIM_DIR / "sensor_data.csv",
    ]

    for path in candidates:
        if path.exists():
            return path
    return None

def read_latest_df(limit: int = 200, hours_back: int = None) -> pd.DataFrame:
    """CSV'den ya son 'limit' kaydi ya da son 'hours_back' saatteki kayitlari alir."""
    csv_path = find_sensor_csv()
    if csv_path is None:
        return pd.DataFrame(columns=DATA_COLUMNS)

    try:
        df = pd.read_csv(csv_path)

        if df.empty:
            return pd.DataFrame(columns=DATA_COLUMNS)

        if not set(CSV_COLUMNS).issubset(df.columns):
            df = df.iloc[:, :len(CSV_COLUMNS)].copy()
            df.columns = CSV_COLUMNS[:len(df.columns)]

        missing_cols = [c for c in CSV_COLUMNS if c not in df.columns]
        if missing_cols:
            print(f"CSV kolonlari eksik: {missing_cols}")
            return pd.DataFrame(columns=DATA_COLUMNS)

        df = df[CSV_COLUMNS].copy()
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")

        for col in ["Sicaklik", "Basinc", "Akim"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

        df = df.dropna(subset=CSV_COLUMNS).reset_index(drop=True)
        if df.empty:
            return pd.DataFrame(columns=DATA_COLUMNS)

        df["Id"] = df.index + 1

        if hours_back is not None:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            df = df[df["Tarih"] >= cutoff]
        else:
            df = df.tail(int(limit))

        df = df.sort_values("Id").reset_index(drop=True)
        df["Anomali"] = (df["Sicaklik"] < SENSOR_LIMITS["temperature_min"]) | (df["Sicaklik"] > SENSOR_LIMITS["temperature_max"])
        df = df[DATA_COLUMNS]
    except Exception as e:
        print(f"CSV okuma hatasi: {e}")
        return pd.DataFrame(columns=DATA_COLUMNS)

    return df

def compute_summary(df: pd.DataFrame) -> dict:
    """Özet metrikleri hesapla."""
    if df.empty:
        return {
            "kayıt_sayısı": 0,
            "min": None,
            "max": None,
            "ortalama": None,
            "anomali_sayısı": 0,
            "anomali_oranı": "0%",
            "risk_seviyesi": "Normal",
            "bakim_mesaji": "Sistem normal çalışıyor.",
            "basinc_ortalama": None,
            "basinc_min": None,
            "basinc_max": None,
            "basinc_risk_seviyesi": "-",
            "basinc_mesaji": "Veri yok",
            "akim_ortalama": None,
            "akim_min": None,
            "akim_max": None,
            "akim_risk_seviyesi": "-",
            "akim_mesaji": "Veri yok",
            "ortalama_basinc": None,
            "ortalama_akim": None,
        }
    
    summary = {}
    summary["kayıt_sayısı"] = len(df)
    summary["min"] = float(df["Sicaklik"].min()) if "Sicaklik" in df.columns and not df["Sicaklik"].empty else None
    summary["max"] = float(df["Sicaklik"].max()) if "Sicaklik" in df.columns and not df["Sicaklik"].empty else None
    summary["ortalama"] = float(df["Sicaklik"].mean()) if "Sicaklik" in df.columns and not df["Sicaklik"].empty else None

    if "Anomali" in df.columns:
        anom_count = int(df["Anomali"].sum())
    else:
        anom_count = 0

    summary["anomali_sayısı"] = anom_count
    ratio = 100.0 * anom_count / len(df) if len(df) > 0 else 0.0
    summary["anomali_oranı"] = f"{ratio:.1f}%"

    if ratio < 2:
        summary["risk_seviyesi"] = "Normal"
        summary["bakim_mesaji"] = "Sistem normal çalışıyor."
    elif ratio < 5:
        summary["risk_seviyesi"] = "Orta"
        summary["bakim_mesaji"] = "Sıcaklık anomalileri artıyor. Takip önerilir."
    else:
        summary["risk_seviyesi"] = "Yüksek"
        summary["bakim_mesaji"] = "Bakım kontrolü önerilir."

    if "Basinc" in df.columns and not df["Basinc"].dropna().empty:
        summary["basinc_ortalama"] = float(df["Basinc"].mean())
        summary["basinc_min"] = float(df["Basinc"].min())
        summary["basinc_max"] = float(df["Basinc"].max())
    else:
        summary["basinc_ortalama"] = None
        summary["basinc_min"] = None
        summary["basinc_max"] = None

    if summary["basinc_ortalama"] is None:
        summary["basinc_risk_seviyesi"] = "-"
        summary["basinc_mesaji"] = "Veri yok"
    elif 4 <= summary["basinc_ortalama"] <= 8:
        summary["basinc_risk_seviyesi"] = "Normal"
        summary["basinc_mesaji"] = "Basınç değerleri normal aralıkta."
    elif 3 <= summary["basinc_ortalama"] < 4 or 8 < summary["basinc_ortalama"] <= 9:
        summary["basinc_risk_seviyesi"] = "Orta"
        summary["basinc_mesaji"] = "Basınç değerlerinde sapma var. Takip önerilir."
    else:
        summary["basinc_risk_seviyesi"] = "Yüksek"
        summary["basinc_mesaji"] = "Basınç kritik aralıkta. Kontrol önerilir."

    if "Akim" in df.columns and not df["Akim"].dropna().empty:
        summary["akim_ortalama"] = float(df["Akim"].mean())
        summary["akim_min"] = float(df["Akim"].min())
        summary["akim_max"] = float(df["Akim"].max())
    else:
        summary["akim_ortalama"] = None
        summary["akim_min"] = None
        summary["akim_max"] = None

    if summary["akim_ortalama"] is None:
        summary["akim_risk_seviyesi"] = "-"
        summary["akim_mesaji"] = "Veri yok"
    elif 15 <= summary["akim_ortalama"] <= 40:
        summary["akim_risk_seviyesi"] = "Normal"
        summary["akim_mesaji"] = "Akım değerleri normal aralıkta."
    elif 10 <= summary["akim_ortalama"] < 15 or 40 < summary["akim_ortalama"] <= 45:
        summary["akim_risk_seviyesi"] = "Orta"
        summary["akim_mesaji"] = "Akım değerlerinde sapma var. Takip önerilir."
    else:
        summary["akim_risk_seviyesi"] = "Yüksek"
        summary["akim_mesaji"] = "Akım kritik aralıkta. Kontrol önerilir."

    summary["ortalama_basinc"] = summary["basinc_ortalama"]
    summary["ortalama_akim"] = summary["akim_ortalama"]

    return summary

def create_pdf_report_task(df: pd.DataFrame, summary: dict, out: Path):
    """PDF oluşturma işlemini bir fonksiyonda toplar."""
    with PdfPages(out) as pdf:
        
        # Grafik renklerini tema bağımsız siyah/beyaz yapalım (PDF için)
        plt.rcParams.update({
            "figure.facecolor": "white", 
            "axes.facecolor": "white",
            "text.color": "black",
            "axes.labelcolor": "black",
            "xtick.color": "black",
            "ytick.color": "black"
        })
        
        # --- Sayfa 1: Zaman Serisi Grafiği + Anomaliler ---
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(df["Tarih"], df["Sicaklik"], label="Sıcaklık", linewidth=1.2, color='#007acc')
        anomalies = df[df["Anomali"] == True]
        if not anomalies.empty:
            ax1.scatter(anomalies["Tarih"], anomalies["Sicaklik"], label="Anomali", color="red", s=30, zorder=5)

        ax1.set_title(f"Sıcaklık Zaman Serisi (Toplam Kayıt: {len(df)})", fontsize=14)
        ax1.set_xlabel("Zaman", fontsize=10)
        ax1.set_ylabel("Sıcaklık (°C)", fontsize=10)
        ax1.legend(loc="upper left")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        fig1.autofmt_xdate()
        pdf.savefig(fig1, bbox_inches="tight")
        plt.close(fig1)

        # --- Sayfa 2: Histogram (Dağılım) ---
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.hist(df["Sicaklik"], bins=25, alpha=0.8, color='#007acc', edgecolor='black')
        ax2.axvline(summary['ortalama'], color='red', linestyle='dashed', linewidth=1, label=f"Ort: {summary['ortalama']:.2f}°C")
        ax2.set_title("Sıcaklık Değerleri Dağılımı (Histogram)", fontsize=14)
        ax2.set_xlabel("Sıcaklık (°C)", fontsize=10)
        ax2.set_ylabel("Frekans", fontsize=10)
        ax2.legend()
        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

        has_basinc = "Basinc" in df.columns and not df["Basinc"].dropna().empty
        has_akim = "Akim" in df.columns and not df["Akim"].dropna().empty

        if has_basinc or has_akim:
            fig_sensor, ax_sensor = plt.subplots(figsize=(10, 6))

            if has_basinc:
                ax_sensor.plot(df["Tarih"], df["Basinc"], label="Basınç", linewidth=1.2, color="blue")

            if has_akim:
                ax_sensor.plot(df["Tarih"], df["Akim"], label="Akım", linewidth=1.2, color="green")

            ax_sensor.set_title("Basınç ve Akım Zaman Serisi", fontsize=14)
            ax_sensor.set_xlabel("Zaman", fontsize=10)
            ax_sensor.set_ylabel("Değer", fontsize=10)
            ax_sensor.legend(loc="upper left")
            ax_sensor.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
            fig_sensor.autofmt_xdate()
            pdf.savefig(fig_sensor, bbox_inches="tight")
            plt.close(fig_sensor)

        # --- Sayfa 3: Özet Metrikler Tablosu ---
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        ax3.axis('off')

        title = f"Analiz Raporu Özeti – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ax3.text(0.5, 0.95, title, ha="center", va="top", fontsize=16, fontweight="bold")
        
        rows = [
            ["Metrik", "Değer"],
            ["Kayıt Sayısı", summary["kayıt_sayısı"]],
            ["Min. Sıcaklık (°C)", f"{summary['min']:.2f}" if summary["min"] is not None else "N/A"],
            ["Maks. Sıcaklık (°C)", f"{summary['max']:.2f}" if summary["max"] is not None else "N/A"],
            ["Ortalama Sıcaklık (°C)", f"{summary['ortalama']:.2f}" if summary["ortalama"] is not None else "N/A"],
            ["Anomali Sayısı (15°C altı / 35°C üstü)", summary["anomali_sayısı"]],
            ["Anomali Oranı", summary["anomali_oranı"]],
            ["Min. Basınç", f"{summary['basinc_min']:.2f}" if summary["basinc_min"] is not None else "N/A"],
            ["Maks. Basınç", f"{summary['basinc_max']:.2f}" if summary["basinc_max"] is not None else "N/A"],
            ["Ortalama Basınç", f"{summary['basinc_ortalama']:.2f}" if summary["basinc_ortalama"] is not None else "N/A"],
            ["Min. Akım", f"{summary['akim_min']:.2f}" if summary["akim_min"] is not None else "N/A"],
            ["Maks. Akım", f"{summary['akim_max']:.2f}" if summary["akim_max"] is not None else "N/A"],
            ["Ortalama Akım", f"{summary['akim_ortalama']:.2f}" if summary["akim_ortalama"] is not None else "N/A"],
        ]
        
        table = ax3.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="center", 
                          colColours=["#f2f2f2", "#f2f2f2"])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.6)
        pdf.savefig(fig3, bbox_inches="tight")
        plt.close(fig3)

    try:
        os.startfile(str(out))
    except Exception as e:
        print(f"PDF açma hatası: {e}")
    return out

# --- UI â€„ CustomTkinter Uygulaması ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sıcaklık Veri Analiz Sistemi")
        self.geometry("1000x700")
        self.minsize(800, 600)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Login ekranı için placeholder (bu versiyonda login atlanmıştır)
        # Eğer login ekranı isterseniz, bu kısmı silip bir LoginWindow ekleyebilirsiniz.

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=170, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Analiz Sistemi", 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.data_button = ctk.CTkButton(self.sidebar_frame, text="Veri Tablosu", command=self.show_data_frame,
                                          font=ctk.CTkFont(size=13, weight="bold"))
        self.data_button.grid(row=1, column=0, padx=20, pady=10)

        self.live_graph_button = ctk.CTkButton(self.sidebar_frame, text="Canlı Grafik", command=self.show_live_graph_frame,
                                                font=ctk.CTkFont(size=13, weight="bold"))
        self.live_graph_button.grid(row=2, column=0, padx=20, pady=10)

        self.report_button = ctk.CTkButton(self.sidebar_frame, text="PDF Raporu Oluştur", command=self.generate_report,
                                            font=ctk.CTkFont(size=13, weight="bold"))
        self.report_button.grid(row=3, column=0, padx=20, pady=10)

        self.alarm_panel = ctk.CTkFrame(self.sidebar_frame, corner_radius=8, fg_color="#4a4a4a")
        self.alarm_panel.grid(row=4, column=0, padx=20, pady=(10, 10), sticky="ew")
        self.alarm_panel.grid_columnconfigure(0, weight=1)

        self.alarm_title_label = ctk.CTkLabel(
            self.alarm_panel,
            text="Sıcaklık Alarm Durumu",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        )
        self.alarm_title_label.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")

        self.alarm_risk_label = ctk.CTkLabel(
            self.alarm_panel,
            text="Risk Seviyesi: -",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        self.alarm_risk_label.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="w")

        self.alarm_message_label = ctk.CTkLabel(
            self.alarm_panel,
            text="Veri bekleniyor",
            wraplength=130,
            justify="left",
            anchor="w",
            text_color="white"
        )
        self.alarm_message_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        self.pressure_alarm_panel = ctk.CTkFrame(self.sidebar_frame, corner_radius=8, fg_color="#4a4a4a")
        self.pressure_alarm_panel.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.pressure_alarm_panel.grid_columnconfigure(0, weight=1)

        self.pressure_alarm_title_label = ctk.CTkLabel(
            self.pressure_alarm_panel,
            text="Basınç Alarm Durumu",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        )
        self.pressure_alarm_title_label.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")

        self.pressure_alarm_risk_label = ctk.CTkLabel(
            self.pressure_alarm_panel,
            text="Risk Seviyesi: -",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        self.pressure_alarm_risk_label.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="w")

        self.pressure_alarm_message_label = ctk.CTkLabel(
            self.pressure_alarm_panel,
            text="Veri yok",
            wraplength=130,
            justify="left",
            anchor="w",
            text_color="white"
        )
        self.pressure_alarm_message_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        self.current_alarm_panel = ctk.CTkFrame(self.sidebar_frame, corner_radius=8, fg_color="#4a4a4a")
        self.current_alarm_panel.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.current_alarm_panel.grid_columnconfigure(0, weight=1)

        self.current_alarm_title_label = ctk.CTkLabel(
            self.current_alarm_panel,
            text="Akım Alarm Durumu",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        )
        self.current_alarm_title_label.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="w")

        self.current_alarm_risk_label = ctk.CTkLabel(
            self.current_alarm_panel,
            text="Risk Seviyesi: -",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white"
        )
        self.current_alarm_risk_label.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="w")

        self.current_alarm_message_label = ctk.CTkLabel(
            self.current_alarm_panel,
            text="Veri yok",
            wraplength=130,
            justify="left",
            anchor="w",
            text_color="white"
        )
        self.current_alarm_message_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Tema:", anchor="w")
        self.appearance_mode_label.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, 
                                                            values=["Dark", "Light", "System"],
                                                            command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=11, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark") 


        # --- Main Frame for Content ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # Data Table Frame
        self.data_frame = DataTableFrame(self.main_frame, self)
        self.frames["data"] = self.data_frame
        
        # Live Graph Frame
        self.live_graph_frame = LiveGraphFrame(self.main_frame, self)
        self.frames["live_graph"] = self.live_graph_frame

        self.show_frame("live_graph") 

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        # Önce tüm frameleri sakla
        for name, f in self.frames.items():
            f.grid_remove()
        
        # İstenen frame'i göster
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def show_data_frame(self):
        self.data_frame.refresh_data()
        self.show_frame("data")

    def show_live_graph_frame(self):
        self.show_frame("live_graph")

    def generate_report(self):
        df_24h = read_latest_df(hours_back=24)
        if df_24h.empty:
            messagebox.showinfo("Bilgi", "Son 24 saatte rapor oluşturulacak veri yok.")
            return

        summary = compute_summary(df_24h)
        try:
            report_path = OUT_DIR / f"report_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            create_pdf_report_task(df_24h, summary, report_path)
            messagebox.showinfo("Başarılı", f"PDF raporu oluşturuldu:\n{report_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"PDF raporu oluşturulamadı: {e}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def update_alarm_panel(self, summary_data: dict):
        def resolve_panel_state(risk_seviyesi, message_text):
            if risk_seviyesi == "Normal":
                panel_color = "#2e7d32"
            elif risk_seviyesi == "Orta":
                panel_color = "#b8860b"
            elif risk_seviyesi == "Yüksek":
                panel_color = "#c62828"
            else:
                panel_color = "#4a4a4a"
                risk_seviyesi = "-"
                if not message_text:
                    message_text = "Veri yok"

            return panel_color, f"Risk Seviyesi: {risk_seviyesi}", message_text

        if summary_data.get("kayıt_sayısı", 0) == 0:
            temp_color, temp_risk_text, temp_message_text = "#4a4a4a", "Risk Seviyesi: -", "Veri bekleniyor"
            pressure_color, pressure_risk_text, pressure_message_text = "#4a4a4a", "Risk Seviyesi: -", "Veri yok"
            current_color, current_risk_text, current_message_text = "#4a4a4a", "Risk Seviyesi: -", "Veri yok"
        else:
            temp_color, temp_risk_text, temp_message_text = resolve_panel_state(
                summary_data.get("risk_seviyesi", "-"),
                summary_data.get("bakim_mesaji", "Veri yok")
            )
            pressure_color, pressure_risk_text, pressure_message_text = resolve_panel_state(
                summary_data.get("basinc_risk_seviyesi", "-"),
                summary_data.get("basinc_mesaji", "Veri yok")
            )
            current_color, current_risk_text, current_message_text = resolve_panel_state(
                summary_data.get("akim_risk_seviyesi", "-"),
                summary_data.get("akim_mesaji", "Veri yok")
            )

        self.alarm_panel.configure(fg_color=temp_color)
        self.alarm_risk_label.configure(text=temp_risk_text)
        self.alarm_message_label.configure(text=temp_message_text)

        self.pressure_alarm_panel.configure(fg_color=pressure_color)
        self.pressure_alarm_risk_label.configure(text=pressure_risk_text)
        self.pressure_alarm_message_label.configure(text=pressure_message_text)

        self.current_alarm_panel.configure(fg_color=current_color)
        self.current_alarm_risk_label.configure(text=current_risk_text)
        self.current_alarm_message_label.configure(text=current_message_text)

    def on_closing(self):
        if messagebox.askokcancel("Çıkış", "Uygulamayı kapatmak istediğinizden emin misiniz?"):
            self.live_graph_frame.stop_sim()
            self.destroy()
            sys.exit(0)


class DataTableFrame(ctk.CTkFrame):
    def __init__(self, parent_frame, app_instance):
        super().__init__(parent_frame, corner_radius=0)
        self.app = app_instance
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Gerçek Zamanlı Veri Tablosu", 
                                        font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.refresh_button = ctk.CTkButton(self, text="Yenile", command=self.refresh_data, 
                                            width=100, font=ctk.CTkFont(size=12, weight="bold"))
        self.refresh_button.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Standart ttk.Style kullanarak Treeview stilizasyonu (CTkStyle hatası düzeltildi)
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # CTk tema renklerini kullanarak ttk stilini özelleştirme
        style.configure("Treeview", 
                        background=self.cget("fg_color")[0], 
                        fieldbackground=self.cget("fg_color")[0], 
                        foreground=ctk.ThemeManager.theme["CTkLabel"]["text_color"][0],
                        rowheight=25)
        style.map('Treeview', background=[('selected', ctk.ThemeManager.theme["CTkButton"]["fg_color"][0])])
        style.configure("Treeview.Heading", 
                        background=ctk.ThemeManager.theme["CTkButton"]["fg_color"][0], 
                        foreground=ctk.ThemeManager.theme["CTkButton"]["text_color"][0],
                        font=('Segoe UI', 10, 'bold'))
        
        # ttk.Treeview kullanılıyor
        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.vsb = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.refresh_data()

    def refresh_data(self):
        df = read_latest_df(200)
        
        cols = ["Id", "Tarih", "Sicaklik", "Basinc", "Akim", "Anomali"]

        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=120 if c != "Tarih" else 180)

        self.tree.delete(*self.tree.get_children())
        
        if df.empty:
            return

        for _, row in df.iloc[::-1].iterrows():
            vals = []
            for c in cols:
                value = row.get(c, "-")

                if c == "Tarih" and isinstance(value, pd.Timestamp):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif pd.isna(value):
                    value = "-"

                vals.append(value)

            tag = "anomaly" if bool(row.get("Anomali", False)) else ""
            self.tree.insert("", "end", values=vals, tags=(tag,))

        self.tree.tag_configure("anomaly", background="#8b0000", foreground="white")

class LiveGraphFrame(ctk.CTkFrame):
    def __init__(self, parent_frame, app_instance):
        super().__init__(parent_frame, corner_radius=0)
        self.app = app_instance
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.proc: subprocess.Popen | None = None
        self.is_alarm_on = False
        self.ani = None

        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(header_frame, text="Canlı Sıcaklık İzleme", 
                                        font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w")

        # Simulator Controls
        self.status_label = ctk.CTkLabel(header_frame, text="Simülatör: DURDU", text_color="red", 
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=0, column=1, padx=20, sticky="e")

        self.start_button = ctk.CTkButton(header_frame, text="Başlat", command=self.start_sim, 
                                          fg_color="#28a745", hover_color="#218838")
        self.start_button.grid(row=0, column=2, padx=5)

        self.stop_button = ctk.CTkButton(header_frame, text="  Durdur", command=self.stop_sim, 
                                         fg_color="#dc3545", hover_color="#c82333", state="disabled")
        self.stop_button.grid(row=0, column=3, padx=5)

        # Summary Cards Frame
        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.summary_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.summary_frame.grid_rowconfigure((0, 1), weight=1)
        
        self.total_records_card = self._create_summary_card(self.summary_frame, "Son 200 Kayıt", "0", 0, "#007acc", row=0)
        self.avg_temp_card = self._create_summary_card(self.summary_frame, "Ortalama Sıcaklık", "0.00°C", 1, "#28a745", row=0)
        self.max_min_card = self._create_summary_card(self.summary_frame, "Sıcaklık Aralığı", "N/A", 2, "#ffc107", row=0)
        self.anomalies_card = self._create_summary_card(self.summary_frame, "Anomali Sayısı", "0 (0.0%)", 0, "#dc3545", row=1)
        self.avg_pressure_card = self._create_summary_card(self.summary_frame, "Ortalama Basınç", "N/A", 1, "#1f6aa5", row=1)
        self.avg_current_card = self._create_summary_card(self.summary_frame, "Ortalama Akım", "N/A", 2, "#2e8b57", row=1)

        # Matplotlib Grafik Alanı
        self.fig, self.ax = plt.subplots(figsize=(9, 5))
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        self._start_animation()

    def _create_summary_card(self, parent, title, value, column, color, row=0):
        card_frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=color)
        card_frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card_frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        value_label = ctk.CTkLabel(card_frame, text=value, font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        value_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        return value_label

    def _update_summary_cards(self, summary_data):
        self.total_records_card.configure(text=str(summary_data["kayıt_sayısı"]))
        
        ortalama = summary_data['ortalama']
        min_val = summary_data['min']
        max_val = summary_data['max']
        avg_pressure = summary_data.get("ortalama_basinc")
        avg_current = summary_data.get("ortalama_akim")
        risk_seviyesi = summary_data.get("risk_seviyesi", "-")
        bakim_mesaji = summary_data.get("bakim_mesaji", "Veri yok")

        if avg_pressure is None or avg_current is None:
            df = read_latest_df(200)
            if not df.empty:
                if avg_pressure is None and "Basinc" in df.columns:
                    avg_pressure = float(df["Basinc"].mean())
                if avg_current is None and "Akim" in df.columns:
                    avg_current = float(df["Akim"].mean())
        
        if ortalama is not None:
            self.avg_temp_card.configure(text=f"{ortalama:.2f}°C")
            self.max_min_card.configure(text=f"{min_val:.2f} - {max_val:.2f}°C")
            self.anomalies_card.configure(text=f"{summary_data['anomali_sayısı']} ({summary_data['anomali_oranı']})")
        else:
             self.avg_temp_card.configure(text="N/A")
             self.max_min_card.configure(text="N/A")
             self.anomalies_card.configure(text="0 (0.0%)")

        if avg_pressure is not None:
            self.avg_pressure_card.configure(text=f"{avg_pressure:.2f}")
        else:
            self.avg_pressure_card.configure(text="N/A")

        if avg_current is not None:
            self.avg_current_card.configure(text=f"{avg_current:.2f}")
        else:
            self.avg_current_card.configure(text="N/A")

        self.app.update_alarm_panel(summary_data)


    def _play_alarm(self):
        if not self.is_alarm_on and WINSOUND_OK:
            try:
                winsound.PlaySound("SystemExit", winsound.SND_ALIAS | winsound.SND_ASYNC)
                self.is_alarm_on = True
                print("!!! ANOMALİ ALARMI ÇALDI !!!")
            except Exception as e:
                print(f"Ses çalma hatası: {e}")

    def _stop_alarm(self):
        if self.is_alarm_on and WINSOUND_OK:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
                self.is_alarm_on = False
            except Exception:
                pass

    def _update_plot(self, frame):
        try:
            # 1. Veriyi Çek ve Özeti Hesapla
            df = read_latest_df(200)
            print(f"[DEBUG] df shape: {df.shape}")
            summary = compute_summary(df)
            self._update_summary_cards(summary)

            self.ax.clear()
            
            # Tema rengine göre dinamik ayar (Matplotlib'i özelleştirme)
            #text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"][0]
            #bg_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][0]
             #plot_bg_color = ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"][0]
            text_color = "#ffffff"  # beyaz
            bg_color = "#2b2b2b"    # koyu gri
            plot_bg_color = "#1e1e1e"


            self.ax.set_title("Canli Sensor Verileri (Son 200 Kayit)", color=text_color)
            self.ax.set_xlabel("Zaman", color=text_color)
            self.ax.set_ylabel("Sensor Degerleri", color=text_color)
            
            self.fig.patch.set_facecolor(bg_color)
            self.ax.set_facecolor(plot_bg_color)
            self.ax.tick_params(colors=text_color)
            self.ax.spines['left'].set_color(text_color)
            self.ax.spines['bottom'].set_color(text_color)
            self.ax.grid(True, linestyle='--', alpha=0.6, color='gray')


            # 2. Grafik Çizimi Kontrolü
            required_cols = {"Tarih", "Sicaklik", "Basinc", "Akim", "Anomali"}
            if df.empty or len(df) < 2 or not required_cols.issubset(df.columns):
                # Veri yoksa veya çizgi çizmeye yetecek kadar (en az 2) nokta yoksa
                self._stop_alarm()
                self.ax.text(0.5, 0.5, "Simülatör çalışıyor, veri bekleniyor...", 
                             color=text_color, ha='center', va='center', fontsize=12)
                self.canvas.draw_idle()
                return
            # >>> EKSİK KISIM BURASIYDI: X ve Y verisi burada tanımlanmalı <<<
            
            # Tarih verisini Matplotlib'in sayısal formatına çeviriyoruz.
            x_data = mdates.date2num(df["Tarih"])
            sicaklik_data = df["Sicaklik"]
            basinc_data = df["Basinc"]
            akim_data = df["Akim"]

            # 3. Çizgiyi Çiz
            self.ax.plot(x_data, sicaklik_data, label="Sicaklik", color="red", linewidth=2)
            self.ax.plot(x_data, basinc_data, label="Basinc", color="blue", linewidth=2)
            self.ax.plot(x_data, akim_data, label="Akim", color="green", linewidth=2)
            self.fig.tight_layout()
            # 4. Anomalileri İşaretle
            anomalies = df[df["Anomali"] == True]
            
            if not anomalies.empty:
                # Scatter plot da aynı şekilde sayısal X verisi kullanmalı
                anomaly_x = mdates.date2num(anomalies["Tarih"])
                anomaly_y = anomalies["Sicaklik"]
                self.ax.scatter(anomaly_x, anomaly_y, color="red", label="Anomali", s=50, zorder=5)
                self._play_alarm()
            else:
                self._stop_alarm()

            # 5. Ekseni ve Görünümü Güncelle
            self.ax.legend(facecolor=plot_bg_color, edgecolor='gray', labelcolor=text_color)
            self.fig.autofmt_xdate()
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            # Grafik eksen sınırlarını dinamik olarak ayarla (sadece görünebilir alanı kapsayacak şekilde)
            self.ax.relim()
            self.ax.autoscale_view()
            
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Plot update error: {e}")
            self._stop_alarm()
            self.canvas.draw_idle()

    def _start_animation(self):
     if self.ani is None:
        self.ani = FuncAnimation(
            self.fig, self._update_plot,
            interval=1000, cache_frame_data=False, blit=False
        )
        self.canvas.draw_idle()
        self.fig.canvas.draw()


    def _stop_animation(self):
        if self.ani:
            self.ani.event_source.stop()
            self.ani = None

            # Grafik alanını temizleyip boş bir eksen göster
            self.ax.clear()
            self.ax.set_title("Canlı Sıcaklık Verisi (Durduruldu)")
            self.canvas.draw_idle()

    def start_sim(self):
        if self.proc and (self.proc.poll() is None):
            messagebox.showinfo("Bilgi", "Simülatör zaten çalışıyor.")
            return

        try:
            self.proc = start_simulator_process()

            time.sleep(2)

            if self.proc.poll() is not None:
                exit_code = self.proc.returncode
                self.proc = None

                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.status_label.configure(text="Simülatör: DURDU", text_color="red")
                self._stop_alarm()
                self._stop_animation()

                messagebox.showerror(
                    "Simülatör Başlatılamadı",
                    "C# simülatörü başlatıldıktan hemen sonra kapandı.\n"
                    f"Çıkış kodu: {exit_code}\n\n"
                    "Lütfen simulator.log dosyasını kontrol edin.\n"
                    "Olası nedenler: yanlış çalışma klasörü, .NET SDK sorunu, csproj yolu hatası veya C# tarafında çalışma zamanı hatası."
                )
                return

            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="Simülatör: ÇALISIYOR", text_color="green")
            self._start_animation()
            messagebox.showinfo("Bilgi", "Simülatör başlatıldı.")

        except Exception as e:
            self.proc = None
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_label.configure(text="Simülatör: DURDU", text_color="red")

            messagebox.showerror(
                "Hata",
                "Simülatör başlatılamadı.\n"
                "Lütfen simulator.log dosyasını kontrol edin.\n\n"
                f"Hata: {e}"
            )

    def stop_sim(self):
        if not self.proc:
            messagebox.showinfo("Bilgi", "Çalışan simülatör yok.")
            return
        stop_process(self.proc)
        self.proc = None
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Simülatör: DURDU", text_color="red")
        self._stop_alarm()
        self._stop_animation()
        messagebox.showinfo("Bilgi", "Simülatör durduruldu.")

# --- Uygulama Başlatıcılar ---
def main():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main() 
