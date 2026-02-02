#!/usr/bin/env python3
"""
Investment Ecosystem Intelligence - 36Kr Data Tracker
投资生态情报 - 36Kr 数据采集监测脚本

功能：
1. 从多个数据源采集投资事件数据
2. 监测关键词匹配的早期投资事件
3. 存储到 SQLite 数据库
4. 支持增量更新和去重

数据源：
- 36Kr RSS (无需认证)
- 鲸准 API (需要账号)
- IT桔子 (需要账号)
- Crunchbase (国际数据源)

作者: OpenClaw Agent
版本: 1.0.0
"""

import os
import re
import json
import sqlite3
import hashlib
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ 配置 ============

# 监测关键词
KEYWORDS_CONFIG = {
    'early_stage': {
        'keywords': ['天使轮', '种子轮', 'Pre-A轮', '天使+', '种子+', 'A轮'],
        'weight': 10,
        'category': '早期投资'
    },
    'ai': {
        'keywords': ['AI', '人工智能', '大模型', 'LLM', 'Agent', 'AIGC', '机器学习', 
                     '深度学习', '神经网络', 'ChatGPT', 'Claude', 'OpenAI', 'Anthropic'],
        'weight': 10,
        'category': '人工智能'
    },
    'accelerator': {
        'keywords': ['MiraclePlus', '奇绩创坛', 'Y Combinator', 'YC China', 
                     '陆奇', 'Demo Day'],
        'weight': 8,
        'category': '孵化器'
    },
    'niche': {
        'keywords': ['Kigurumi', '二次元', 'Cosplay', 'ACG', '动漫', '虚拟偶像', 
                     'Vtuber', '手办', '潮玩', '盲盒', '谷子'],
        'weight': 6,
        'category': '二次元文化'
    },
    'vc_firms': {
        'keywords': ['红杉', 'IDG', '高瓴', '源码资本', '五源资本', 'GGV', 
                     '真格基金', '金沙江', '经纬中国', '启明创投'],
        'weight': 5,
        'category': '知名机构'
    }
}

# 数据源配置
SOURCES = {
    '36kr_rss': {
        'url': 'https://36kr.com/feed',
        'enabled': True,
        'type': 'rss'
    },
    '36kr_news': {
        'url': 'https://36kr.com/api/newsflash',
        'enabled': False,  # 需要绕开验证码
        'type': 'api'
    },
    'jingdata': {
        'url': 'https://www.jingdata.com/api/funding/search',
        'enabled': False,  # 需要登录
        'type': 'api',
        'auth_required': True
    }
}

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'research', 'investment', 'investment.db')


# ============ 数据模型 ============

@dataclass
class FundingEvent:
    """融资事件数据模型"""
    id: Optional[int] = None
    company_name: str = ''
    funding_round: str = ''
    amount: str = ''
    amount_usd: Optional[float] = None
    currency: str = 'CNY'
    funding_date: Optional[str] = None
    investors: str = ''  # JSON 格式
    description: str = ''
    source_url: str = ''
    source_platform: str = ''
    tags: str = ''  # JSON 格式
    keyword_matches: str = ''  # JSON 格式
    match_score: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def generate_hash(self) -> str:
        """生成唯一标识，用于去重"""
        content = f"{self.company_name}|{self.funding_round}|{self.funding_date}"
        return hashlib.md5(content.encode()).hexdigest()


# ============ 数据库操作 ============

class Database:
    """SQLite 数据库管理"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 融资事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS funding_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                funding_round TEXT,
                amount TEXT,
                amount_usd REAL,
                currency TEXT DEFAULT 'CNY',
                funding_date DATE,
                investors TEXT,  -- JSON
                description TEXT,
                source_url TEXT,
                source_platform TEXT,
                tags TEXT,  -- JSON
                keyword_matches TEXT,  -- JSON
                match_score INTEGER DEFAULT 0,
                event_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 公司信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                industry TEXT,
                sub_industry TEXT,
                location TEXT,
                description TEXT,
                website TEXT,
                founded_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_funding_date ON funding_events(funding_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company ON funding_events(company_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_match_score ON funding_events(match_score)
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
    
    def insert_event(self, event: FundingEvent) -> bool:
        """插入融资事件，自动去重"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        event_hash = event.generate_hash()
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM funding_events WHERE event_hash = ?', (event_hash,))
        if cursor.fetchone():
            logger.debug(f"Event already exists: {event.company_name} {event.funding_round}")
            return False
        
        # 插入新记录
        cursor.execute('''
            INSERT INTO funding_events (
                company_name, funding_round, amount, amount_usd, currency,
                funding_date, investors, description, source_url, source_platform,
                tags, keyword_matches, match_score, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.company_name,
            event.funding_round,
            event.amount,
            event.amount_usd,
            event.currency,
            event.funding_date,
            event.investors,
            event.description,
            event.source_url,
            event.source_platform,
            event.tags,
            event.keyword_matches,
            event.match_score,
            event_hash
        ))
        
        conn.commit()
        logger.info(f"Inserted event: {event.company_name} {event.funding_round}")
        return True
    
    def get_recent_events(self, days: int = 30, min_score: int = 0) -> List[Dict]:
        """获取最近的投资事件"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM funding_events 
            WHERE funding_date >= ? AND match_score >= ?
            ORDER BY match_score DESC, funding_date DESC
        ''', (since_date, min_score))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """获取数据统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 总事件数
        cursor.execute('SELECT COUNT(*) FROM funding_events')
        stats['total_events'] = cursor.fetchone()[0]
        
        # 近30天事件数
        since_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM funding_events WHERE funding_date >= ?', (since_date,))
        stats['recent_30d'] = cursor.fetchone()[0]
        
        # 高匹配度事件数
        cursor.execute('SELECT COUNT(*) FROM funding_events WHERE match_score >= 10')
        stats['high_priority'] = cursor.fetchone()[0]
        
        # 按平台统计
        cursor.execute('''
            SELECT source_platform, COUNT(*) as count 
            FROM funding_events 
            GROUP BY source_platform
        ''')
        stats['by_platform'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# ============ 关键词匹配 ============

def match_keywords(text: str) -> Tuple[List[str], int]:
    """
    匹配关键词，返回匹配的标签和权重分数
    
    Args:
        text: 待匹配的文本
    
    Returns:
        (匹配的标签列表, 总权重分数)
    """
    if not text:
        return [], 0
    
    text = text.lower()
    matched_categories = []
    total_score = 0
    
    for category, config in KEYWORDS_CONFIG.items():
        for keyword in config['keywords']:
            if keyword.lower() in text:
                matched_categories.append(config['category'])
                total_score += config['weight']
                break  # 每个类别只计一次分
    
    return list(set(matched_categories)), total_score


def extract_funding_info(text: str) -> Dict:
    """
    从文本中提取融资信息
    
    使用正则表达式匹配常见的融资信息格式
    """
    info = {
        'company_name': '',
        'funding_round': '',
        'amount': '',
        'investors': []
    }
    
    # 匹配融资轮次
    round_patterns = [
        r'(种子轮|天使轮|天使\+|Pre-A轮|A轮|A\+轮|B轮|C轮|D轮|E轮|F轮|IPO|并购)',
        r'(天使|种子|Pre-A|A|B|C|D|E|F)轮[+\+]?',
    ]
    
    for pattern in round_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['funding_round'] = match.group(1)
            break
    
    # 匹配金额
    amount_patterns = [
        r'(\d+\.?\d*)\s*([万亿])?([人民币美元美金CNYUSD]+)?',
        r'([数百万千万亿]+)([人民币美元美金CNYUSD]+)?',
    ]
    
    # 匹配公司名称 (简单启发式)
    company_patterns = [
        r'([\u4e00-\u9fa5]{2,10})(?:公司|科技|智能|网络)?(?:完成|宣布|获得)',
        r'(?:投资|融资)([\u4e00-\u9fa5]{2,10})(?:的|完成)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            info['company_name'] = match.group(1)
            break
    
    return info


# ============ 数据源采集器 ============

class BaseCrawler:
    """采集器基类"""
    
    def __init__(self):
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch(self, url: str, **kwargs) -> Optional[str]:
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def parse(self, content: str) -> List[FundingEvent]:
        """解析内容，子类需实现"""
        raise NotImplementedError


class Kr36RssCrawler(BaseCrawler):
    """36Kr RSS 采集器"""
    
    def __init__(self):
        super().__init__()
        self.source_name = '36kr_rss'
    
    def fetch_rss(self) -> Optional[str]:
        """获取 RSS 内容"""
        # 尝试多个可能的 RSS 地址
        rss_urls = [
            'https://36kr.com/feed',
            'https://36kr.com/feed-newsflash',
            'https://rsshub.app/36kr/newsflashes'
        ]
        
        for url in rss_urls:
            content = self.fetch(url)
            if content and ('xml' in content or '<rss' in content or '<feed' in content):
                logger.info(f"Successfully fetched RSS from {url}")
                return content
        
        return None
    
    def parse(self, content: str) -> List[FundingEvent]:
        """解析 RSS 内容"""
        events = []
        
        try:
            root = ET.fromstring(content)
            
            # 处理 Atom 格式
            if root.tag.endswith('feed'):
                entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                for entry in entries:
                    event = self._parse_atom_entry(entry)
                    if event:
                        events.append(event)
            
            # 处理 RSS 2.0 格式
            elif root.tag.endswith('rss') or root.tag == 'rss':
                items = root.findall('.//item')
                for item in items:
                    event = self._parse_rss_item(item)
                    if event:
                        events.append(event)
        
        except ET.ParseError as e:
            logger.error(f"RSS parse error: {e}")
        
        return events
    
    def _parse_rss_item(self, item: ET.Element) -> Optional[FundingEvent]:
        """解析 RSS item"""
        title = item.findtext('title', '')
        description = item.findtext('description', '')
        link = item.findtext('link', '')
        pub_date = item.findtext('pubDate', '')
        
        # 只处理与融资相关的条目
        funding_keywords = ['融资', '投资', '轮', '基金', '天使', '种子']
        if not any(kw in title or kw in description for kw in funding_keywords):
            return None
        
        # 提取融资信息
        funding_info = extract_funding_info(title + ' ' + description)
        
        # 关键词匹配
        matched_tags, score = match_keywords(title + ' ' + description)
        
        # 解析日期
        funding_date = None
        if pub_date:
            try:
                # 尝试解析 RSS 日期格式
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                funding_date = dt.strftime('%Y-%m-%d')
            except:
                pass
        
        event = FundingEvent(
            company_name=funding_info['company_name'],
            funding_round=funding_info['funding_round'],
            amount=funding_info['amount'],
            funding_date=funding_date,
            description=description[:500] if description else title,
            source_url=link,
            source_platform=self.source_name,
            tags=json.dumps(matched_tags),
            keyword_matches=json.dumps(matched_tags),
            match_score=score
        )
        
        return event
    
    def _parse_atom_entry(self, entry: ET.Element) -> Optional[FundingEvent]:
        """解析 Atom entry"""
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        title = entry.findtext('atom:title', '', ns)
        content = entry.findtext('atom:content', '', ns)
        summary = entry.findtext('atom:summary', '', ns)
        link_elem = entry.find('atom:link', ns)
        link = link_elem.get('href', '') if link_elem is not None else ''
        updated = entry.findtext('atom:updated', '', ns)
        
        description = content or summary or title
        
        # 只处理与融资相关的条目
        funding_keywords = ['融资', '投资', '轮', '基金', '天使', '种子']
        if not any(kw in title or kw in description for kw in funding_keywords):
            return None
        
        # 提取融资信息
        funding_info = extract_funding_info(title + ' ' + description)
        
        # 关键词匹配
        matched_tags, score = match_keywords(title + ' ' + description)
        
        # 解析日期
        funding_date = None
        if updated:
            try:
                dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                funding_date = dt.strftime('%Y-%m-%d')
            except:
                pass
        
        event = FundingEvent(
            company_name=funding_info['company_name'],
            funding_round=funding_info['funding_round'],
            amount=funding_info['amount'],
            funding_date=funding_date,
            description=description[:500] if description else title,
            source_url=link,
            source_platform=self.source_name,
            tags=json.dumps(matched_tags),
            keyword_matches=json.dumps(matched_tags),
            match_score=score
        )
        
        return event


class MockDataCrawler(BaseCrawler):
    """
    模拟数据采集器
    
    用于生成示例数据，演示数据结构
    """
    
    def __init__(self):
        super().__init__()
        self.source_name = 'mock_data'
    
    def generate_sample_data(self) -> List[FundingEvent]:
        """生成示例数据"""
        sample_events = [
            {
                'company_name': '智元机器人',
                'funding_round': 'A轮',
                'amount': '数亿元人民币',
                'amount_usd': 15000000,
                'currency': 'CNY',
                'funding_date': '2026-01-28',
                'investors': json.dumps(['高瓴创投', '奇绩创坛']),
                'description': '智元机器人完成A轮融资，专注于具身智能和机器人技术研发。',
                'source_url': 'https://36kr.com/p/123456',
                'tags': json.dumps(['人工智能', '早期投资']),
                'keyword_matches': json.dumps(['人工智能', '早期投资']),
                'match_score': 20
            },
            {
                'company_name': 'Kigurumi Studio',
                'funding_round': '天使轮',
                'amount': '数百万元人民币',
                'amount_usd': 500000,
                'currency': 'CNY',
                'funding_date': '2026-01-25',
                'investors': json.dumps(['某知名二次元基金']),
                'description': '专注Kigurumi头壳定制的初创公司获得天使轮投资。',
                'source_url': 'https://36kr.com/p/234567',
                'tags': json.dumps(['二次元文化', '早期投资']),
                'keyword_matches': json.dumps(['二次元文化', '早期投资']),
                'match_score': 16
            },
            {
                'company_name': 'DeepAgent AI',
                'funding_round': '种子轮',
                'amount': '100万美元',
                'amount_usd': 1000000,
                'currency': 'USD',
                'funding_date': '2026-01-20',
                'investors': json.dumps(['MiraclePlus', '红杉种子']),
                'description': '构建企业级AI Agent平台，自动化复杂业务流程。',
                'source_url': 'https://36kr.com/p/345678',
                'tags': json.dumps(['人工智能', '孵化器', '早期投资']),
                'keyword_matches': json.dumps(['人工智能', '孵化器', '早期投资']),
                'match_score': 28
            },
            {
                'company_name': '大模型科技',
                'funding_round': 'Pre-A轮',
                'amount': '数千万人民币',
                'amount_usd': 5000000,
                'currency': 'CNY',
                'funding_date': '2026-01-15',
                'investors': json.dumps(['源码资本', '真格基金']),
                'description': '垂直领域大模型研发，专注金融场景应用。',
                'source_url': 'https://36kr.com/p/456789',
                'tags': json.dumps(['人工智能', '早期投资']),
                'keyword_matches': json.dumps(['人工智能', '早期投资']),
                'match_score': 20
            },
            {
                'company_name': 'Cosplay Gear',
                'funding_round': '天使轮',
                'amount': '300万人民币',
                'amount_usd': 450000,
                'currency': 'CNY',
                'funding_date': '2026-01-10',
                'investors': json.dumps(['某动漫产业基金']),
                'description': 'Cosplay道具定制与租赁平台。',
                'source_url': 'https://36kr.com/p/567890',
                'tags': json.dumps(['二次元文化', '早期投资']),
                'keyword_matches': json.dumps(['二次元文化', '早期投资']),
                'match_score': 16
            },
            {
                'company_name': 'AI Coding',
                'funding_round': 'A轮',
                'amount': '2000万美元',
                'amount_usd': 20000000,
                'currency': 'USD',
                'funding_date': '2026-01-05',
                'investors': json.dumps(['GGV', 'MiraclePlus']),
                'description': 'AI编程助手，提升开发者效率。',
                'source_url': 'https://36kr.com/p/678901',
                'tags': json.dumps(['人工智能', '孵化器', '早期投资']),
                'keyword_matches': json.dumps(['人工智能', '孵化器', '早期投资']),
                'match_score': 28
            },
        ]
        
        events = []
        for data in sample_events:
            event = FundingEvent(
                company_name=data['company_name'],
                funding_round=data['funding_round'],
                amount=data['amount'],
                amount_usd=data['amount_usd'],
                currency=data['currency'],
                funding_date=data['funding_date'],
                investors=data['investors'],
                description=data['description'],
                source_url=data['source_url'],
                source_platform=self.source_name,
                tags=data['tags'],
                keyword_matches=data['keyword_matches'],
                match_score=data['match_score']
            )
            events.append(event)
        
        return events


# ============ 主程序 ============

def run_tracker(use_mock: bool = False, days: int = 30):
    """
    运行投资事件监测
    
    Args:
        use_mock: 是否使用模拟数据
        days: 采集多少天内的数据
    """
    logger.info("=" * 50)
    logger.info("Investment Tracker Started")
    logger.info("=" * 50)
    
    # 初始化数据库
    db = Database()
    
    all_events = []
    
    # 1. 尝试 RSS 采集
    if not use_mock:
        logger.info("Fetching data from 36Kr RSS...")
        rss_crawler = Kr36RssCrawler()
        rss_content = rss_crawler.fetch_rss()
        
        if rss_content:
            rss_events = rss_crawler.parse(rss_content)
            logger.info(f"RSS parsed: {len(rss_events)} events found")
            all_events.extend(rss_events)
        else:
            logger.warning("RSS fetch failed, falling back to mock data")
            use_mock = True
    
    # 2. 使用模拟数据 (用于演示)
    if use_mock:
        logger.info("Generating sample data...")
        mock_crawler = MockDataCrawler()
        mock_events = mock_crawler.generate_sample_data()
        logger.info(f"Generated {len(mock_events)} sample events")
        all_events.extend(mock_events)
    
    # 3. 插入数据库
    inserted_count = 0
    for event in all_events:
        if db.insert_event(event):
            inserted_count += 1
    
    logger.info(f"Total events: {len(all_events)}, Inserted: {inserted_count}")
    
    # 4. 输出统计
    stats = db.get_stats()
    logger.info("-" * 50)
    logger.info("Database Statistics:")
    logger.info(f"  Total events: {stats['total_events']}")
    logger.info(f"  Recent 30d: {stats['recent_30d']}")
    logger.info(f"  High priority: {stats['high_priority']}")
    logger.info(f"  By platform: {stats['by_platform']}")
    
    # 5. 导出最近的高优先级事件
    recent_events = db.get_recent_events(days=days, min_score=10)
    logger.info("-" * 50)
    logger.info(f"Recent high-priority events (score>=10, {days}d):")
    for event in recent_events[:10]:
        logger.info(f"  [{event['match_score']}] {event['company_name']} - {event['funding_round']} ({event['funding_date']})")
    
    db.close()
    logger.info("=" * 50)
    logger.info("Investment Tracker Completed")
    logger.info("=" * 50)
    
    return stats


def export_to_json(output_path: str = None, days: int = 30):
    """导出数据到 JSON 文件"""
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'research', 
            'investment', 
            'sample-data',
            f'funding_events_{datetime.now().strftime("%Y%m%d")}.json'
        )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    db = Database()
    events = db.get_recent_events(days=days, min_score=0)
    db.close()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Exported {len(events)} events to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Investment Ecosystem Intelligence Tracker')
    parser.add_argument('--mock', action='store_true', help='Use mock data for testing')
    parser.add_argument('--days', type=int, default=30, help='Number of days to track')
    parser.add_argument('--export', action='store_true', help='Export data to JSON')
    parser.add_argument('--output', type=str, help='Output file path for export')
    
    args = parser.parse_args()
    
    # 运行采集
    stats = run_tracker(use_mock=args.mock, days=args.days)
    
    # 导出数据
    if args.export:
        export_path = export_to_json(args.output, args.days)
        print(f"\nData exported to: {export_path}")
    
    # 打印摘要
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total events in database: {stats['total_events']}")
    print(f"Events in last 30 days: {stats['recent_30d']}")
    print(f"High priority events: {stats['high_priority']}")


if __name__ == '__main__':
    main()
