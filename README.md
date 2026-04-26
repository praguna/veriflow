# Veriflow

Multi-modal content verification. Feed it text, images, PDFs, or URLs — it extracts claims, checks them against the web and image forensics, and tells you what doesn't add up.

Not a fact-checker that says "true" or "false." It shows you *where the signals disagree* — the caption says Istanbul but the GPS says Kahramanmaraş, the date says 2026 but the EXIF says 2023.

## How it works

Two LLM calls, everything else runs in parallel with no LLM:

1. **Decomposer** — breaks input into atomic claims, tags by modality, outputs a logical formula connecting them
2. **Verifiers** (parallel, no LLM) — web search, EXIF metadata, image forensics (FFT, ELA, noise), reverse image search
3. **Aggregator** — reasons over all signals, produces a trust profile

Based on [SAFE](https://arxiv.org/abs/2403.18802) (DeepMind) and [TRUST Agents](https://arxiv.org/abs/2604.12184) (Bulusu et al.).

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env   # fill in your keys
```

You need:
- `GEMINI_API_KEY` — [get one here](https://aistudio.google.com/apikey) (free)
- `TAVILY_API_KEY` — [get one here](https://tavily.com) (free tier: 1000/month)
- `SERPAPI_KEY` — optional, only for `--deep` mode (reverse image search)
- `IMGBB_API_KEY` — optional, required for `--deep` mode alongside `SERPAPI_KEY`; [get one here](https://api.imgbb.com/) (free)

## Usage

```bash
python -m veriflow --text "The Great Wall is visible from the Moon"
python -m veriflow --image photo.jpg --text "Earthquake in Istanbul"
python -m veriflow --pdf document.pdf
python -m veriflow --url "https://example.com/article"
python -m veriflow --image photo.jpg --deep    # adds reverse image search
python -m veriflow --text "claim" --json        # raw JSON output
```

## MCP Server (Claude Desktop)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "veriflow": {
      "command": "python",
      "args": ["-m", "veriflow.mcp_server"],
      "cwd": "/path/to/veriflow",
      "env": {
        "GEMINI_API_KEY": "...",
        "TAVILY_API_KEY": "...",
        "SERPAPI_KEY": "...",
        "IMGBB_API_KEY": "..."
      }
    }
  }
}
```

Exposes three tools: `veriflow_quick` (~6-8s), `veriflow_deep` (~10-15s), `veriflow_extract` (claims only).

## Example from chat

[veriflow_deep on a recycled earthquake image](https://claude.ai/share/ed86d19a-d804-49e6-ad26-8572cc6a6a6b) — full MCP flow in Claude Desktop: tool call, trust profile, provenance hits, and red flags.

## Example output

```
VERIFLOW TRUST PROFILE (QUICK)
============================================================
Verdict:    LIKELY_MANIPULATED
Confidence: 15%

Claims (3):
  [x] Earthquake hit Istanbul
      refuted (90%) — No credible reports found
  [x] Event happened April 2026
      refuted (95%) — EXIF date: 2023-02-06
  [+] Photo shows destroyed building
      supported (85%) — Consistent with earthquake damage

Red Flags:
  ! EXIF date (Feb 2023) contradicts claimed date
  ! GPS: Kahramanmaraş, not Istanbul
  ! Image found in Reuters 2023 earthquake coverage
```

## Tests

```bash
pytest tests/ -v    # all APIs mocked, no keys needed
```

## Extending

New input type? Add a connector in `connectors/` that returns `{"text": ..., "images": [...]}`. Pipeline handles the rest.

New verification signal? Add a verifier in `verifiers/` and wire it into `pipeline.py:_collect_signals()`.
