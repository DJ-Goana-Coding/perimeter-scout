---
title: Perimeter Scout
emoji: 📡
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

This repository deploys to the Hugging Face Space `DJ-Goanna-Coding/perimeter-scout` as a Docker Space.

The Space container starts the FastAPI backend on `127.0.0.1:8000` for the bundled Streamlit UI, then serves Streamlit on port `7860` for Hugging Face.

`.github/workflows/hf-sync.yml` force-pushes `main` to the Space because starter/template Spaces can begin with unrelated Git history. That force sync makes this repository's `main` branch the authoritative Space contents.
