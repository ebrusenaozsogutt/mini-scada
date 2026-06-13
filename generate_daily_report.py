# generate_daily_report.py
from pathlib import Path
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timedelta

# === AYARLAR ===
# Raporun kapsayacağı zaman penceresi: son 24 saat
HOURS_BACK = 24
# Grafikte gösterilecek örnek sayısı (çok büyük olursa PDF şişer)
TAIL_N = 10
# Veritabanında tutulacak maksimum satır sayısı (fazlası silinecek)
RETAIN_MAX_ROWS = 10

# === YOLLAR ===
BASE_DIR = Path(__file__).resolve().parents[2]  # .../src
DB_PATH = BASE_DIR / "csharp" / "SensorSimulator" / "sensor_data.db"
OUT_DIR = Path(__file__).resolve().parent / "outputs" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def read_data_from_sqlite():
    """SQLite'tan son 24 saate ait verileri DataFrame olarak döndürür."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Veritabanı bulunamadı: {DB_PATH}")

    since_dt = datetime.now() - timedelta(hours=HOURS_BACK)
    since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Tarih TEXT kolon olduğu için ISO formatı ile karşılaştırma güvenli
    conn = sqlite3.connect(DB_PATH, timeout=5)
    query = """
        SELECT Id, Tarih, Sicaklik
        FROM SensorData
        WHERE Tarih >= ?
        ORDER BY Id ASC;
    """
    df = pd.read_sql_query(query, conn, params=(since_str,))
    conn.close()

    if df.empty:
        return df

    # Dönüşümler
    df["Tarih"] = pd.to_datetime(df["Tarih"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["Tarih", "Sicaklik"]).reset_index(drop=True)

    # Çok fazla satır varsa son TAIL_N kadarını al
    if len(df) > TAIL_N:
        df = df.tail(TAIL_N).reset_index(drop=True)

    return df

def compute_summary(df: pd.DataFrame) -> dict:
    """Özet metrikleri hesapla."""
    if df.empty:
        return {
            "kayıt_sayısı": 0, "min": None, "max": None, "ortalama": None,
            "std": None, "anomali_sayısı": 0, "anomali_oranı": "0%"
        }
    summary = {}
    summary["kayıt_sayısı"] = len(df)
    summary["min"] = float(df["Sicaklik"].min())
    summary["max"] = float(df["Sicaklik"].max())
    summary["ortalama"] = float(df["Sicaklik"].mean())
    summary["std"] = float(df["Sicaklik"].std(ddof=0))

    # Anomali kuralı (manuel eşikler)
    df["Anomali"] = (df["Sicaklik"] < 15) | (df["Sicaklik"] > 35)
    anom_count = int(df["Anomali"].sum())
    summary["anomali_sayısı"] = anom_count
    ratio = 100.0 * anom_count / len(df) if len(df) > 0 else 0.0
    summary["anomali_oranı"] = f"{ratio:.1f}%"
    return summary

def make_pdf_report(df: pd.DataFrame, summary: dict, out_pdf: Path):
    """PDF raporu oluştur ve kaydet."""
    with PdfPages(out_pdf) as pdf:
        # Sayfa 1: Zaman serisi + anomaliler
        fig1, ax1 = plt.subplots(figsize=(11.69, 8.27))  # A4 yatay (yaklaşık)
        if df.empty:
            ax1.text(0.5, 0.5, "Son 24 saatte veri bulunamadı.", ha="center", va="center", fontsize=16)
        else:
            ax1.plot(df["Tarih"], df["Sicaklik"], label="Sıcaklık", linewidth=1.2)
            anomalies = df[df["Anomali"] == True]
            if not anomalies.empty:
                ax1.scatter(anomalies["Tarih"], anomalies["Sicaklik"], label="Anomali", color="red", s=25)

            ax1.set_xlabel("Zaman")
            ax1.set_ylabel("Sıcaklık (°C)")
            ax1.set_title(f"Sıcaklık Zaman Serisi — Son {HOURS_BACK} Saat")
            ax1.legend(loc="upper left")
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
            fig1.autofmt_xdate()

        pdf.savefig(fig1, bbox_inches="tight")
        plt.close(fig1)

        # Sayfa 2: Histogram + boxplot + metin
        fig2, ax2 = plt.subplots(figsize=(11.69, 8.27))
        if df.empty:
            ax2.text(0.5, 0.5, "Veri yok (histogram/boxplot oluşturulamadı).", ha="center", va="center", fontsize=16)
        else:
            # Histogram
            ax2.hist(df["Sicaklik"], bins=20, alpha=0.7)
            ax2.set_title("Sıcaklık Dağılımı (Histogram)")
            ax2.set_xlabel("Sıcaklık (°C)")
            ax2.set_ylabel("Frekans")

        pdf.savefig(fig2, bbox_inches="tight")
        plt.close(fig2)

        # Sayfa 3: Özet tablo (matplotlib table)
        fig3, ax3 = plt.subplots(figsize=(11.69, 8.27))
        ax3.axis('off')

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = f"Günlük Rapor — {now_str}\nKapsam: Son {HOURS_BACK} Saat"
        ax3.text(0.5, 0.95, title, ha="center", va="top", fontsize=16, fontweight="bold")

        # Özet metrikleri tabloya dönüştür
        rows = [
            ["Kayıt Sayısı", summary["kayıt_sayısı"]],
            ["Min (°C)", "—" if summary["min"] is None else f"{summary['min']:.2f}"],
            ["Maks (°C)", "—" if summary["max"] is None else f"{summary['max']:.2f}"],
            ["Ortalama (°C)", "—" if summary["ortalama"] is None else f"{summary['ortalama']:.2f}"],
            ["Std Sapma", "—" if summary["std"] is None else f"{summary['std']:.2f}"],
            ["Anomali Sayısı", summary["anomali_sayısı"]],
            ["Anomali Oranı", summary["anomali_oranı"]],
        ]
        the_table = ax3.table(cellText=rows, colLabels=["Metrik", "Değer"], loc="center", cellLoc="center")
        the_table.scale(1, 2)  # satır yüksekliği

        info_text = f"\nVeritabanı: {DB_PATH}\nRaporu oluşturan: generate_daily_report.py"
        ax3.text(0.01, 0.02, info_text, ha="left", va="bottom", fontsize=9)

        pdf.savefig(fig3, bbox_inches="tight")
        plt.close(fig3)

def cleanup_old_rows():
    """Tablo RETAIN_MAX_ROWS değerini aşıyorsa, en eski kayıtları sil."""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cur = conn.cursor()
    # Toplam satır sayısını öğren
    cur.execute("SELECT COUNT(*) FROM SensorData;")
    total = cur.fetchone()[0]

    deleted = 0
    if total > RETAIN_MAX_ROWS:
        # Kaç satır silinecek?
        to_delete = total - RETAIN_MAX_ROWS
        # En eski 'to_delete' kadar kaydı Id'ye göre sil
        # (alt sorgu ile en küçük Id'leri hedefliyoruz)
        cur.execute("""
            DELETE FROM SensorData
            WHERE Id IN (
                SELECT Id FROM SensorData ORDER BY Id ASC LIMIT ?
            );
        """, (to_delete,))
        deleted = cur.rowcount
        conn.commit()

    conn.close()
    return total, deleted

def main():
    print(f"DB yolu: {DB_PATH}")
    print(f"Rapor klasörü: {OUT_DIR}")

    # 1) Veriyi oku
    df = read_data_from_sqlite()
    print(f"Çekilen kayıt sayısı: {len(df)}")

    # 2) Özet hesapla
    summary = compute_summary(df)
    print("Özet:", summary)

    # 3) PDF üret
    out_pdf = OUT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    make_pdf_report(df, summary, out_pdf)
    print(f"PDF kaydedildi: {out_pdf}")

    # 4) (Opsiyonel ama önerilen) veri temizleme
    total_before, deleted = cleanup_old_rows()
    if deleted > 0:
        print(f"Veri temizleme: toplam {total_before} kayıt vardı, {deleted} eski kayıt silindi.")
    else:
        print(f"Veri temizleme: {total_before} kayıt var, temizlik gerekmedi (limit {RETAIN_MAX_ROWS}).")

if __name__ == "__main__":
    main()
