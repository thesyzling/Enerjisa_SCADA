import os
import pandas as pd
import numpy as np
import requests  # ollama kütüphanesi yerine requests kullanıyoruz
import datetime
import logging
from pathlib import Path

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scada_fault_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SCADA_Analyzer")


class SCADAFaultAnalyzer:
    def __init__(self):
        # Dizin yapısını oluştur
        self.base_dir = Path.cwd()
        self.prompts_dir = self.base_dir / "prompts"
        self.data_dir = self.base_dir / "data"
        self.output_dir = self.base_dir / "output"

        # Dizinleri oluştur
        self._create_directories()

        # Prompt dosyalarını yükle
        self.fault_analysis_prompt = self._load_prompt("fault_analysis_prompt.txt")

        # Ollama API ayarları
        self.ollama_host = "http://localhost:11434"
        self.ollama_model = "llama3.1:8b"
        self.model_options = {
            'num_gpu_layers': 10,
            'num_ctx': 4096,
            'num_threads': 8,
            'temperature': 0.3,
            'top_p': 0.9,
            'repeat_penalty': 1.1
        }

    def _create_directories(self):
        """Gerekli dizinleri oluşturur"""
        for directory in [self.prompts_dir, self.data_dir, self.output_dir]:
            directory.mkdir(exist_ok=True)
            logger.info(f"Dizin oluşturuldu: {directory}")

    def _load_prompt(self, prompt_name):
        """Prompt dosyasını yükler"""
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            logger.error(f"Prompt dosyası bulunamadı: {prompt_path}")
            raise FileNotFoundError(f"Prompt dosyası bulunamadı: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_scada_data(self, file_path):
        """SCADA verisini yükler ve temizler"""
        try:
            # CSV dosyasını yükle
            df = pd.read_csv(file_path)
            logger.info(f"Veri yüklendi: {file_path}, {len(df)} satır")

            # Sütun adlarını düzelt (boşluk ve özel karakterleri temizle)
            df.columns = [col.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                          for col in df.columns]

            # Zaman sütununu numeric olarak tut (sıralama için)
            if 'time' in df.columns:
                df['time'] = pd.to_numeric(df['time'], errors='coerce')
                df = df.sort_values('time')
                logger.info("Zaman sütunu sıralandı")

            return df
        except Exception as e:
            logger.error(f"Veri yüklenirken hata: {str(e)}")
            raise

    def analyze_fault_scenarios(self, df):
        """Arıza senaryolarını analiz eder"""
        summary = {
            'total_records': len(df),
            'time_range': f"{df['time'].min():.6f} - {df['time'].max():.6f} saniye",
            'pickup_events': {},
            'trip_events': {},
            'critical_events': []
        }

        # PICK UP sinyallerini analiz et
        pickup_columns = [col for col in df.columns if 'PICK_UP' in col and '67' in col]
        for col in pickup_columns:
            active_count = df[df[col] == 1].shape[0]
            if active_count > 0:
                summary['pickup_events'][col] = {
                    'count': active_count,
                    'times': df[df[col] == 1]['time'].tolist()[:3]  # İlk 3 zaman damgası
                }

        # TRIP sinyallerini analiz et
        trip_columns = [col for col in df.columns if 'TRIP' in col and '67' in col]
        for col in trip_columns:
            active_count = df[df[col] == 1].shape[0]
            if active_count > 0:
                summary['trip_events'][col] = {
                    'count': active_count,
                    'times': df[df[col] == 1]['time'].tolist()[:3]  # İlk 3 zaman damgası
                }

        # Kritik olayları tespit et (yüksek akım)
        for idx, row in df.iterrows():
            # Yüksek akım kontrolü (normal işletme akımından çok daha yüksek)
            high_current = False
            for phase in ['IL1', 'IL2', 'IL3']:
                if phase in df.columns and abs(row[phase]) > 10:  # 10A üzerinde yüksek akım
                    high_current = True

            # Nötr akımı kontrolü
            neutral_high = False
            if 'Io' in df.columns and abs(row['Io']) > 5:  # 5A üzerinde nötr akımı
                neutral_high = True

            if high_current or neutral_high:
                summary['critical_events'].append({
                    'time': row['time'],
                    'IL1': row.get('IL1', 0),
                    'IL2': row.get('IL2', 0),
                    'IL3': row.get('IL3', 0),
                    'Io': row.get('Io', 0),
                    'pickup_signals': [col for col in pickup_columns if row[col] == 1],
                    'trip_signals': [col for col in trip_columns if row[col] == 1]
                })

        return summary

    def generate_data_summary(self, summary):
        """Veri özetini metin formatında oluşturur"""
        summary_text = f"Toplam Kayıt Sayısı: {summary['total_records']}\n"
        summary_text += f"Zaman Aralığı: {summary['time_range']}\n\n"

        # PICK UP olayları
        summary_text += "PICK UP Sinyalleri:\n"
        if summary['pickup_events']:
            for signal, data in summary['pickup_events'].items():
                summary_text += f"- {signal}: {data['count']} kez tetiklendi, İlk zamanlar: {', '.join([f'{t:.4f}' for t in data['times']])}\n"
        else:
            summary_text += "- Hiç PICK UP sinyali yok\n"

        # TRIP olayları
        summary_text += "\nTRIP Sinyalleri:\n"
        if summary['trip_events']:
            for signal, data in summary['trip_events'].items():
                summary_text += f"- {signal}: {data['count']} kez tetiklendi, İlk zamanlar: {', '.join([f'{t:.4f}' for t in data['times']])}\n"
        else:
            summary_text += "- Hiç TRIP sinyali yok\n"

        # Kritik olaylar
        summary_text += "\nKritik Olaylar:\n"
        if summary['critical_events']:
            for i, event in enumerate(summary['critical_events'][:5]):  # İlk 5 olayı göster
                summary_text += f"{i + 1}. Zaman: {event['time']:.4f}s\n"
                summary_text += f"   Akımlar: IL1={event['IL1']:.2f}A, IL2={event['IL2']:.2f}A, IL3={event['IL3']:.2f}A, Io={event['Io']:.2f}A\n"
                summary_text += f"   PICK UP: {', '.join(event['pickup_signals']) if event['pickup_signals'] else 'Yok'}\n"
                summary_text += f"   TRIP: {', '.join(event['trip_signals']) if event['trip_signals'] else 'Yok'}\n\n"
        else:
            summary_text += "- Kritik olay tespit edilmedi\n"

        return summary_text

    def analyze_with_ollama(self, data_summary):
        """Ollama API ile arıza analizi yapar"""
        logger.info("Ollama API ile analiz başlatılıyor...")

        # Prompt'u hazırla
        full_prompt = self.fault_analysis_prompt.replace("{data_summary}", data_summary)

        try:
            # Ollama API'sine istek gönder
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    'model': self.ollama_model,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': self.model_options  # Bu satırı ekleyin
                },
                timeout=180  # Büyük modeller için daha uzun zaman
            )

            response.raise_for_status()  # HTTP hatası kontrolü
            result = response.json()

            logger.info("Ollama analizi tamamlandı")
            return result['response']
        except requests.exceptions.ConnectionError:
            logger.error(
                "Ollama'ya bağlanılamadı. Lütfen Ollama'yı ayrı bir terminalde çalıştırdığınızdan emin olun (ollama serve)")
            return "HATA: Ollama'ya bağlanılamadı. Lütfen Ollama'yı ayrı bir terminalde çalıştırdığınızdan emin olun."
        except Exception as e:
            logger.error(f"Ollama analiz hatası: {str(e)}")
            return f"Analiz hatası: {str(e)}"

    def save_results(self, results, file_name="analysis_results.txt"):
        """Analiz sonuçlarını kaydeder"""
        output_path = self.output_dir / file_name

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"## SCADA Arıza Analiz Raporu\n")
            f.write(f"## Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(results)

        logger.info(f"Analiz sonuçları kaydedildi: {output_path}")
        return output_path

    def run_analysis(self, file_path):
        """Tam analiz sürecini çalıştırır"""
        logger.info(f"Analiz başlıyor: {file_path}")

        try:
            # Veriyi yükle
            df = self.load_scada_data(file_path)

            # Veriyi analiz et
            summary = self.analyze_fault_scenarios(df)
            data_summary = self.generate_data_summary(summary)

            # Ollama ile analiz yap
            results = self.analyze_with_ollama(data_summary)

            # Sonuçları kaydet
            output_path = self.save_results(results,
                                            f"analysis_{Path(file_path).stem}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

            logger.info("Analiz başarıyla tamamlandı")
            return output_path, results
        except Exception as e:
            logger.error(f"Analiz hatası: {str(e)}")
            raise


def main():
    analyzer = SCADAFaultAnalyzer()

    # Mevcut CSV dosyalarını bul ve analiz et
    csv_files = list(analyzer.data_dir.glob("*.csv"))

    if not csv_files:
        logger.error("Analiz edilecek CSV dosyası bulunamadı!")
        print(
            "HATA: 'data' klasöründe CSV dosyası bulunamadı. Lütfen comtrade40_data.csv ve comtrade41_data.csv dosyalarını data klasörüne kopyalayın.")
        return

    for csv_file in csv_files:
        logger.info(f"İşleniyor: {csv_file}")
        output_path, results = analyzer.run_analysis(csv_file)

        print("\n=== Analiz Sonuçları ===")
        print(f"Kaydedildi: {output_path}")
        print("\nÖnizleme:")
        print(results[:500] + "..." if len(results) > 500 else results)
        print("=======================\n")


if __name__ == "__main__":
    main()