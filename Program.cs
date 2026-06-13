using System;
using System.IO;
using System.Globalization;

class Program
{
    static void Main(string[] args)
    {
        string filePath = "sensor_data.csv";

        // Dosya yoksa başlık oluştur
        if (!File.Exists(filePath))
        {
            File.WriteAllText(filePath, "Tarih,Sicaklik,Basinc,Akim\n");
        }

        Random rnd = new Random();

        Console.WriteLine("CSV yazma başladı...");

        while (true)
        {
            // Sıcaklık
            double sicaklik = (rnd.Next(0, 20) == 0)
                ? rnd.Next(90, 120)
                : 20 + rnd.NextDouble() * 10;

            // Basınç
            double basinc = 1 + rnd.NextDouble() * 9;

            // Akım
            double akim = rnd.Next(0, 50);

            string zaman = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

            // 🔥 EN KRİTİK DÜZELTME (nokta kullanımı)
            string line = $"{zaman}," +
                          $"{sicaklik.ToString("F2", CultureInfo.InvariantCulture)}," +
                          $"{basinc.ToString("F2", CultureInfo.InvariantCulture)}," +
                          $"{akim}";

            File.AppendAllText(filePath, line + "\n");

            Console.WriteLine($"Kaydedildi: {line}");

            System.Threading.Thread.Sleep(1000);
        }
    }
}