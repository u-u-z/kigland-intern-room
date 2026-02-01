# arXiv API Technical Specification

## Automated Paper Tracking Pipeline

**Document Version:** 1.0  
**Date:** 2026-02-01  
**Purpose:** Technical reference for building an automated paper tracking system using the arXiv API

---

## 1. API Overview

### 1.1 Base Endpoint
```
http://export.arxiv.org/api/{method_name}?{parameters}
```

### 1.2 Primary Query Endpoint
```
http://export.arxiv.org/api/query?{parameters}
```

### 1.3 Protocol
- **HTTP Methods:** GET or POST
- **Response Format:** Atom 1.0 (XML-based)
- **Encoding:** UTF-8
- **No authentication required** for public API access

---

## 2. Rate Limits and Usage Guidelines

### 2.1 Rate Limiting
| Limit | Value | Notes |
|-------|-------|-------|
| Request Frequency | **1 request per 3 seconds** | Applies to all machines under your control |
| Concurrent Connections | **1 connection at a time** | Do not parallelize requests |
| Max Results per Query | **30,000 total** | Retrieved in slices of max 2,000 at a time |
| Max Results per Call | **2,000** | Use pagination for larger result sets |

### 2.2 Best Practices
- **Implement 3-second delays** between consecutive API calls
- **Cache results** - Search results only change at midnight (24-hour submission cycle)
- **Use smaller slices** (< 1,000 results) for better performance
- **No need to query more than once per day** for the same search

### 2.3 Rate Limit Example (Python)
```python
import time
import urllib.request

def fetch_with_rate_limit(url):
    """Fetch URL with 3-second rate limiting"""
    time.sleep(3)  # Respect rate limits
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')
```

---

## 3. Query Parameters

### 3.1 Query Interface Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search_query` | string | No | None | Search query string |
| `id_list` | comma-delimited string | No | None | List of arXiv IDs |
| `start` | integer | No | 0 | 0-based index of first result |
| `max_results` | integer | No | 10 | Number of results to return (max 2000) |
| `sortBy` | string | No | relevance | Sort order: `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | string | No | descending | Sort direction: `ascending`, `descending` |

### 3.2 Parameter Logic
| search_query | id_list | Returns |
|--------------|---------|---------|
| Yes | No | Articles matching search_query |
| No | Yes | Articles in id_list |
| Yes | Yes | Articles in id_list that also match search_query (filter mode) |

---

## 4. Search Query Construction

### 4.1 Search Field Prefixes

| Prefix | Field | Example |
|--------|-------|---------|
| `ti` | Title | `ti:neural` |
| `au` | Author | `au:Hinton` |
| `abs` | Abstract | `abs:learning` |
| `co` | Comment | `co:revised` |
| `jr` | Journal Reference | `jr:Nature` |
| `cat` | **Subject Category** | `cat:cs.AI` |
| `rn` | Report Number | `rn:MIT-CSAIL` |
| `id` | ID (use id_list instead) | Not recommended |
| `all` | All fields | `all:transformer` |

### 4.2 Boolean Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | Both terms must match | `au:Smith AND ti:neural` |
| `OR` | Either term matches | `cat:cs.AI OR cat:cs.LG` |
| `ANDNOT` | Exclude term | `ti:learning ANDNOT ti:deep` |

### 4.3 Grouping and Phrases

| Symbol | URL Encoding | Purpose |
|--------|--------------|---------|
| `( )` | `%28 %29` | Group Boolean expressions |
| `" "` | `%22 %22` | Search for exact phrases |
| Space | `+` | Separate query components |

---

## 5. Category Queries (Target Categories)

### 5.1 Primary Categories for ML/AI Pipeline

| Category | Description | Query Example |
|----------|-------------|---------------|
| **cs.AI** | Artificial Intelligence | `cat:cs.AI` |
| **cs.CV** | Computer Vision and Pattern Recognition | `cat:cs.CV` |
| **cs.LG** | Machine Learning | `cat:cs.LG` |
| **cs.RO** | Robotics | `cat:cs.RO` |

### 5.2 Category Query Examples

#### Single Category
```
http://export.arxiv.org/api/query?search_query=cat:cs.AI&start=0&max_results=100
```

#### Multiple Categories (OR)
```
http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CV+OR+cat:cs.LG+OR+cat:cs.RO&start=0&max_results=100
```

#### Category with Date Filter
```
http://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+submittedDate:[202401010000+TO+202402010000]&sortBy=submittedDate&sortOrder=descending
```

#### Category + Keyword
```
http://export.arxiv.org/api/query?search_query=cat:cs.CV+AND+ti:segmentation&max_results=50
```

### 5.3 Date Range Filtering

Format: `[YYYYMMDDTTTT+TO+YYYYMMDDTTTT]` (24-hour GMT time)

```
submittedDate:[202301010600+TO+202401010600]
```

---

## 6. Response Format (Atom 1.0)

### 6.1 Feed-Level Elements

| Element | Description |
|---------|-------------|
| `<title>` | Canonicalized query string |
| `<id>` | Unique query identifier |
| `<updated>` | Last update time (midnight of current day) |
| `<link>` | Self-referencing URL |
| `<opensearch:totalResults>` | Total number of matching results |
| `<opensearch:startIndex>` | Index of first returned result (0-based) |
| `<opensearch:itemsPerPage>` | Number of results in this response |

### 6.2 Entry-Level Elements (Paper Metadata)

| Element | Description | Example |
|---------|-------------|---------|
| `<title>` | Paper title | "Attention Is All You Need" |
| `<id>` | arXiv URL | `http://arxiv.org/abs/1706.03762` |
| `<published>` | Version 1 submission date | `2017-06-12T17:27:05Z` |
| `<updated>` | Retrieved version date | `2017-06-12T17:27:05Z` |
| `<summary>` | Abstract | Paper abstract text |
| `<author>` | Author list | `<name>John Doe</name>` |
| `<category>` | Categories | `term="cs.CL"` |
| `<arxiv:primary_category>` | Primary category | `term="cs.CL"` |
| `<arxiv:comment>` | Author comments | `6 pages, 3 figures` |
| `<arxiv:journal_ref>` | Journal reference | `Eur.Phys.J. C31 (2003) 17-29` |
| `<arxiv:doi>` | DOI | `10.1234/example` |
| `<arxiv:affiliation>` | Author affiliation | Child of `<author>` |

### 6.3 Link Elements

| `rel` | `title` | Points To |
|-------|---------|-----------|
| `alternate` | - | Abstract page (HTML) |
| `related` | `pdf` | PDF download |
| `related` | `doi` | Resolved DOI (if available) |

### 6.4 Example Response Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title>ArXiv Query: search_query=cat:cs.AI&amp;start=0&amp;max_results=1</title>
  <id>http://arxiv.org/api/...</id>
  <updated>2024-01-01T00:00:00-05:00</updated>
  <opensearch:totalResults>1000</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  
  <entry>
    <id>http://arxiv.org/abs/1706.03762</id>
    <published>2017-06-12T17:27:05Z</published>
    <updated>2017-06-12T17:27:05Z</updated>
    <title>Attention Is All You Need</title>
    <summary>The dominant sequence transduction models...</summary>
    <author><name>Ashish Vaswani</name></author>
    <link href="http://arxiv.org/abs/1706.03762v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
```

---

## 7. Authentication Requirements

### 7.1 Public API Access
- **No API key required** for basic queries
- **No registration required** for read-only access
- Rate limits apply to all users equally

### 7.2 Terms of Use Highlights

#### ✅ Allowed
- Retrieve and store descriptive metadata (CC0 license)
- Personal/research use of e-print content
- Build discovery tools and notification services
- Create visualizations and citation graphs
- Link to arXiv.org abstract pages

#### ❌ Prohibited
- Store and serve PDFs from your servers (without copyright permission)
- Imply arXiv endorsement of your project
- Circumvent rate limits
- Use others' credentials

#### 📋 Requirements
- Include acknowledgment: "Thank you to arXiv for use of its open access interoperability"
- Do not use "arXiv", "arXiv.org", "arXiv Labs" branding without permission
- Respect the 3-second rate limit
- Cache results - don't query same data multiple times per day

---

## 8. Implementation Recommendations

### 8.1 Recommended Libraries

| Language | HTTP | Atom Parsing |
|----------|------|--------------|
| Python | `urllib`, `requests` | `feedparser`, `xml.etree.ElementTree` |
| JavaScript | `fetch`, `axios` | `fast-xml-parser` |
| Ruby | `net/http` | `feedtools` |
| PHP | `file_get_contents()`, `cURL` | `SimplePie` |
| Perl | `LWP` | `XML::Atom` |

### 8.2 Python Implementation Example

```python
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

class ArxivAPI:
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # XML namespaces
    NS = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom',
        'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
    }
    
    def __init__(self, delay=3):
        self.delay = delay  # Rate limit delay in seconds
        self.last_request = None
    
    def _rate_limit(self):
        """Ensure 3-second delay between requests"""
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self.last_request = datetime.now()
    
    def search(self, query, start=0, max_results=100, 
               sort_by="submittedDate", sort_order="descending"):
        """
        Search arXiv with rate limiting
        
        Args:
            query: Search query string
            start: Start index (0-based)
            max_results: Number of results (max 2000)
            sort_by: 'relevance', 'lastUpdatedDate', 'submittedDate'
            sort_order: 'ascending', 'descending'
        """
        self._rate_limit()
        
        url = (f"{self.BASE_URL}?search_query={urllib.parse.quote(query)}"
               f"&start={start}&max_results={max_results}"
               f"&sortBy={sort_by}&sortOrder={sort_order}")
        
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    
    def parse_entries(self, xml_data):
        """Parse Atom XML and extract paper metadata"""
        root = ET.fromstring(xml_data)
        entries = []
        
        for entry in root.findall('atom:entry', self.NS):
            paper = {
                'id': entry.find('atom:id', self.NS).text,
                'title': entry.find('atom:title', self.NS).text.strip(),
                'summary': entry.find('atom:summary', self.NS).text.strip(),
                'published': entry.find('atom:published', self.NS).text,
                'updated': entry.find('atom:updated', self.NS).text,
                'authors': [a.find('atom:name', self.NS).text 
                           for a in entry.findall('atom:author', self.NS)],
                'primary_category': entry.find(
                    'arxiv:primary_category', self.NS).get('term'),
                'categories': [c.get('term') 
                              for c in entry.findall('atom:category', self.NS)],
                'pdf_url': None,
                'abstract_url': None
            }
            
            # Extract links
            for link in entry.findall('atom:link', self.NS):
                rel = link.get('rel')
                title = link.get('title', '')
                href = link.get('href')
                
                if rel == 'alternate':
                    paper['abstract_url'] = href
                elif rel == 'related' and title == 'pdf':
                    paper['pdf_url'] = href
            
            # Optional fields
            comment = entry.find('arxiv:comment', self.NS)
            if comment is not None:
                paper['comment'] = comment.text
            
            journal_ref = entry.find('arxiv:journal_ref', self.NS)
            if journal_ref is not None:
                paper['journal_ref'] = journal_ref.text
            
            doi = entry.find('arxiv:doi', self.NS)
            if doi is not None:
                paper['doi'] = doi.text
            
            entries.append(paper)
        
        return entries
    
    def get_total_results(self, xml_data):
        """Get total number of results for pagination"""
        root = ET.fromstring(xml_data)
        total = root.find('opensearch:totalResults', self.NS)
        return int(total.text) if total is not None else 0


# Example: Daily paper tracking for ML categories
class PaperTracker:
    CATEGORIES = ['cs.AI', 'cs.CV', 'cs.LG', 'cs.RO']
    
    def __init__(self):
        self.api = ArxivAPI()
    
    def get_yesterdays_papers(self):
        """Fetch papers submitted yesterday in target categories"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        today = datetime.now().strftime('%Y%m%d')
        
        # Build category query
        cat_query = '+OR+'.join([f'cat:{c}' for c in self.CATEGORIES])
        
        # Add date filter
        query = f"({cat_query})+AND+submittedDate:[{yesterday}0000+TO+{today}0000]"
        
        xml_data = self.api.search(query, max_results=1000, 
                                   sort_by='submittedDate')
        papers = self.api.parse_entries(xml_data)
        
        return papers
```

### 8.3 Pagination Strategy

```python
def fetch_all_results(api, query, max_total=10000):
    """
    Fetch all results with proper pagination and rate limiting
    """
    all_papers = []
    start = 0
    batch_size = 100  # Small batches for efficiency
    
    while start < max_total:
        xml_data = api.search(query, start=start, max_results=batch_size)
        papers = api.parse_entries(xml_data)
        
        if not papers:
            break
        
        all_papers.extend(papers)
        
        # Check if we've got all results
        total = api.get_total_results(xml_data)
        if start + batch_size >= total:
            break
        
        start += batch_size
    
    return all_papers
```

### 8.4 Recommended Pipeline Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Scheduler      │────▶│  arXiv API      │────▶│  Data Parser    │
│  (Daily @ 00:05)│     │  (Rate Limited) │     │  (Atom→JSON)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Notification   │◀────│  Diff Engine    │◀────│  Database       │
│  (Email/Slack)  │     │  (New Papers)   │     │  (Deduplication)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 9. Error Handling

### 9.1 Common Errors

| Error | HTTP Code | Cause |
|-------|-----------|-------|
| `start must be an integer` | 400 | Non-integer start parameter |
| `start must be >= 0` | 400 | Negative start value |
| `max_results must be an integer` | 400 | Non-integer max_results |
| `max_results must be >= 0` | 400 | Negative max_results |
| Malformed ID | 400 | Invalid arXiv identifier format |
| Max results exceeded | 400 | Requested > 30,000 results |

### 9.2 Error Response Format
Errors are returned as Atom feeds with a single `<entry>` containing error details:

```xml
<feed>
  <entry>
    <id>http://arxiv.org/api/errors#incorrect_id_format_for_...</id>
    <title>Error</title>
    <summary>incorrect id format for ...</summary>
    <updated>2024-01-01T00:00:00-05:00</updated>
    <author><name>arXiv api core</name></author>
  </entry>
</feed>
```

---

## 10. Additional Resources

### 10.1 Official Documentation
- [arXiv API Help](https://info.arxiv.org/help/api/index.html)
- [API Basics](https://info.arxiv.org/help/api/basics.html)
- [User Manual](https://info.arxiv.org/help/api/user-manual.html)
- [Terms of Use](https://info.arxiv.org/help/api/tou.html)
- [Category Taxonomy](https://arxiv.org/category_taxonomy)

### 10.2 Alternative Interfaces
- **OAI-PMH**: Better for bulk metadata harvesting
- **RSS Feeds**: For simple category-based feeds
- **Bulk Data**: S3 access for large-scale downloads

### 10.3 Community
- [arXiv API Google Group](https://groups.google.com/a/arxiv.org/g/api)

---

## 11. Summary Checklist

### For Implementation:
- [ ] Implement 3-second delay between requests
- [ ] Handle pagination (max 2000 per request)
- [ ] Cache results (daily refresh is sufficient)
- [ ] Parse Atom XML namespaces correctly
- [ ] Handle rate limiting errors gracefully
- [ ] Include arXiv acknowledgment in your project

### For Category Tracking:
- [ ] Use `cat:cs.AI`, `cat:cs.CV`, `cat:cs.LG`, `cat:cs.RO`
- [ ] Combine with OR operator for multiple categories
- [ ] Add `submittedDate` filter for daily tracking
- [ ] Sort by `submittedDate` descending for latest papers

### For Production:
- [ ] Monitor request frequency
- [ ] Implement exponential backoff on errors
- [ ] Store last check timestamp
- [ ] Deduplicate papers by arXiv ID
- [ ] Handle timezone conversions for date filters

---

*End of Specification*
