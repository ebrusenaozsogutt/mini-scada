# live_plot.py
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import time
import seaborn as sns

DB_PATH = Path(__file__).resolve().parents[2] / "csharp" / "SensorSimulator" / "sensor_data.db"
print(f"DB yolu: {DB_PATH}")

# Ayarlar
POLL_INTERVAL_MS = 2000   # 2000 ms = her 2 saniyede bir veri oku ve güncelle
TAIL_N = 200              # grafikte gösterilecek son N kayıt

# Matplotlib figür ve çizgiler hazırla
# plt.style.use('seaborn-darkgrid')
# Seaborn stili aktif et
sns.set_style('darkgrid')
fig, ax = plt.subplots(figsize=(10,6))
line, = ax.plot([], [], label="Sıcaklık", marker='o', linewidth=1)
scat = ax.scatter([], [], color='red', label='Anomali')
ax.set_xlabel("Zaman")
ax.set_ylabel("Sıcaklık (°C)")
ax.set_title("Canlı Sıcaklık Verileri (SQLite)")
ax.legend()

def fetch_df():
    """Veritabanından son TAIL_N kaydı çek. Hataları yakala."""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        query = f"SELECT Id, Tarih, Sicaklik FROM SensorData ORDER BY Id DESC LIMIT {TAIL_N};"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return df
        df = df.sort_values("Id").reset_index(drop=True)
        df["Tarih"] = pd.to_datetime(df["Tarih"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        df = df.dropna(subset=["Tarih", "Sicaklik"])
        return df
    except Exception as e:
        print("DB okuma hatası:", e)
        return pd.DataFrame(columns=["Id","Tarih","Sicaklik"])

def update(frame):
    """FuncAnimation tarafından periyodik çağrılır."""
    df = fetch_df()
    if df.empty:
        return line, scat

    # Anomali tanımı (manual)
    anomalies = df[(df["Sicaklik"] < 15) | (df["Sicaklik"] > 35)]

    # X ve Y verisi (tarih)
    x = df["Tarih"]
    y = df["Sicaklik"]

    # Çizgiyi ve scatter'ı güncelle
    line.set_data(x, y)
    if not anomalies.empty:
        scat.set_offsets(list(zip(anomalies["Tarih"].map(mdates.date2num), anomalies["Sicaklik"])))
    else:
        scat.set_offsets([])

    # Ekseni ayarla: xlim, ylim
    ax.relim()
    ax.autoscale_view()

    # X ekseni tarih formatı
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()
    return line, scat

# Animasyonu başlat
ani = FuncAnimation(fig, update, interval=POLL_INTERVAL_MS, blit=False)

print("Canlı grafik başlatıldı. Grafiği kapatmak için pencereyi kapat veya Ctrl+C.")
plt.show()
