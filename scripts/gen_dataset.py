"""Generate a synthetic SFT dataset for fine-tuning (distillation from Groq 70B).

For each sampled 10-K chunk: (1) the teacher writes an investor question the chunk
can answer, (2) FilingIQ retrieves fresh excerpts, (3) the teacher answers, grounded
and cited. Each example is stored in chat format matching inference, so a small
student model learns FilingIQ's exact task.

    uv run python scripts/gen_dataset.py -n 60
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import httpx  # noqa: E402
import lancedb  # noqa: E402

from filingiq.llm import Message, get_llm  # noqa: E402
from filingiq.llm.groq import MissingAPIKey  # noqa: E402
from filingiq.rag.answer import SYSTEM, _format_context  # noqa: E402
from filingiq.rag.index import DEFAULT_LANCE, TABLE  # noqa: E402
from filingiq.rag.retrieve import search  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "finetune"

Q_PROMPT = (
    "You are building a training set of investor questions about SEC filings. "
    "Given this excerpt from a company's 10-K, write ONE clear, specific question "
    "an investor could ask that is answerable from it. Return only the question.\n\n"
    "Excerpt:\n{chunk}"
)


def _complete(llm, messages, retries: int = 5) -> str:
    for i in range(retries):
        try:
            return llm.complete(messages)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and i < retries - 1:
                time.sleep(2 * (i + 1))  # backoff on rate limit
                continue
            raise
    raise RuntimeError("unreachable")


def load_chunks() -> list[dict]:
    tbl = lancedb.connect(DEFAULT_LANCE).open_table(TABLE)
    return tbl.to_pandas().to_dict("records")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--val-frac", type=float, default=0.15)
    args = ap.parse_args()

    try:
        llm = get_llm()
    except MissingAPIKey as e:
        print(e)
        sys.exit(1)

    rows = [r for r in load_chunks() if len(r["text"]) > 400]
    random.seed(args.seed)
    random.shuffle(rows)
    rows = rows[: args.n]

    examples: list[dict] = []
    for i, r in enumerate(rows, 1):
        try:
            q = _complete(
                llm, [Message("user", Q_PROMPT.format(chunk=r["text"][:1600]))]
            ).strip().strip('"')
            ctx = search(q, k=6, ticker=r["ticker"], cross_encoder=False)
            user = (
                f"Question: {q}\n\nExcerpts:\n{_format_context(ctx)}\n\n"
                "Answer the question using only these excerpts, with [n] citations:"
            )
            answer = _complete(llm, [Message("system", SYSTEM), Message("user", user)])
        except Exception as e:  # noqa: BLE001
            print(f"  skip {i}: {e}")
            continue
        examples.append(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user},
                    {"role": "assistant", "content": answer},
                ]
            }
        )
        if i % 5 == 0:
            print(f"  {i}/{len(rows)} generated")

    random.shuffle(examples)
    n_val = int(len(examples) * args.val_frac)
    splits = {"val.jsonl": examples[:n_val], "train.jsonl": examples[n_val:]}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in splits.items():
        with (OUT_DIR / name).open("w", encoding="utf-8") as f:
            for ex in data:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Wrote {len(splits['train.jsonl'])} train + {len(splits['val.jsonl'])} val "
          f"-> {OUT_DIR}")


if __name__ == "__main__":
    main()
