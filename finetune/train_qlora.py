"""QLoRA fine-tune of a small model on FilingIQ's synthetic data — run on a free
Colab/Kaggle T4 GPU (your 4 GB-VRAM laptop can't train this).

Colab setup (one cell):
    !pip install -q "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
    !pip install -q --no-deps trl peft accelerate bitsandbytes datasets
    !git clone https://github.com/sohamdwivedi2005-png/filingiq.git
    %cd filingiq
    !python finetune/train_qlora.py

Outputs a LoRA adapter and a GGUF you can serve locally with Ollama.
"""

from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
from unsloth import FastLanguageModel

BASE_MODEL = "unsloth/Qwen2.5-3B-Instruct"   # open (Apache-2.0), fits a free T4
MAX_SEQ = 2048
OUT = "filingiq-qwen3b-lora"

# 1. Load base model in 4-bit + attach LoRA adapters.
model, tok = FastLanguageModel.from_pretrained(
    BASE_MODEL, max_seq_length=MAX_SEQ, load_in_4bit=True
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    lora_dropout=0.0,
    bias="none",
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    use_gradient_checkpointing="unsloth",
)

# 2. Data: our chat-format JSONL -> a single text field via the chat template.
ds = load_dataset(
    "json",
    data_files={"train": "finetune/train.jsonl", "validation": "finetune/val.jsonl"},
)


def to_text(ex):
    return {"text": tok.apply_chat_template(ex["messages"], tokenize=False)}


ds = ds.map(to_text, remove_columns=ds["train"].column_names)

# 3. Train.
trainer = SFTTrainer(
    model=model,
    tokenizer=tok,
    train_dataset=ds["train"],
    eval_dataset=ds["validation"],
    args=SFTConfig(
        output_dir=OUT,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        bf16=True,
        packing=False,
    ),
)
trainer.train()

# 4. Save the LoRA adapter, and a GGUF for local serving via Ollama.
model.save_pretrained(OUT)
tok.save_pretrained(OUT)
model.save_pretrained_gguf(OUT + "-gguf", tok, quantization_method="q4_k_m")
print(f"Done. LoRA -> {OUT} ; GGUF -> {OUT}-gguf")
