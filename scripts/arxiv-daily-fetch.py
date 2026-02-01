#!/usr/bin/env python3
"""
arXiv Daily Paper Fetcher for KIGLAND

Fetches daily papers from arXiv API for AI/ML categories,
relevance-filters for KIGLAND focus areas, and generates
a structured markdown report.

Usage:
    python scripts/arxiv-daily-fetch.py [--date YYYY-MM-DD] [--test]

Author: KIGLAND Research Intelligence
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from xml.etree import ElementTree as ET

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "http://export.arxiv.org/api/query"
RATE_LIMIT_SECONDS = 3
MAX_RESULTS_PER_CALL = 100
BATCH_SIZE = 50  # Smaller batches for testing

# Target categories for KIGLAND research
TARGET_CATEGORIES = ["cs.AI", "cs.CV", "cs.LG", "cs.RO"]

# XML Namespaces
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

# Output directory
OUTPUT_DIR = Path("/home/remi/clawd/kigland-intern-room/research/intelligence/arxiv-daily")

# KIGLAND Focus Areas - Keywords for relevance filtering
KIGLAND_KEYWORDS = {
    "ai": [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "transformer", "llm", "large language model",
        "foundation model", "generative ai", "diffusion model",
        "reinforcement learning", "agent", "multi-agent"
    ],
    "vision": [
        "computer vision", "image generation", "video generation",
        "3d reconstruction", "pose estimation", "face recognition",
        "object detection", "segmentation", "generative adversarial",
        "nerf", "neural radiance field", "synthetic data"
    ],
    "agents": [
        "autonomous agent", "ai agent", "embodied ai", "robot learning",
        "task planning", "tool use", "function calling", "api calling",
        "llm agent", "language agent", "interactive learning"
    ],
    "manufacturing": [
        "3d printing", "additive manufacturing", "digital twin",
        "industrial automation", "quality control", "defect detection",
        "predictive maintenance", "smart manufacturing", "industry 4.0"
    ],
    "kigurumi": [
        "kigurumi", "cosplay", "mask detection", "facial capture",
        "motion capture", "character animation", "avatar generation",
        "virtual idol", "vtuber", "digital avatar", "face tracking"
    ],
}

# Flatten all keywords for matching
ALL_KEYWORDS = [kw for cat in KIGLAND_KEYWORDS.values() for kw in cat]

# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the script."""
    logger = logging.getLogger("arxiv_fetcher")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    return logger

# ============================================================================
# ArXiv API Client
# ============================================================================

class ArxivAPIError(Exception):
    """Custom exception for arXiv API errors."""
    pass


class ArxivAPI:
    """
    Client for the arXiv API with rate limiting and error handling.
    """
    
    def __init__(self, delay: int = RATE_LIMIT_SECONDS):
        """
        Initialize the API client.
        
        Args:
            delay: Seconds to wait between requests (default 3)
        """
        self.delay = delay
        self.last_request_time: Optional[float] = None
        self.logger = logging.getLogger("arxiv_fetcher.api")
    
    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self.last_request_time is not None:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _build_url(
        self,
        query: str,
        start: int = 0,
        max_results: int = MAX_RESULTS_PER_CALL,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> str:
        """Build the API URL with query parameters."""
        encoded_query = urllib.parse.quote(query, safe="+=[]")
        url = (
            f"{BASE_URL}?search_query={encoded_query}"
            f"&start={start}"
            f"&max_results={max_results}"
            f"&sortBy={sort_by}"
            f"&sortOrder={sort_order}"
        )
        return url
    
    def fetch(
        self,
        query: str,
        start: int = 0,
        max_results: int = MAX_RESULTS_PER_CALL,
        retries: int = 3
    ) -> str:
        """
        Fetch data from arXiv API with rate limiting and retry logic.
        
        Args:
            query: Search query string
            start: Start index (0-based)
            max_results: Number of results to fetch
            retries: Number of retry attempts on failure
            
        Returns:
            Raw XML response string
            
        Raises:
            ArxivAPIError: If all retry attempts fail
        """
        url = self._build_url(query, start, max_results)
        self.logger.debug(f"Fetching: {url}")
        
        for attempt in range(retries):
            try:
                self._rate_limit()
                
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "KIGLAND-Research/1.0 (research@kigland.dev)"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = response.read().decode("utf-8")
                    
                # Check for error response
                if "<title>Error</title>" in data:
                    error_match = re.search(
                        r"<summary>(.*?)</summary>", data, re.DOTALL
                    )
                    error_msg = error_match.group(1) if error_match else "Unknown error"
                    raise ArxivAPIError(f"API Error: {error_msg}")
                
                return data
                
            except urllib.error.HTTPError as e:
                self.logger.warning(f"HTTP {e.code} on attempt {attempt + 1}: {e.reason}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise ArxivAPIError(f"HTTP Error {e.code}: {e.reason}") from e
                    
            except urllib.error.URLError as e:
                self.logger.warning(f"URL Error on attempt {attempt + 1}: {e.reason}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise ArxivAPIError(f"URL Error: {e.reason}") from e
                    
            except TimeoutError as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise ArxivAPIError("Request timeout") from e
        
        raise ArxivAPIError("All retry attempts failed")
    
    def fetch_all(
        self,
        query: str,
        max_total: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch all results with pagination.
        
        Args:
            query: Search query string
            max_total: Maximum total results to fetch
            
        Returns:
            List of paper dictionaries
        """
        all_papers = []
        start = 0
        
        while start < max_total:
            self.logger.info(f"Fetching papers {start} to {start + BATCH_SIZE}...")
            
            try:
                xml_data = self.fetch(query, start=start, max_results=BATCH_SIZE)
                papers = self._parse_entries(xml_data)
                
                if not papers:
                    self.logger.info("No more papers found.")
                    break
                
                all_papers.extend(papers)
                
                # Check if we've reached the total
                total_results = self._get_total_results(xml_data)
                if start + BATCH_SIZE >= min(total_results, max_total):
                    break
                
                start += BATCH_SIZE
                
            except ArxivAPIError as e:
                self.logger.error(f"Failed to fetch batch: {e}")
                break
        
        self.logger.info(f"Fetched {len(all_papers)} papers total")
        return all_papers
    
    def _parse_entries(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse Atom XML and extract paper metadata."""
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            self.logger.error(f"XML parse error: {e}")
            return []
        
        entries = []
        
        for entry in root.findall("atom:entry", NAMESPACES):
            try:
                paper = self._parse_single_entry(entry)
                if paper:
                    entries.append(paper)
            except Exception as e:
                self.logger.warning(f"Failed to parse entry: {e}")
                continue
        
        return entries
    
    def _parse_single_entry(self, entry: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single entry element into a paper dictionary."""
        paper = {}
        
        # Required fields
        id_elem = entry.find("atom:id", NAMESPACES)
        if id_elem is None or not id_elem.text:
            return None
        paper["id"] = id_elem.text.strip()
        
        title_elem = entry.find("atom:title", NAMESPACES)
        paper["title"] = self._clean_text(title_elem.text) if title_elem is not None else ""
        
        summary_elem = entry.find("atom:summary", NAMESPACES)
        paper["summary"] = self._clean_text(summary_elem.text) if summary_elem is not None else ""
        
        published_elem = entry.find("atom:published", NAMESPACES)
        paper["published"] = published_elem.text if published_elem is not None else ""
        
        updated_elem = entry.find("atom:updated", NAMESPACES)
        paper["updated"] = updated_elem.text if updated_elem is not None else ""
        
        # Authors
        authors = []
        for author in entry.findall("atom:author", NAMESPACES):
            name_elem = author.find("atom:name", NAMESPACES)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        paper["authors"] = authors
        
        # Categories
        primary_cat = entry.find("arxiv:primary_category", NAMESPACES)
        paper["primary_category"] = (
            primary_cat.get("term") if primary_cat is not None else ""
        )
        
        categories = []
        for cat in entry.findall("atom:category", NAMESPACES):
            term = cat.get("term")
            if term:
                categories.append(term)
        paper["categories"] = categories
        
        # Links
        paper["abstract_url"] = None
        paper["pdf_url"] = None
        
        for link in entry.findall("atom:link", NAMESPACES):
            rel = link.get("rel", "")
            title = link.get("title", "")
            href = link.get("href", "")
            
            if rel == "alternate":
                paper["abstract_url"] = href
            elif rel == "related" and title == "pdf":
                paper["pdf_url"] = href
        
        # Optional fields
        comment = entry.find("arxiv:comment", NAMESPACES)
        paper["comment"] = comment.text if comment is not None else None
        
        journal_ref = entry.find("arxiv:journal_ref", NAMESPACES)
        paper["journal_ref"] = journal_ref.text if journal_ref is not None else None
        
        doi = entry.find("arxiv:doi", NAMESPACES)
        paper["doi"] = doi.text if doi is not None else None
        
        return paper
    
    def _clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove excessive whitespace and newlines
        text = " ".join(text.split())
        return text.strip()
    
    def _get_total_results(self, xml_data: str) -> int:
        """Extract total result count from response."""
        try:
            root = ET.fromstring(xml_data)
            total = root.find("opensearch:totalResults", NAMESPACES)
            if total is not None and total.text:
                return int(total.text)
        except (ET.ParseError, ValueError) as e:
            self.logger.warning(f"Failed to parse total results: {e}")
        return 0


# ============================================================================
# Relevance Filter
# ============================================================================

class RelevanceFilter:
    """
    Filters papers by relevance to KIGLAND focus areas.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("arxiv_fetcher.filter")
        self.keywords = KIGLAND_KEYWORDS
        self.all_keywords = ALL_KEYWORDS
    
    def calculate_score(self, paper: Dict[str, Any]) -> tuple[float, List[str]]:
        """
        Calculate relevance score for a paper.
        
        Returns:
            Tuple of (score, matched_categories)
        """
        title = paper.get("title", "").lower()
        summary = paper.get("summary", "").lower()
        categories = [c.lower() for c in paper.get("categories", [])]
        
        text = f"{title} {summary}"
        score = 0.0
        matched_areas = []
        
        # Check each focus area
        for area, keywords in self.keywords.items():
            area_score = 0
            for keyword in keywords:
                # Title matches are weighted more heavily
                if keyword.lower() in title:
                    area_score += 3
                if keyword.lower() in summary:
                    area_score += 1
            
            if area_score > 0:
                score += area_score
                matched_areas.append(area)
        
        # Bonus for target categories
        target_cats = [c.lower() for c in TARGET_CATEGORIES]
        if any(cat in target_cats for cat in categories):
            score *= 1.2
        
        return score, matched_areas
    
    def filter_papers(
        self,
        papers: List[Dict[str, Any]],
        min_score: float = 1.0,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter and rank papers by relevance.
        
        Args:
            papers: List of paper dictionaries
            min_score: Minimum relevance score to include
            top_k: Maximum number of papers to return (None for all above threshold)
            
        Returns:
            Filtered and sorted list of papers with relevance metadata
        """
        scored_papers = []
        
        for paper in papers:
            score, matched_areas = self.calculate_score(paper)
            
            if score >= min_score:
                paper["relevance_score"] = round(score, 2)
                paper["matched_areas"] = matched_areas
                scored_papers.append(paper)
        
        # Sort by score (descending)
        scored_papers.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        if top_k:
            scored_papers = scored_papers[:top_k]
        
        self.logger.info(
            f"Filtered {len(papers)} papers to {len(scored_papers)} relevant papers "
            f"(min_score={min_score})"
        )
        
        return scored_papers


# ============================================================================
# Report Generator
# ============================================================================

class ReportGenerator:
    """
    Generates markdown reports from paper data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("arxiv_fetcher.report")
    
    def generate_markdown(
        self,
        papers: List[Dict[str, Any]],
        date: datetime,
        total_fetched: int
    ) -> str:
        """
        Generate a markdown report from paper list.
        
        Args:
            papers: List of paper dictionaries with relevance metadata
            date: Date of the report
            total_fetched: Total number of papers fetched
            
        Returns:
            Markdown-formatted report string
        """
        date_str = date.strftime("%Y-%m-%d")
        
        lines = [
            "# KIGLAND Daily arXiv Intelligence Report",
            "",
            f"**Date:** {date_str}",
            f"**Categories:** {', '.join(TARGET_CATEGORIES)}",
            f"**Total Papers Fetched:** {total_fetched}",
            f"**Relevant Papers Found:** {len(papers)}",
            "",
            "---",
            "",
        ]
        
        # Summary section
        lines.extend([
            "## 📊 Summary",
            "",
            f"This report covers {len(papers)} papers relevant to KIGLAND focus areas:",
            "",
        ])
        
        # Count by focus area
        area_counts = {}
        for paper in papers:
            for area in paper.get("matched_areas", []):
                area_counts[area] = area_counts.get(area, 0) + 1
        
        for area, count in sorted(area_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- **{area.title()}:** {count} papers")
        
        lines.extend(["", "---", ""])
        
        # Papers section
        lines.extend([
            "## 📄 Papers",
            "",
        ])
        
        for i, paper in enumerate(papers, 1):
            lines.extend(self._format_paper(paper, i))
            lines.append("")
        
        # Footer
        lines.extend([
            "---",
            "",
            "*This report was automatically generated by the KIGLAND arXiv Pipeline.*",
            "*Thank you to arXiv for use of its open access interoperability.*",
        ])
        
        return "\n".join(lines)
    
    def _format_paper(self, paper: Dict[str, Any], index: int) -> List[str]:
        """Format a single paper entry."""
        lines = []
        
        # Title with link
        title = paper.get("title", "Untitled")
        abstract_url = paper.get("abstract_url") or paper.get("id", "")
        lines.append(f"### {index}. [{title}]({abstract_url})")
        lines.append("")
        
        # Metadata
        authors = paper.get("authors", [])
        if len(authors) > 3:
            author_str = f"{', '.join(authors[:3])} et al."
        else:
            author_str = ', '.join(authors) if authors else "Unknown"
        lines.append(f"**Authors:** {author_str}")
        
        # Categories
        categories = paper.get("categories", [])
        if categories:
            lines.append(f"**Categories:** {', '.join(categories[:5])}")
        
        # Publication date
        published = paper.get("published", "")
        if published:
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                lines.append(f"**Published:** {pub_date.strftime('%Y-%m-%d')}")
            except:
                lines.append(f"**Published:** {published}")
        
        # Relevance
        score = paper.get("relevance_score", 0)
        matched_areas = paper.get("matched_areas", [])
        if matched_areas:
            lines.append(f"**Relevance Score:** {score} | **Areas:** {', '.join(matched_areas)}")
        
        # Links
        pdf_url = paper.get("pdf_url", "")
        if pdf_url:
            lines.append(f"**PDF:** [Download]({pdf_url})")
        
        lines.append("")
        
        # Abstract (truncated)
        summary = paper.get("summary", "")
        if summary:
            # Truncate to ~300 chars
            if len(summary) > 300:
                summary = summary[:297] + "..."
            lines.append(f"**Abstract:** {summary}")
        
        return lines
    
    def save_json(
        self,
        papers: List[Dict[str, Any]],
        filepath: Path
    ) -> None:
        """Save papers as JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Saved JSON to {filepath}")
    
    def save_markdown(
        self,
        content: str,
        filepath: Path
    ) -> None:
        """Save markdown report to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        self.logger.info(f"Saved Markdown to {filepath}")


# ============================================================================
# Main Pipeline
# ============================================================================

class ArxivPipeline:
    """
    Main pipeline for fetching and processing arXiv papers.
    """
    
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.api = ArxivAPI()
        self.filter = RelevanceFilter()
        self.report = ReportGenerator()
        self.logger = logging.getLogger("arxiv_fetcher.pipeline")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_query(self, date: Optional[datetime] = None) -> str:
        """
        Build the search query for target categories and date.
        
        Args:
            date: Target date (defaults to yesterday)
            
        Returns:
            URL-encoded query string
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        # Date range: from start of day to end of day
        date_start = date.strftime("%Y%m%d0000")
        date_end = (date + timedelta(days=1)).strftime("%Y%m%d0000")
        
        # Build category query with OR
        cat_query = "+OR+".join([f"cat:{c}" for c in TARGET_CATEGORIES])
        
        # Full query with date filter
        query = f"({cat_query})+AND+submittedDate:[{date_start}+TO+{date_end}]"
        
        return query
    
    def run(
        self,
        date: Optional[datetime] = None,
        test_mode: bool = False,
        min_score: float = 1.0,
        max_papers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the full pipeline.
        
        Args:
            date: Target date for fetching papers
            test_mode: If True, fetch only a small batch for testing
            min_score: Minimum relevance score for filtering
            max_papers: Maximum papers to fetch (None for unlimited)
            
        Returns:
            Dictionary with results summary
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        self.logger.info(f"Starting arXiv pipeline for {date.strftime('%Y-%m-%d')}")
        self.logger.info(f"Test mode: {test_mode}")
        
        # Build query
        query = self.build_query(date)
        self.logger.debug(f"Query: {query}")
        
        # Fetch papers
        if test_mode:
            self.logger.info("Test mode: fetching small batch (10 papers)")
            xml_data = self.api.fetch(query, start=0, max_results=10)
            papers = self.api._parse_entries(xml_data)
        else:
            max_fetch = max_papers or 500
            papers = self.api.fetch_all(query, max_total=max_fetch)
        
        total_fetched = len(papers)
        self.logger.info(f"Fetched {total_fetched} papers")
        
        if not papers:
            self.logger.warning("No papers found for the specified criteria")
            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_fetched": 0,
                "relevant_count": 0,
                "output_files": []
            }
        
        # Filter by relevance
        relevant_papers = self.filter.filter_papers(papers, min_score=min_score)
        self.logger.info(f"Found {len(relevant_papers)} relevant papers")
        
        # Generate report
        date_str = date.strftime("%Y-%m-%d")
        markdown_content = self.report.generate_markdown(
            relevant_papers, date, total_fetched
        )
        
        # Save outputs
        output_files = []
        
        # JSON output
        json_path = self.output_dir / f"arxiv-{date_str}.json"
        self.report.save_json(relevant_papers, json_path)
        output_files.append(str(json_path))
        
        # Markdown report
        md_path = self.output_dir / f"arxiv-{date_str}.md"
        self.report.save_markdown(markdown_content, md_path)
        output_files.append(str(md_path))
        
        # Summary
        result = {
            "date": date_str,
            "total_fetched": total_fetched,
            "relevant_count": len(relevant_papers),
            "output_files": output_files
        }
        
        self.logger.info("Pipeline completed successfully")
        self.logger.info(f"Results saved to: {self.output_dir}")
        
        return result


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Fetch and process daily arXiv papers for KIGLAND research"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to fetch papers for (YYYY-MM-DD format, default: yesterday)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (fetch only 10 papers)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=1.0,
        help="Minimum relevance score for filtering (default: 1.0)"
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=None,
        help="Maximum papers to fetch (default: unlimited)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(verbose=args.verbose)
    
    # Parse date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            sys.exit(1)
    
    # Run pipeline
    try:
        pipeline = ArxivPipeline(output_dir=Path(args.output_dir))
        result = pipeline.run(
            date=target_date,
            test_mode=args.test,
            min_score=args.min_score,
            max_papers=args.max_papers
        )
        
        # Print summary
        print("\n" + "=" * 50)
        print("PIPELINE COMPLETE")
        print("=" * 50)
        print(f"Date: {result['date']}")
        print(f"Total papers fetched: {result['total_fetched']}")
        print(f"Relevant papers: {result['relevant_count']}")
        print(f"Output files:")
        for f in result['output_files']:
            print(f"  - {f}")
        print("=" * 50)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
