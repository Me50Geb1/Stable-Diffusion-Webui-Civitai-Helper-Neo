# Changelog

## Forge Neo

### 1.13.0 - 2026-09-01

#### Added / Changed

- Added a shared `404 or ORIGINAL` LoRA card preview for definite Civitai hash or model-version 404 responses
- Persisted 404 results in `civitai_preview_status.json`
- Added a local read-only preview-status endpoint so persisted results work immediately after restart
- Kept real/manual previews at the highest priority
- Kept transient API failures and preview download failures as the standard NO PREVIEW state
- Added compatibility with automatic card refresh from Forge Extra Networks Pagination

### 2026-09-01

Initial Forge Neo compatibility release.

### Added / Changed

- Added compatibility with sd-webui-forge-neo
- Added support for multiple Checkpoint directories
- Added support for multiple LoRA directories
- Adjusted Embeddings path handling for Forge Neo
- Adjusted Hypernetwork path compatibility
- Updated Gradio-related UI handling
- Updated Extra Networks refresh behavior
- Added compatibility with `civitai.red`
- Kept `image.civitai.com` for preview image delivery
- Added retry handling for failed preview downloads
- Added temporary `.part` file handling for safer image downloads
- Added detection and replacement of invalid preview images
- Improved scanning across multiple model directories

### Notes

This changelog describes changes specific to the Forge Neo compatibility branch.

For the original project history, refer to the upstream repository.
