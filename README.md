Enerjisa_SCADA

SCADA arıza analizi ve durum farkındalığı için geliştirilen yerel (local) LLM destekli analiz uygulaması ve web arayüzü.
Proje; COMTRADE formatındaki olay/veri dosyalarını CSV’ye dönüştürüp işliyor, ardından yerel LLM ile otomatik özet, arıza sınıflandırma, kanıt/indis çıkarımı ve öneri üretimi yapıyor.

Not: Proje internet bağlantısı olmadan çalışacak şekilde tasarlanmıştır; gizli veriler ve saha kayıtları lokalde kalır.

Özellikler

Yerel LLM ile analiz: Ollama üzerinden çalışan LLM (ör. Llama 3, Gemma vb.) ile:

Olay özeti (TL;DR)

Olası arıza tipi ve olasılık

Deliller/indikasyonlar (akım/süre/koruma tetikleri vb.)

Kısa aksiyon önerileri (işletme ve bakım için)

COMTRADE → CSV dönüşümü:

.CFG + .DAT dosyalarını okuyup zaman-serisi CSV üretir

Örnekleme oranı, kanal adları vb. metaveriyi korur

Modern web arayüzü:

Dosya yükleme (COMTRADE veya CSV)

Grafiksel sinyal görüntüleme (akım/gerilim trendleri, event işaretleri)

LLM analiz çıktılarının panel görünümü

Tamamen lokal çalışma:

Veri dışarı çıkmaz

GPU bulunursa hızlanma (opsiyonel)

Mimarinin Kısa Özeti
[Web UI]  <—HTTP—>  [Backend API]
    |                    |
   Dosya               Dönüştürücü (COMTRADE→CSV)
   yükleme             Analiz Pipeline (Python)
    |                    |
   Grafikler   <—LLM—>  Yerel LLM (Ollama)


Web UI: (React/Streamlit/FastAPI-UI—proje yapına göre) dosya yükleme, grafik ve sonuçların gösterimi

Backend: Python tabanlı servis; COMTRADE okuma/dönüştürme, veri temizleme/özellik çıkarımı, LLM istemcisi

LLM: Ollama ile lokalde barındırılan model (ör. llama3, gemma2:9b, vb.)

Hızlı Başlangıç
1) Gereksinimler

Python 3.10+

Ollama (lokal LLM için) — https://ollama.com

(Opsiyonel) NVIDIA GPU + CUDA: hız için

2) Depoyu Klonla
git clone https://github.com/thesyzling/Enerjisa_SCADA.git
cd Enerjisa_SCADA

3) Python Ortamı
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt


requirements.txt yoksa, tipik bağımlılıklar:
fastapi, uvicorn, pydantic, pandas, numpy, matplotlib, plotly,
comtrade (veya pycomtrade), scipy, httpx/requests.

4) Ollama ve Model

Ollama’yı kurduktan sonra çalıştır:

# Ollama servisini başlat (OS’e göre farklı olabilir)
ollama serve
# Uygun bir model çek (örnekler)
ollama pull llama3
# veya
ollama pull gemma2:9b


.env dosyasında kullanılacak model adını belirt (varsayılan llama3):

LLM_MODEL=llama3
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434

5) Uygulamayı Çalıştır

Backend (ör. FastAPI/uvicorn) için:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


UI (proje yapına göre):

Streamlit ise:

streamlit run ui/app.py


React/Vite ise:

cd ui
npm install
npm run dev


Arayüz açıldıktan sonra COMTRADE (.cfg + .dat) veya CSV yükleyip analizi başlat.

Klasör Yapısı (Öneri)
Enerjisa_SCADA/
├─ app/
│  ├─ main.py               # FastAPI/Backend giriş
│  ├─ routers/
│  │  ├─ files.py           # Upload/download uçları
│  │  ├─ analyze.py         # LLM analiz uçları
│  ├─ services/
│  │  ├─ comtrade_io.py     # COMTRADE okuma/dönüştürme
│  │  ├─ features.py        # Sinyal işleme, öznitelikler
│  │  ├─ llm_client.py      # Ollama LLM istemcisi
│  ├─ models/               # Pydantic modelleri
│  └─ utils/                # yardımcılar (log, config)
├─ ui/                      # Web arayüzü (React/Streamlit)
├─ data/
│  ├─ raw/                  # Yüklenen COMTRADE/ham dosyalar
│  └─ processed/            # Üretilen CSV/ara çıktılar
├─ scripts/
│  ├─ comtrade_to_csv.py    # Komut satırı dönüştürücü
│  └─ demo_analyze.py       # Örnek uçtan uca analiz
├─ .env.example
├─ requirements.txt
└─ README.md

COMTRADE Dönüşümü

Proje, COMTRADE 1991/1999/2013 varyantlarını okumak için Python comtrade kütüphanesini (veya eşdeğerini) kullanır.
Girdi: .cfg + .dat (opsiyonel .hdr, .inf)
Çıktı: processed/<oturum>/<dosya>.csv

Script ile
python scripts/comtrade_to_csv.py \
  --cfg data/raw/OLAY_001.CFG \
  --dat data/raw/OLAY_001.DAT \
  --out data/processed/OLAY_001.csv


scripts/comtrade_to_csv.py örnek iskeleti:

# scripts/comtrade_to_csv.py
import argparse
import pandas as pd
from comtrade import Comtrade  # pip install comtrade
from pathlib import Path

def convert(cfg_path: str, dat_path: str, out_path: str):
    rec = Comtrade()
    rec.load(cfg_path, dat_path)

    # Zaman ekseni (saniye cinsinden)
    t = pd.Series(rec.time, name="time_s")

    # Analog ve dijital kanallar
    analog_cols = {f"a{i+1}_{rec.analog[i].name}": rec.analog[i].values for i in range(rec.analog_count)}
    digital_cols = {f"d{i+1}_{rec.status[i].name}": rec.status[i].values for i in range(rec.status_count)}

    df = pd.DataFrame({**{"time_s": t}, **analog_cols, **digital_cols})
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--cfg", required=True)
    p.add_argument("--dat", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    convert(args.cfg, args.dat, args.out)


İpuçları

Kanal isimlerini .cfg içinden alıp başlıklara ekliyoruz (okunurluk artar).

Çok büyük kayıtlarda bellek tasarrufu için chunksize ve parquet düşünülebilir.

LLM Analiz Akışı

Ön-işleme:

CSV’ye çevrilen sinyallerde zaman penceresi seçimi (ör. olaydan ±N ms)

Filtreleme/normalize (opsiyonel)

Öznitelik çıkarımı (pik akımlar, RMS, toplam süre, koruma tetik anları vb.)

İstem (Prompt) Tasarımı:

Kısa ama mühendislik terminolojisine uygun içerik

“Arıza senaryosu / olasılık / kanıt / öneri” başlıklarıyla yapılandırılmış yanıt

Ör. (Türkçe profesyonel format)

Görev: SCADA olay analiz özeti üret.
Çıktı biçimi:
- Olay Özeti:
- Olası Arıza Tipi ve Olasılık (%):
- Kanıt/İndikasyonlar:
- Öneriler (İşletme/Bakım):
- Varsayımlar/Sınırlar:


Yerel LLM Çağrısı (Ollama):

HTTP API ile POST /api/generate (Ollama varsayılanı: http://localhost:11434)

model, prompt, options (max tokens, temperature) parametreleri

Sonuç Sunumu:

UI’da metin paneli + kanıtları işaretleyen grafik/tablolar

Örnek API Uçları (Backend)

POST /api/upload — dosya yükleme (COMTRADE veya CSV)

POST /api/convert — COMTRADE → CSV dönüştür

POST /api/analyze — CSV üstünde LLM analizi

GET /api/result/{id} — sonuç/rapor çekme

FastAPI kullanıyorsan, app/routers/analyze.py içinde LLM çağrısı yapan endpoint’i konumlandırabilirsin.

Yapılandırma

.env.example dosyasını .env olarak kopyala ve doldur:

LLM_MODEL=llama3
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
DATA_DIR=./data
RESULTS_DIR=./data/processed
MAX_FILE_SIZE_MB=200


Uygulama açılışında .env otomatik yükleniyorsa (örn. python-dotenv), değerler servisler tarafından kullanılır.

Geliştirme ve Test

Birim testleri: pytest ile app/services ve scripts testleri

Numune veri: data/samples/ içine anonim örnek COMTRADE dosyaları ekleyip CI’da doğrulama

Stil: ruff, black ile kod kalitesi

Yol Haritası

 Gelişmiş özellik çıkarımı (frekans, harmonikler, RMS pencereleri)

 Otomatik olay penceresi tespiti (threshold/ML)

 Çoklu model desteği (seçilebilir LLM + prompt preset’leri)

 Rapor dışa aktarma (PDF/Docx)

 Kullanıcı/rol yönetimi

Güvenlik ve Veri Gizliliği

Dosyalar yerel diskte kalır, dış servislere gönderilmez.

Loglarda hassas veri maskelemesi önerilir.

Opsiyonel şifreli depolama ve erişim denetimi eklenebilir.

Katkıda Bulunma

Fork’la

Yeni dal aç (feat/…, fix/…)

Testleri çalıştır

PR aç

Lisans

Bu depo için uygun lisansı seçip bu bölümü güncelle (örn. MIT).

SSS

S: İnternetsiz çalışır mı?
Evet. Ollama + model lokalde olduğu sürece çalışır.

S: COMTRADE dosyaları farklı sürümlerdeyse?
comtrade kütüphanesi yaygın sürümleri destekler. Sorunlu dosyalarda scripts/comtrade_to_csv.py içindeki okuma mantığına “tarihçe/sürüm” kontrolleri eklenebilir.

S: GPU zorunlu mu?
Hayır; CPU ile de çalışır. Ancak büyük modeller ve uzun kayıtlar için GPU ciddi hız kazandırır.
