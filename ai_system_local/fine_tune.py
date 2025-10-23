import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig
from trl import SFTTrainer
import os

# --- Model ve Veri Seti Ayarları ---
base_model_name = "meta-llama/Llama-3.2-3B-Instruct"
new_model_name = "enerjisa-scada-analyzer-v1"
dataset_path = "fault_analysis_dataset.jsonl"

# --- Veri Setini Yükleme ---
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"'{dataset_path}' dosyası bulunamadı. Lütfen proje klasöründe olduğundan emin olun.")
dataset = load_dataset("json", data_files=dataset_path, split="train")

# --- Model Quantization ---
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=False,
)

# --- Temel Modeli Yükleme ---
print(f"'{base_model_name}' modeli yükleniyor...")
model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)
model.config.use_cache = False

# --- Tokenizer'ı Yükleme ---
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# --- LoRA Konfigürasyonu ---
peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=32,
    bias="none",
    task_type="CAUSAL_LM",
)

# --- Eğitim Argümanları ---
training_arguments = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    optim="paged_adamw_32bit",
    save_steps=50,
    logging_steps=10,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=False,
    bf16=True,
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="constant",
)

# --- Veri Setini Formatlama (En Güncel Yöntem) ---
def format_dataset_entry(entry):
    return {"text": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n### Talimat:\n{entry['instruction']}\n\n### Veri Özeti:\n{entry['input']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{entry['output']}<|eot_id|>"}

formatted_dataset = dataset.map(format_dataset_entry)

# --- Trainer'ı Oluşturma (En Güncel Kütüphanelerle Uyumlu Argümanlar) ---
trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=formatted_dataset,
    peft_config=peft_config,
    args=training_arguments,
)

# --- Eğitimi Başlatma ---
print("\n--- Model Eğitimi Başlatılıyor ---")
trainer.train()
print("--- Model Eğitimi Tamamlandı ---")

# --- Eğitilmiş Modeli Kaydetme ---
print(f"Eğitilmiş model '{new_model_name}' klasörüne kaydediliyor...")
trainer.model.save_pretrained(new_model_name)

print("\n\n✅ EĞİTİM TAMAMLANDI!")