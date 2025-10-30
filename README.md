---
title: SnapDisclosure
emoji: 🌍
colorFrom: pink
colorTo: pink
sdk: docker
pinned: false
short_description: SnapDisclosure - Inspect Disclosure Documents In Snap
---

## Deployment Prep Notes

- Backend reads the port from the `PORT` environment variable (defaults to `7860`) for Hugging Face Spaces compatibility.
- A trimmed dependency list lives in `backend/requirements.txt` so the Space installs only what the API needs.
- Populate `OPENAI_API_KEY` through each host's secret manager; the sample `.env` files now contain placeholders only.
- Point the frontend environment variables (`VITE_API_BASE`, `VITE_BACKEND_URL`) at the final Space URL when it is available.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
