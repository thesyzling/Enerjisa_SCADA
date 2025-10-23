import torch
import pandas as pd
import datetime
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# --- Logging Ayarları ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s (Local Model) - %(message)s',
    handlers=[
        logging.FileHandler("local_model_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Local_Model_Analyzer")


class LocalAnalyzer:
    def __init__(self, model_path):
        self.base_dir = Path.cwd()
        self.prompts_dir = self.base_dir / "prompts"
        self.data_dir = self.base_dir / "data"
        self.output_dir = self.base_dir / "fine_tune_output"
        self.output_dir.mkdir(exist_ok=True)

        self.fault_analysis_prompt = self._load_prompt("fault_analysis_prompt.txt")

        # --- Model ve Tokenizer'ı Doğrudan Yükleme ---
        logger.info(f"Uzman model '{model_path}' klasöründen yükleniyor...")
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model klasörü bulunamadı: '{model_path}'. Lütfen merge_model.py'yi çalıştırdığınızdan emin olun.")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",  # Modeli otomatik olarak GPU'ya yükle
        )

        # Metin üretimi için bir pipeline oluşturuyoruz
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )
        logger.info("Uzman model başarıyla yüklendi ve kullanıma hazır.")

    def _load_prompt(self, prompt_name):
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt dosyası bulunamadı: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_scada_data(self, file_path):
        df = pd.read_csv(file_path)
        df.columns = [col.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_') for col in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_numeric(df['time'], errors='coerce')
            df = df.sort_values('time')
        return df

    def generate_data_summary(self, df):
        # Bu fonksiyon main.py'deki ile aynı
        summary = {
            'total_records': len(df),
            'time_range': f"{df['time'].min():.6f} - {df['time'].max():.6f} saniye"
        }
        summary_text = f"Toplam Kayıt Sayısı: {summary['total_records']}\n"
        summary_text += f"Zaman Aralığı: {summary['time_range']}\n\n"
        # ... (Daha detaylı özet eklenebilir) ...
        return summary_text

    def analyze(self, data_summary):
        logger.info(f"Yerel model ile analiz başlatılıyor...")

        # Prompt'u, modeli eğittiğimiz formatla %100 aynı yapıyoruz.
        prompt_start = self.fault_analysis_prompt.split('### Veri Özeti')[0].strip()
        full_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n### Talimat:\n{prompt_start}\n\n### Veri Özeti:\n{data_summary}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

        # Pipeline'ı kullanarak metin üretiyoruz
        outputs = self.pipe(
            full_prompt,
            max_new_tokens=1024,  # Ne kadar uzun bir cevap istediğimiz
            do_sample=False,  # Daha deterministik sonuçlar için
            temperature=0.1,
            top_p=0.9,
            eos_token_id=self.tokenizer.eos_token_id
        )

        # Pipeline'ın çıktısından sadece üretilen yeni metni alıyoruz
        generated_text = outputs[0]['generated_text']
        # Prompt'u sonuçtan çıkarıp sadece modelin cevabını döndürüyoruz
        response = generated_text.split("<|end_header_id|>\n\n")[-1]

        return response.strip()


def main():
    # Eğitilmiş ve birleştirilmiş modelimizin bulunduğu klasörün yolu
    finetuned_model_path = "./enerjisa-scada-analyzer-v1-merged"

    analyzer = LocalAnalyzer(finetuned_model_path)

    csv_files = list(analyzer.data_dir.glob("*.csv"))
    if not csv_files:
        logger.error("'data' klasöründe analiz edilecek CSV dosyası bulunamadı!")
        return

    logger.info(f"Yerel uzman model ile {len(csv_files)} adet dosya analiz edilecek.")

    for csv_file in csv_files:
        try:
            logger.info(f"İşleniyor: {csv_file.name}")
            df = analyzer.load_scada_data(csv_file)
            data_summary = analyzer.generate_data_summary(df)
            results = analyzer.analyze(data_summary)

            # Sonucu yeni klasöre kaydet
            output_filename = f"analysis_{csv_file.stem}_LOCAL_FINETUNED.txt"
            output_path = analyzer.output_dir / output_filename

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"## Yerel Finetuned Model Analiz Raporu\n")
                f.write(f"## Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(results)

            logger.info(f"Sonuçlar kaydedildi: {output_path}")
            print(f"\n✅ Analiz tamamlandı -> {output_path.name}")

        except Exception as e:
            logger.error(f"{csv_file.name} işlenirken bir hata oluştu: {e}")
            print(f"\n❌ HATA: {csv_file.name} işlenemedi.")


if __name__ == "__main__":
    main()