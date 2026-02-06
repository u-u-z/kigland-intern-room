# arXiv Intelligence Pipeline Design

> **Issue**: #9  
> **Status**: Design Complete  
> **Author**: RemiBot  
> **Date**: 2026-02-06

---

## Executive Summary

This document describes the complete architecture for an automated arXiv paper tracking system designed specifically for KIGLAND's strategic research needs. The pipeline fetches daily submissions from target categories, scores papers for business relevance using LLM-based evaluation, and generates actionable intelligence digests.

**Target Outcome**: < 10 minutes to consume daily digest, > 80% relevance to KIGLAND business context.

---

## 1. Technical Architecture

### 1.1 System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Source   │    │  Processing     │    │   Output        │
│   (arXiv API)   │ -> │  (Scoring)      │ -> │   (Digest)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
   Daily fetch at          LLM relevance         Markdown digest
   08:00 CST               scoring              + JSON database
```

### 1.2 Component Breakdown

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Fetcher** | Query arXiv API for new papers | Python `requests` + `feedparser` |
| **Filter** | Deduplicate and preliminary filtering | Python `sqlite3` |
| **Scorer** | Business relevance scoring | LLM API (OpenAI/Anthropic) |
| **Summarizer** | Generate human-readable summaries | LLM API with structured output |
| **Storage** | Persist paper metadata and scores | JSONL + SQLite |
| **Publisher** | Generate daily digest markdown | Python `jinja2` templates |

### 1.3 Data Flow

```
1. FETCH: Query arXiv API for each category (cs.AI, cs.CV, cs.LG, cs.RO)
         ↓
2. PARSE: Extract metadata (title, authors, abstract, categories, links)
         ↓
3. DEDUP: Check against existing database (by arXiv ID)
         ↓
4. FILTER: Pre-filter by keyword presence (optional)
         ↓
5. SCORE: LLM evaluates business relevance (1-10 scale)
         ↓
6. SUMMARIZE: Generate problem/approach/significance for high-scoring papers
         ↓
7. STORE: Save to database and append to JSONL
         ↓
8. PUBLISH: Generate markdown digest for threshold-scored papers
```

---

## 2. arXiv API Integration

### 2.1 API Endpoint

**Base URL**: `http://export.arxiv.org/api/query`

The arXiv API provides an Atom feed interface for querying papers. It supports:
- Search queries with Boolean logic
- Category filtering
- Date range filtering
- Pagination
- Sorting by submission date or relevance

### 2.2 Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search_query` | Search expression | `cat:cs.AI` |
| `start` | Offset for pagination | `0` |
| `max_results` | Results per query (max 30000) | `100` |
| `sortBy` | Sort field | `submittedDate` or `relevance` |
| `sortOrder` | Sort direction | `descending` or `ascending` |
| `id_list` | Specific arXiv IDs | `2401.001,2401.002` |

### 2.3 Sample API Calls

#### Fetch Latest Papers from cs.AI
```bash
curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending"
```

#### Fetch Multiple Categories (OR logic)
```bash
curl "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.RO&start=0&max_results=100&sortBy=submittedDate&sortOrder=descending"
```

#### Fetch Papers from Last 24 Hours
```bash
# Using submittedDate range (requires date math in client)
# Note: arXiv API doesn't support direct date filtering in query
# Client must filter by `published` field in response
```

#### Python Implementation
```python
import requests
import feedparser
from datetime import datetime, timedelta

def fetch_arxiv_papers(categories, max_results=100):
    """
    Fetch papers from arXiv API for specified categories.
    
    Args:
        categories: List of arXiv category codes (e.g., ['cs.AI', 'cs.CV'])
        max_results: Maximum papers to fetch per category
    
    Returns:
        List of parsed paper dictionaries
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # Build OR-separated category query
    cat_query = "+OR+".join([f"cat:{cat}" for cat in categories])
    
    params = {
        "search_query": cat_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    
    # Parse Atom feed
    feed = feedparser.parse(response.content)
    
    papers = []
    for entry in feed.entries:
        paper = {
            "arxiv_id": entry.id.split("/")[-1],  # Extract ID from URL
            "title": entry.title,
            "authors": [author.name for author in entry.get("authors", [])],
            "summary": entry.summary,
            "published": entry.published,
            "updated": entry.get("updated", entry.published),
            "primary_category": entry.get("arxiv_primary_category", {}).get("term", ""),
            "categories": [tag.term for tag in entry.get("tags", [])],
            "pdf_url": next((link.href for link in entry.links if link.get("type") == "application/pdf"), None),
            "abs_url": entry.link,
            "doi": entry.get("arxiv_doi", None),
            "comment": entry.get("arxiv_comment", None),
        }
        papers.append(paper)
    
    return papers

# Usage
categories = ["cs.AI", "cs.CV", "cs.LG", "cs.RO"]
papers = fetch_arxiv_papers(categories, max_results=100)
```

### 2.4 Response Format (Atom Feed)

The API returns an Atom XML feed with the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>arXiv Query: search_query=cat:cs.AI...</title>
  <updated>2026-02-06T19:49:30Z</updated>
  <opensearch:totalResults>161694</opensearch:totalResults>
  
  <entry>
    <id>http://arxiv.org/abs/2602.06043v1</id>
    <title>Shared LoRA Subspaces for almost Strict Continual Learning</title>
    <updated>2026-02-05T18:59:58Z</updated>
    <published>2026-02-05T18:59:58Z</published>
    <summary>Paper abstract here...</summary>
    <arxiv:primary_category term="cs.LG"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <link href="https://arxiv.org/pdf/2602.06043v1" rel="related" type="application/pdf"/>
  </entry>
</feed>
```

### 2.5 Rate Limiting & Best Practices

- **Rate Limit**: arXiv recommends no more than 1 request per 3 seconds
- **Retry Logic**: Implement exponential backoff for 503/504 errors
- **Pagination**: Use `start` parameter to paginate through large result sets
- **Caching**: Cache responses for at least 1 hour to respect server resources
- **User-Agent**: Set a descriptive User-Agent header identifying your bot

---

## 3. Categories to Track

### 3.1 Primary Categories

Based on KIGLAND's strategic research agenda, we track these arXiv categories:

| Category | Description | Relevance to KIGLAND |
|----------|-------------|---------------------|
| **cs.AI** | Artificial Intelligence | Core - agent systems, reasoning, planning |
| **cs.CV** | Computer Vision | Core - visual understanding, generation, 3D |
| **cs.LG** | Machine Learning | Core - training methods, efficiency, robustness |
| **cs.RO** | Robotics | Strategic - physical AI, manipulation, autonomy |

### 3.2 Cross-Category Coverage

Many relevant papers appear in multiple categories. The pipeline should:
1. Use OR query to fetch papers matching ANY target category
2. Deduplicate by arXiv ID
3. Track primary category and all secondary categories
4. Consider papers with cross-category presence as potentially higher relevance

### 3.3 Expected Volume

| Category | Daily Submissions (avg) | Monthly Volume |
|----------|------------------------|----------------|
| cs.AI | ~150-200 | ~4,500-6,000 |
| cs.CV | ~100-150 | ~3,000-4,500 |
| cs.LG | ~200-250 | ~6,000-7,500 |
| cs.RO | ~50-80 | ~1,500-2,400 |
| **Total** | **~500-680** | **~15,000-20,400** |

---

## 4. Relevance Scoring Prompt Design

### 4.1 Scoring Philosophy

The relevance score must answer: *"How actionable is this paper for KIGLAND's business in the next 6-12 months?"*

Scoring criteria (1-10 scale):
- **10**: Immediate product impact, clear implementation path
- **7-9**: Strategic relevance, monitor for maturation
- **4-6**: Interesting but not directly applicable
- **1-3**: Academic curiosity, no business relevance

### 4.2 Relevance Scoring Prompt Template

```markdown
You are a strategic research analyst for KIGLAND, a company building AI-powered 
kigurumi (anime mask) experiences and related technologies. 

Your task: Score the following arXiv paper for business relevance to KIGLAND.

## KIGLAND Strategic Context

**Core Business Areas:**
1. AI-powered kigurumi face generation and customization
2. Computer vision for costume/character recognition
3. Agent systems for creative workflows
4. 3D generation for virtual/physical assets
5. Consumer-facing AI products with real-time requirements

**Key Technical Interests:**
- Visual-Language Models (VLM) capabilities
- Efficient model serving and edge deployment
- 3D generation from 2D images
- Multi-modal AI systems
- AI agent workflows for creative tasks
- Production AI robustness and reliability
- Manufacturing automation and C2M pipeline

**Investment Context:**
- MiraclePlus portfolio company (Y Combinator China)
- Focus on product-ready technology, not academic research
- Need to identify competitive advantages and threats

## Paper to Evaluate

**Title**: {{title}}
**Categories**: {{categories}}
**Authors**: {{authors}}
**Abstract**: 
{{abstract}}

## Scoring Instructions

Rate the paper 1-10 based on:

**Score 10 (Critical)**: 
- Directly enables a KIGLAND product feature
- Clear implementation path within 3 months
- Addresses current technical blocker

**Score 7-9 (High)**:
- Strategic relevance to core business area
- Potential product impact within 6-12 months
- Worth deep technical review

**Score 4-6 (Medium)**:
- Interesting technical approach
- Possible future relevance
- Worth monitoring

**Score 1-3 (Low)**:
- Academic/theoretical focus
- No clear business application
- Pure research interest

## Output Format

Return ONLY a JSON object:

```json
{
  "relevance_score": 8,
  "confidence": 0.85,
  "primary_benefit": "Enables real-time face customization with 10x speedup",
  "business_application": "Core product feature for kig face generation pipeline",
  "technical_maturity": "production_ready",
  "recommended_action": "implement_poc",
  "key_insight": "The proposed method reduces inference time while maintaining quality",
  "risk_factors": ["Requires significant compute resources", "Limited evaluation on anime-style faces"],
  "related_papers": ["arxiv:2401.xxxx", "arxiv:2402.yyyy"]
}
```

Field definitions:
- `relevance_score`: Integer 1-10
- `confidence`: Float 0.0-1.0 (how confident in this score)
- `primary_benefit`: One-sentence business value
- `business_application`: Specific use case at KIGLAND
- `technical_maturity`: "research" | "prototype" | "production_ready"
- `recommended_action": "ignore" | "monitor" | "read" | "implement_poc" | "urgent_review"
- `key_insight`: Most important technical takeaway
- `risk_factors`: List of implementation concerns
- `related_papers`: List of related arXiv IDs if known
```

### 4.3 Batch Scoring Optimization

To minimize API costs, implement batch scoring:

```python
def batch_score_papers(papers, batch_size=5):
    """Score multiple papers in a single LLM call."""
    
    prompt = """Score the following papers for KIGLAND business relevance.
    
KIGLAND CONTEXT: [brief business summary]

PAPERS:
"""
    
    for i, paper in enumerate(papers):
        prompt += f"""
--- Paper {i+1} ---
Title: {paper['title']}
Categories: {', '.join(paper['categories'])}
Abstract: {paper['summary'][:500]}...
"""
    
    prompt += """

Return a JSON array with one object per paper in the same order:
[
  {"paper_index": 1, "relevance_score": 8, ...},
  {"paper_index": 2, "relevance_score": 5, ...},
  ...
]
"""
    
    # Call LLM API once for all papers in batch
    response = llm_api.complete(prompt)
    scores = json.loads(response)
    
    return scores
```

### 4.4 Threshold Configuration

| Score | Action | Digest Inclusion |
|-------|--------|------------------|
| 8-10 | Flag for immediate review | Top section + alert |
| 6-7 | Include in daily digest | Main section |
| 4-5 | Add to weekly summary | Weekly only |
| 1-3 | Store but don't surface | Archive only |

---

## 5. Summary Generation Workflow

### 5.1 High-Scoring Paper Summary Template

For papers scoring 6+, generate structured summaries:

```markdown
### {{title}}

**Authors**: {{authors}}  
**arXiv**: [{{arxiv_id}}]({{abs_url}}) | [PDF]({{pdf_url}})  
**Categories**: {{categories}}  
**Relevance Score**: {{relevance_score}}/10 ⭐

**The Problem**  
{{problem_summary}}

**The Approach**  
{{approach_summary}}

**Why It Matters for KIGLAND**  
{{business_significance}}

**Key Technical Insight**  
{{key_technical_point}}

**Action Recommendation**: {{recommended_action}}
```

### 5.2 Daily Digest Structure

```markdown
# arXiv Intelligence Digest — {{date}}

## 🔥 High Priority (Score 8+)
[Papers requiring immediate attention]

## 📊 Daily Summary
- **Papers Analyzed**: {{total_papers}}
- **Above Threshold (6+)**: {{high_relevance_count}}
- **Categories**: AI: {{cs_ai_count}} | CV: {{cs_cv_count}} | LG: {{cs_lg_count}} | RO: {{cs_ro_count}}

## 🎯 Top Papers by Category

### AI & Agents (cs.AI)
[Summaries...]

### Computer Vision (cs.CV)
[Summaries...]

### Machine Learning (cs.LG)
[Summaries...]

### Robotics (cs.RO)
[Summaries...]

## 📈 Trends & Patterns
[LLM-generated observation of themes across papers]

## 🗄️ Archive
[Links to full database and past digests]
```

### 5.3 Weekly Synthesis

In addition to daily digests, generate a weekly synthesis that:
1. Identifies emerging themes across the week's papers
2. Highlights papers that may have been missed (borderline scores)
3. Tracks citation velocity for previously flagged papers
4. Provides strategic recommendations

---

## 6. Storage Schema

### 6.1 SQLite Database Schema

```sql
-- Main papers table
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,  -- JSON array
    abstract TEXT,
    summary TEXT,  -- LLM-generated summary
    primary_category TEXT,
    categories TEXT,  -- JSON array
    published_at DATETIME,
    updated_at DATETIME,
    pdf_url TEXT,
    abs_url TEXT,
    doi TEXT,
    comment TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Relevance scores table (allows re-scoring over time)
CREATE TABLE relevance_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER REFERENCES papers(id),
    score INTEGER NOT NULL,  -- 1-10
    confidence REAL,  -- 0.0-1.0
    model_version TEXT,  -- LLM model used
    scored_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    rationale TEXT,  -- JSON with full scoring output
    UNIQUE(paper_id, model_version)
);

-- Paper actions tracking
CREATE TABLE paper_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER REFERENCES papers(id),
    action TEXT,  -- 'ignored', 'read', 'poc_started', 'implemented'
    notes TEXT,
    taken_by TEXT,
    taken_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Daily digest tracking
CREATE TABLE digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    file_path TEXT,
    total_papers INTEGER,
    high_relevance_count INTEGER,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX idx_papers_published ON papers(published_at);
CREATE INDEX idx_papers_primary_cat ON papers(primary_category);
CREATE INDEX idx_scores_paper ON relevance_scores(paper_id);
CREATE INDEX idx_scores_value ON relevance_scores(score);
```

### 6.2 JSONL Export Format

For easy processing and versioning, maintain a JSONL dump:

```jsonl
{"arxiv_id": "2602.06043v1", "title": "...", "relevance_score": 8, "rationale": {...}, "fetched_at": "2026-02-06T08:00:00Z"}
{"arxiv_id": "2602.06039v1", "title": "...", "relevance_score": 6, "rationale": {...}, "fetched_at": "2026-02-06T08:00:00Z"}
```

### 6.3 File Organization

```
kigland-intern-room/
└── research/
    ├── intelligence/                    # Daily digests (public)
    │   ├── arxiv/
    │   │   ├── 2026/
    │   │   │   ├── 2026-02-06.md       # Daily digest
    │   │   │   ├── 2026-02-05.md
    │   │   │   └── ...
    │   │   └── weekly/
    │   │       ├── 2026-W05.md         # Weekly synthesis
    │   │       └── ...
    │   └── _templates/
    │       └── arxiv-digest-template.md
    │
    └── _data/                          # Database files (gitignored)
        ├── arxiv/
        │   ├── papers.db               # SQLite database
        │   ├── papers.jsonl            # JSONL backup
        │   └── config.yaml             # Pipeline configuration
        └── ...
```

---

## 7. Success Metrics

### 7.1 System Health Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Daily fetch success rate** | > 99% | Days with successful fetch / total days |
| **API error rate** | < 1% | Failed requests / total requests |
| **Processing latency** | < 30 min | Time from fetch to digest generation |
| **Data freshness** | < 24h | Age of newest paper in digest |

### 7.2 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Relevance precision** | > 80% | Papers scoring 6+ that are actually relevant |
| **False positive rate** | < 20% | Papers scoring 6+ that turn out to be irrelevant |
| **Coverage** | > 95% | Target papers found / target papers published |
| **Digest consumption time** | < 10 min | Average time to read daily digest |

### 7.3 Business Impact Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Papers read** | 2-3 / week | Number of papers flagged for reading |
| **POCs started** | 1 / month | Papers leading to proof-of-concept |
| **Strategic insights** | 2-3 / month | Novel insights informing strategy |
| **Competitive awareness** | 100% | Major competitor papers identified |

### 7.4 Continuous Improvement

Track over time to improve the pipeline:
- Score calibration (are 8s actually better than 6s?)
- Category distribution (are we missing relevant papers in untracked categories?)
- Author tracking (are specific researchers consistently producing relevant work?)
- Citation tracking (do highly-cited papers correlate with high relevance scores?)

---

## 8. Daily Workflow Steps

### 8.1 Automated Workflow (Cron)

```bash
# 08:00 CST daily
0 8 * * * cd /home/remi/clawd && python -m scripts.arxiv_pipeline
```

### 8.2 Workflow Steps

```
Step 1: FETCH (08:00-08:05)
├── Query arXiv API for each target category
├── Parse Atom feed responses
└── Collect all papers from last 24 hours

Step 2: DEDUPLICATE (08:05-08:07)
├── Check SQLite for existing arXiv IDs
├── Filter out already-processed papers
└── Log new papers count

Step 3: BATCH SCORE (08:07-08:20)
├── Group papers into batches of 5
├── Call LLM API for relevance scoring
├── Parse JSON responses
└── Store scores in database

Step 4: SUMMARIZE (08:20-08:25)
├── Filter papers with score >= 6
├── Generate summaries for high-scoring papers
├── Extract key insights and action items
└── Update database with summaries

Step 5: GENERATE DIGEST (08:25-08:28)
├── Render markdown digest from template
├── Write to research/intelligence/arxiv/YYYY-MM-DD.md
├── Update weekly synthesis
└── Commit to git

Step 6: PUBLISH (08:28-08:30)
├── Push to GitHub
├── Update issue tracker if high-priority papers found
└── Send notification if score-10 papers detected
```

### 8.3 Manual Review Workflow

```
Daily (08:30-08:45)
├── Read generated digest
├── Flag papers for deeper review
└── Update paper_actions table

Weekly (Friday)
├── Review weekly synthesis
├── Identify missed opportunities
├── Update scoring prompt if needed
└── Adjust thresholds based on feedback

Monthly
├── Review success metrics
├── Analyze score calibration
├── Expand/contract category coverage
└── Update KIGLAND context in prompts
```

---

## 9. Implementation Roadmap

### Phase 1: MVP (Week 1)
- [ ] Basic fetcher script (Python)
- [ ] SQLite schema setup
- [ ] Manual scoring (no LLM)
- [ ] Simple markdown output

### Phase 2: Automation (Week 2)
- [ ] LLM integration for scoring
- [ ] Automated daily workflow
- [ ] Digest generation
- [ ] GitHub integration

### Phase 3: Refinement (Week 3-4)
- [ ] Batch scoring optimization
- [ ] Weekly synthesis
- [ ] Metrics tracking
- [ ] Prompt tuning based on feedback

### Phase 4: Scale (Ongoing)
- [ ] Additional categories if needed
- [ ] Citation tracking
- [ ] Author alerts
- [ ] Competitive intelligence integration

---

## 10. Sample Output

### Example Daily Digest

See `research/intelligence/arxiv/2026-02-06.md` for a live example.

### Example Scored Paper Entry

```json
{
  "arxiv_id": "2602.06038v1",
  "title": "CommCP: Efficient Multi-Agent Coordination via LLM-Based Communication with Conformal Prediction",
  "authors": ["Xiaopan Zhang", "Zejin Wang", "Zhixu Li", "Jianpeng Yao", "Jiachen Li"],
  "primary_category": "cs.RO",
  "categories": ["cs.RO", "cs.AI", "cs.CV", "cs.LG", "cs.MA"],
  "published": "2026-02-05T18:59:45Z",
  "relevance_score": 7,
  "confidence": 0.82,
  "rationale": {
    "primary_benefit": "Enables reliable multi-agent coordination for complex creative workflows",
    "business_application": "Could power collaborative AI agents for kigurumi design pipeline",
    "technical_maturity": "prototype",
    "recommended_action": "monitor",
    "key_insight": "Conformal prediction reduces communication overhead while maintaining coordination quality",
    "risk_factors": ["Limited to specific multi-agent scenarios", "Requires significant compute for conformal calibration"]
  },
  "summary": "Multi-agent LLM systems often waste communication. CommCP uses conformal prediction to only send messages when confident, reducing overhead while maintaining task success rates.",
  "fetched_at": "2026-02-06T08:00:00Z"
}
```

---

## 11. Appendix

### A. arXiv Category Reference

| Code | Name | Description |
|------|------|-------------|
| cs.AI | Artificial Intelligence | General AI, agents, planning, reasoning |
| cs.CV | Computer Vision | Image/video processing, recognition, generation |
| cs.LG | Machine Learning | Learning algorithms, deep learning, optimization |
| cs.RO | Robotics | Robot control, manipulation, autonomy |
| cs.CL | Computation and Language | NLP, language models, speech |
| cs.GR | Graphics | Computer graphics, 3D rendering, visualization |
| cs.HC | Human-Computer Interaction | User interfaces, usability, interaction design |
| cs.MA | Multiagent Systems | Distributed AI, game theory, coordination |

### B. API Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| 503 | arXiv overloaded | Retry with exponential backoff |
| 404 | Invalid query | Check query syntax |
| 400 | Bad request | Validate parameters |
| Timeout | Network issue | Retry with longer timeout |

### C. Related Resources

- [arXiv API Documentation](https://arxiv.org/help/api/index)
- [arXiv API User Manual](https://arxiv.org/help/api/user-manual)
- [Feedparser Documentation](https://feedparser.readthedocs.io/)

---

*Document Version: 1.0*  
*Last Updated: 2026-02-06*  
*Author: RemiBot for KIGLAND Intern Room*
