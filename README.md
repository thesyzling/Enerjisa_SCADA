# Enerjisa_SCADA

Yerel LLM tabanlı **SCADA arıza analizi** arayüzü.  
Bu proje, **COMTRADE formatındaki** olay dosyalarını otomatik olarak **CSV’ye dönüştürür**, sinyalleri görselleştirir ve **yerel LLM** kullanarak mühendislik odaklı rapor üretir.

---

## ✨ Özellikler

- **Yerel LLM ile analiz** (Ollama üzerinden)  
  - Olay özeti  
  - Olası arıza tipi & olasılık  
  - Kanıt / göstergeler  
  - İşletme & bakım önerileri  

- **COMTRADE → CSV dönüşümü**  
  - `.cfg + .dat` dosyalarından zaman-serisi CSV üretir  
  - Kanal isimlerini ve metaveriyi korur  

- **Web arayüzü**  
  - Dosya yükleme (COMTRADE veya CSV)  
  - Trend grafikleri (akım/gerilim, dijital sinyaller)  
  - LLM analiz çıktısı paneli  

- **Tamamen lokal çalışma**  
  - İnternete ihtiyaç duymaz  
  - Veriler dışarı çıkmaz  

---

## 📸 Arayüz Görselleri

>![Demo](Resim1.png)
>![Arayuz2](Resim3.png)




---

## 🛠 Kurulum

### Gereksinimler
- Python 3.10+
- Ollama (LLM için) → [https://ollama.com](https://ollama.com)
- (Opsiyonel) NVIDIA GPU

### Adımlar

```bash
🚀 Özellikler

SCADA Veri Analizi:
Ölçüm verilerinden yapay zekâ tabanlı çıkarımlar ve hata tespitleri.

Yerel LLM Entegrasyonu (Ollama):
SCADA verilerini doğal dilde açıklama, raporlama ve özetleme.

React Arayüz:
Son kullanıcıya sade, anlaşılır ve görsel olarak zengin bir dashboard.

Grafiksel Görselleştirme:
Zaman serisi verilerinin çizelgeler ve grafiklerle sunulması.

Genişletilebilir Yapı:
Yeni sensörler, ek veri kaynakları veya model güncellemeleri kolayca eklenebilir.

🛠 Kullanılan Teknolojiler

Backend: Python (pandas, scikit-learn, vb.)

Yapay Zekâ: Ollama (Yerel LLM entegrasyonu)

Frontend: React

Veri Kaynakları: SCADA CSV dosyaları

📂 Proje Yapısı
Enerjisa_SCADA/
│
├── backend/            # Python tabanlı analiz kodları
├── frontend/           # React arayüzü
├── models/             # Yapay zekâ modelleri (Ollama, ML, vb.)
├── data/               # Örnek SCADA verileri (CSV)
├── outputs/            # Grafikler, rapor çıktıları
├── Resim1.gif          # Proje arayüzünden örnek görsel
└── README.md           # Bu dosya

⚙️ Kurulum
1. Depoyu klonla
git clone https://github.com/thesyzling/Enerjisa_SCADA.git
cd Enerjisa_SCADA

2. Backend (Python) ortamını kur
cd backend
pip install -r requirements.txt

3. Frontend (React) ortamını kur
cd frontend
npm install
npm start

4. Ollama’yı kur ve çalıştır
ollama run llama3

▶️ Çalıştırma

Backend servisini başlat (Python analiz).

Frontend’i çalıştır (React arayüz).

SCADA verilerini data/ klasörüne yerleştir.

Tarayıcıdan http://localhost:3000 adresine git.
