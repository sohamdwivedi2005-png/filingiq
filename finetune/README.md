# FilingIQ — fine-tuning a specialised model

Goal: distill Groq-70B's grounded-answer behaviour into a small open model, then
prove it's competitive using the same eval harness. Your laptop (4 GB VRAM) can't
train — steps 2 use a **free** Colab/Kaggle T4 GPU.

## 1. Generate training data (local — uses Groq)

```bash
uv run python scripts/gen_dataset.py -n 300
```

Teacher (Groq 70B) writes investor questions over indexed 10-K chunks, FilingIQ
retrieves excerpts, teacher answers (grounded + cited). Output: `finetune/train.jsonl`
and `val.jsonl` in chat format. Run in batches if you hit Groq's free rate limits;
a few hundred examples is enough for a demonstrable fine-tune. Commit the JSONL so
Colab can pull it via `git clone`.

## 2. Train on a free GPU (Colab / Kaggle)

Open Colab (Runtime → T4 GPU) and run the one-cell setup at the top of
[`train_qlora.py`](train_qlora.py). It QLoRA-fine-tunes `Qwen2.5-3B-Instruct` and
exports a LoRA adapter **and** a `q4_k_m` GGUF. Download the GGUF folder.

## 3. Serve locally via Ollama (free) and plug into FilingIQ

```bash
# from the downloaded GGUF folder
ollama create filingiq-qwen3b -f Modelfile        # Unsloth writes a Modelfile
ollama run filingiq-qwen3b "hello"                # smoke test
```

The `ollama` provider is already wired into the adapter, so no code change is needed.

## 4. Prove it with the eval harness (the payoff)

Run the *same* suites against the fine-tuned model and compare to Groq:

```bash
# baseline (Groq)
uv run python scripts/run_evals.py

# fine-tuned (local Ollama)
LLM_PROVIDER=ollama LLM_MODEL=filingiq-qwen3b uv run python scripts/run_evals.py
```

Report numeric accuracy / verified-rate and answer quality side by side. That
comparison — "my 3B specialised model matches the 70B on FilingIQ's task at a
fraction of the cost" — is the headline result.

## Notes / caveats

- Serving the custom model **for free in the deployed public app** is the hard part
  (the local Ollama path only serves your machine). Options: run the GGUF in a
  Hugging Face **ZeroGPU** Space, or keep the public demo on Groq and showcase the
  fine-tune + eval comparison in the README.
- `train_qlora.py` is written for a Colab T4; library versions move fast, so pin if
  a call signature drifts.
