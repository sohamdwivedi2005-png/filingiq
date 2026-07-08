# Deploying FilingIQ (free public URL)

Recommended host: **Hugging Face Spaces (Docker SDK)** — free, ~16 GB RAM (enough
for the embeddings + vector index), and supports secrets for the Groq key. Groq
runs the LLM, so the host needs **no GPU**.

## Steps

1. **Create a free Hugging Face account** at https://huggingface.co.

2. **Create a new Space**: New → Space → **SDK: Docker** → blank template.

3. **Tell the Space it's a Docker app** — its `README.md` needs this frontmatter
   at the very top (the app listens on 7860):

   ```
   ---
   title: FilingIQ
   emoji: 📊
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```

4. **Add the Groq key as a secret**: Space → Settings → *Variables and secrets* →
   New secret → name `GROQ_API_KEY`, value = your key.

5. **Push this repo to the Space's git remote**:

   ```bash
   git remote add space https://huggingface.co/spaces/<user>/<space-name>
   git push space main
   ```

6. The Space builds the Docker image (this **bakes the vector index**, so the first
   build takes a few minutes), then serves the app at your public URL.

## Notes

- The index is baked at build time for `AAPL MSFT NVDA GOOGL AMZN`. To change the
  covered companies, edit the `build_index.py` line in the `Dockerfile` and rebuild.
- No secrets are committed — `GROQ_API_KEY` lives only in the Space secret store.
- Alternative hosts (Render/Railway/Fly) work with the same `Dockerfile`, but their
  free tiers have less RAM and may need a smaller index.
