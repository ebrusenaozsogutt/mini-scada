from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Veritabanı yolu
DB_PATH = Path(__file__).resolve().parents[2] / "csharp" / "SensorSimulator" / "sensor_data.db"
print(f"DB yolu: {DB_PATH}")

# Veritabanına bağlan
conn = sqlite3.connect(DB_PATH)

# Son 100 kaydı çek
df = pd.read_sql_query(
    "SELECT Id, Tarih, Sicaklik FROM SensorData ORDER BY Id DESC LIMIT 100;",
    conn
)
conn.close()

# Id'ye göre küçükten büyüğe sırala (grafik düzgün çıksın)
df = df.sort_values("Id").reset_index(drop=True)

# Tarih sütununu datetime tipine çevir
df["Tarih"] = pd.to_datetime(df["Tarih"], format="%Y-%m-%d %H:%M:%S", errors="coerce")

# Anomalileri işaretle (<15 veya >35 derece)
df["Anomali"] = (df["Sicaklik"] < 15) | (df["Sicaklik"] > 35)

print("\nTespit edilen anomaliler:")
print(df[df["Anomali"] == True])

# Grafik çiz
plt.figure(figsize=(10,6))
plt.plot(df["Tarih"], df["Sicaklik"], label="Sıcaklık", color="blue")
plt.scatter(df[df["Anomali"] == True]["Tarih"],
            df[df["Anomali"] == True]["Sicaklik"],
            color="red", label="Anomali")
plt.xlabel("Zaman")
plt.ylabel("Sıcaklık (°C)")
plt.title("SQLite'den Çekilen Sıcaklık Verileri ve Anomaliler")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
