import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

# --- AYARLAR ---
base_model_name = "meta-llama/Llama-3.2-3B-Instruct"
adapter_path = "./enerjisa-scada-analyzer-v1"
merged_model_path = "./enerjisa-scada-analyzer-v1-merged"

# --- BİRLEŞTİRME İŞLEMİ ---
print(f"Temel model yükleniyor: {base_model_name}")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)

print(f"Adaptör yükleniyor: {adapter_path}")

# HATA ÇÖZÜMÜ: 'offload_folder' parametresini ekliyoruz.
# Bu, belleğe sığmayan parçaların geçici olarak nereye yazılacağını belirtir.
offload_directory = "./offload_temp"
os.makedirs(offload_directory, exist_ok=True) # Klasör yoksa oluştur

# Temel modelin üzerine adaptörü (eğitilmiş katmanları) yüklüyoruz
merged_model = PeftModel.from_pretrained(
    base_model,
    adapter_path,
    offload_folder=offload_directory # Kritik ekleme burada
)

print("Modeller birleştiriliyor (merge and unload)...")
# Adaptörü temel modelle kalıcı olarak birleştiriyoruz
merged_model = merged_model.merge_and_unload()

print(f"Birleştirilmiş model '{merged_model_path}' klasörüne kaydediliyor...")
# Artık tek parça olan yeni modeli ve tokenizer'ı kaydediyoruz
merged_model.save_pretrained(merged_model_path)
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
tokenizer.save_pretrained(merged_model_path)

print("\n✅ Birleştirme tamamlandı!")
print(f"Nihai modelin artık '{merged_model_path}' klasöründe kullanıma hazır.")