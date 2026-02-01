# arXiv Daily Paper Fetcher for KIGLAND

Automated pipeline for tracking AI/ML papers from arXiv relevant to KIGLAND research areas.

## Features

- **Multi-category support**: Fetches from cs.AI, cs.CV, cs.LG, cs.RO
- **Rate limiting**: Respects arXiv's 3-second delay between requests
- **Smart filtering**: Relevance scoring based on KIGLAND focus areas
- **Structured output**: JSON data + Markdown reports
- **Error handling**: Retry logic with exponential backoff
- **Configurable**: CLI arguments for date, test mode, thresholds

## Usage

### Quick Start

```bash
# Fetch yesterday's papers
python scripts/arxiv-daily-fetch.py

# Fetch specific date
python scripts/arxiv-daily-fetch.py --date 2025-01-15

# Test mode (fetches only 10 papers)
python scripts/arxiv-daily-fetch.py --test

# Verbose logging
python scripts/arxiv-daily-fetch.py -v
```

### Command Line Options

```
--date DATE        Date to fetch (YYYY-MM-DD format, default: yesterday)
--test             Run in test mode (fetch only 10 papers)
--min-score FLOAT  Minimum relevance score (default: 1.0)
--max-papers INT   Maximum papers to fetch
--output-dir PATH  Output directory path
-v, --verbose      Enable verbose logging
```

## Output

Files are saved to `research/intelligence/arxiv-daily/`:

- `arxiv-YYYY-MM-DD.json` - Full paper data with metadata
- `arxiv-YYYY-MM-DD.md` - Human-readable markdown report

## Relevance Scoring

Papers are scored based on keyword matches in KIGLAND focus areas:

| Area | Keywords |
|------|----------|
| AI | neural network, transformer, llm, agent, multi-agent, etc. |
| Vision | computer vision, image generation, 3d reconstruction, etc. |
| Agents | autonomous agent, embodied ai, task planning, etc. |
| Manufacturing | 3d printing, digital twin, quality control, etc. |
| Kigurumi | cosplay, mask detection, motion capture, avatar, etc. |

Scoring:
- Title match: +3 points per keyword
- Abstract match: +1 point per keyword
- Target category bonus: ×1.2 multiplier

## Rate Limiting

The script enforces arXiv's rate limits:
- 3-second delay between requests
- Single-threaded (no parallel requests)
- Exponential backoff on errors

## API Specification

See: `research/arxiv-api-spec.md`

## License

This tool respects arXiv's Terms of Use. Results include the required acknowledgment:
> Thank you to arXiv for use of its open access interoperability.
