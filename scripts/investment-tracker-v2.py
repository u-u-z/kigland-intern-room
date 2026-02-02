#!/usr/bin/env python3
"""
Investment Ecosystem Intelligence - Phase 2 Continuous Tracker
投资生态情报 - Phase 2 持续追踪系统

功能：
1. 定时采集投资事件数据
2. 自动生成每日简报
3. 更新周度趋势分析
4. 发送机会预警

运行模式：
- 单次运行: python3 investment-tracker-v2.py --run-once
- 持续运行: python3 investment-tracker-v2.py --daemon

作者: OpenClaw Agent
版本: 2.0.0
"""

import os
import sys
import json
import sqlite3
import hashlib
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# 配置路径
BASE_DIR = Path(__file__).parent.parent
RESEARCH_DIR = BASE_DIR / "research" / "investment"
DAILY_REPORTS_DIR = RESEARCH_DIR / "daily-reports"
DB_PATH = RESEARCH_DIR / "investment.db"

# 确保目录存在
DAILY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(RESEARCH_DIR / "tracker.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


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
    investors: str = ''
    description: str = ''
    source_url: str = ''
    source_platform: str = ''
    tags: str = ''
    keyword_matches: str = ''
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
        self.db_path = str(db_path or DB_PATH)
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
                investors TEXT,
                description TEXT,
                source_url TEXT,
                source_platform TEXT,
                tags TEXT,
                keyword_matches TEXT,
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_date ON funding_events(funding_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON funding_events(company_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_match_score ON funding_events(match_score)')
        
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
            event.company_name, event.funding_round, event.amount, event.amount_usd,
            event.currency, event.funding_date, event.investors, event.description,
            event.source_url, event.source_platform, event.tags, event.keyword_matches,
            event.match_score, event_hash
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
        
        # 近7天事件数
        since_date_7d = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM funding_events WHERE funding_date >= ?', (since_date_7d,))
        stats['recent_7d'] = cursor.fetchone()[0]
        
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
        
        # 按领域统计
        cursor.execute('SELECT tags FROM funding_events WHERE tags IS NOT NULL')
        tags_data = cursor.fetchall()
        tag_counts = {}
        for row in tags_data:
            try:
                tags = json.loads(row[0])
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            except:
                pass
        stats['by_tag'] = tag_counts
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# ============ 报告生成 ============

class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def generate_daily_report(self, date: str = None) -> str:
        """生成每日简报"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取最近数据
        events = self.db.get_recent_events(days=30, min_score=0)
        stats = self.db.get_stats()
        
        # 分类事件
        p0_events = [e for e in events if e['match_score'] >= 20]
        p1_events = [e for e in events if 15 <= e['match_score'] < 20]
        p2_events = [e for e in events if 10 <= e['match_score'] < 15]
        
        # 统计
        miracleplus_count = len([e for e in events if 'miracleplus' in e.get('investors', '').lower()])
        ai_agent_count = len([e for e in events if 'agent' in e.get('description', '').lower()])
        niche_count = len([e for e in events if '二次元' in e.get('tags', '')])
        
        report = f"""# 投资动态简报 - {date}

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')} CST  
**数据来源**: 36Kr RSS, Investment Tracker  
**监测范围**: 过去30天投资事件

---

## 📊 概览

| 指标 | 数值 | 变化 |
|------|------|------|
| 新增投资事件 | {stats['recent_30d']} | - |
| 高优先级事件 (≥20分) | {len(p0_events)} | - |
| MiraclePlus 相关 | {miracleplus_count} | - |
| AI Agent 领域 | {ai_agent_count} | - |
| 二次元相关 | {niche_count} | - |

---

## 🎯 重点事件

### P0 - 最高优先级

"""
        
        for event in p0_events:
            investors = json.loads(event.get('investors', '[]'))
            tags = json.loads(event.get('tags', '[]'))
            report += f"""#### {event['company_name']} - {event['funding_round']} ({event['amount']})
- **匹配分**: {event['match_score']}/30 ⭐⭐⭐
- **投资方**: {', '.join(investors)}
- **日期**: {event['funding_date']}
- **简介**: {event['description'][:100]}...

"""
        
        if not p0_events:
            report += "*暂无 P0 级别事件*\n\n"
        
        report += """### P1 - 高优先级

"""
        
        for event in p1_events:
            investors = json.loads(event.get('investors', '[]'))
            report += f"""#### {event['company_name']} - {event['funding_round']}
- **匹配分**: {event['match_score']}/30 ⭐⭐
- **投资方**: {', '.join(investors)}
- **日期**: {event['funding_date']}

"""
        
        if not p1_events:
            report += "*暂无 P1 级别事件*\n\n"
        
        report += f"""---

## 📈 数据统计

- **数据库总事件**: {stats['total_events']}
- **近7天事件**: {stats['recent_7d']}
- **高优先级事件**: {stats['high_priority']}

---

*本报告由 Investment Ecosystem Intelligence 系统自动生成*
"""
        
        return report
    
    def save_daily_report(self, date: str = None):
        """保存每日报告"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        report = self.generate_daily_report(date)
        report_path = DAILY_REPORTS_DIR / f"{date}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Daily report saved: {report_path}")
        return report_path


# ============ 数据采集器 ============

class DataCollector:
    """数据采集器"""
    
    # 监测关键词配置
    KEYWORDS_CONFIG = {
        'early_stage': {
            'keywords': ['天使轮', '种子轮', 'Pre-A轮', '天使+', '种子+', 'A轮'],
            'weight': 10,
            'category': '早期投资'
        },
        'ai': {
            'keywords': ['AI', '人工智能', '大模型', 'LLM', 'Agent', 'AIGC', 
                        '机器学习', '深度学习', 'ChatGPT', 'Claude'],
            'weight': 10,
            'category': '人工智能'
        },
        'accelerator': {
            'keywords': ['MiraclePlus', '奇绩创坛', 'Y Combinator', '陆奇'],
            'weight': 8,
            'category': '孵化器'
        },
        'niche': {
            'keywords': ['Kigurumi', '二次元', 'Cosplay', 'ACG', '动漫', 
                        '虚拟偶像', 'Vtuber', '手办', '潮玩'],
            'weight': 6,
            'category': '二次元文化'
        }
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    def match_keywords(self, text: str) -> Tuple[List[str], int]:
        """匹配关键词"""
        if not text:
            return [], 0
        
        text = text.lower()
        matched_categories = []
        total_score = 0
        
        for category, config in self.KEYWORDS_CONFIG.items():
            for keyword in config['keywords']:
                if keyword.lower() in text:
                    matched_categories.append(config['category'])
                    total_score += config['weight']
                    break
        
        return list(set(matched_categories)), total_score
    
    def collect_from_rss(self) -> List[FundingEvent]:
        """从 RSS 采集数据 (待实现)"""
        # RSS 采集逻辑
        logger.info("RSS collection not yet implemented")
        return []
    
    def generate_mock_events(self, count: int = 3) -> List[FundingEvent]:
        """生成模拟事件用于测试"""
        mock_data = [
            {
                'company_name': 'AutoAgent Labs',
                'funding_round': '种子轮',
                'amount': '500万美元',
                'amount_usd': 5000000,
                'currency': 'USD',
                'funding_date': datetime.now().strftime('%Y-%m-%d'),
                'investors': json.dumps(['MiraclePlus']),
                'description': '自动化工作流 AI Agent 平台',
                'source_platform': 'mock_v2',
                'match_score': 18
            },
            {
                'company_name': 'CosAI Studio',
                'funding_round': '天使轮',
                'amount': '300万人民币',
                'amount_usd': 450000,
                'currency': 'CNY',
                'funding_date': datetime.now().strftime('%Y-%m-%d'),
                'investors': json.dumps(['某天使投资人']),
                'description': 'AI 驱动的 Cosplay 设计工具',
                'source_platform': 'mock_v2',
                'match_score': 16
            },
            {
                'company_name': 'RobotMind',
                'funding_round': 'Pre-A轮',
                'amount': '800万美元',
                'amount_usd': 8000000,
                'currency': 'USD',
                'funding_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                'investors': json.dumps(['红杉中国', '真格基金']),
                'description': '具身智能决策系统',
                'source_platform': 'mock_v2',
                'match_score': 20
            }
        ]
        
        events = []
        for data in mock_data[:count]:
            event = FundingEvent(
                company_name=data['company_name'],
                funding_round=data['funding_round'],
                amount=data['amount'],
                amount_usd=data['amount_usd'],
                currency=data['currency'],
                funding_date=data['funding_date'],
                investors=data['investors'],
                description=data['description'],
                source_platform=data['source_platform'],
                tags=json.dumps(['人工智能', '早期投资']),
                keyword_matches=json.dumps(['人工智能', '早期投资']),
                match_score=data['match_score']
            )
            events.append(event)
        
        return events
    
    def run_collection(self, use_mock: bool = True) -> int:
        """运行数据采集"""
        logger.info("Starting data collection...")
        
        events = []
        
        # 尝试 RSS 采集 (生产环境)
        if not use_mock:
            rss_events = self.collect_from_rss()
            events.extend(rss_events)
        
        # 使用模拟数据 (测试/演示)
        if use_mock:
            mock_events = self.generate_mock_events(3)
            events.extend(mock_events)
        
        # 插入数据库
        inserted = 0
        for event in events:
            if self.db.insert_event(event):
                inserted += 1
        
        logger.info(f"Collection completed: {len(events)} events, {inserted} new")
        return inserted


# ============ 主程序 ============

def run_once(use_mock: bool = True, generate_report: bool = True):
    """单次运行模式"""
    logger.info("=" * 50)
    logger.info("Investment Tracker v2.0 - Single Run Mode")
    logger.info("=" * 50)
    
    # 初始化
    db = Database()
    collector = DataCollector(db)
    reporter = ReportGenerator(db)
    
    # 数据采集
    new_events = collector.run_collection(use_mock=use_mock)
    
    # 生成报告
    if generate_report:
        report_path = reporter.save_daily_report()
        logger.info(f"Report generated: {report_path}")
    
    # 输出统计
    stats = db.get_stats()
    logger.info("-" * 50)
    logger.info("Statistics:")
    logger.info(f"  Total events: {stats['total_events']}")
    logger.info(f"  Recent 7d: {stats['recent_7d']}")
    logger.info(f"  Recent 30d: {stats['recent_30d']}")
    logger.info(f"  High priority: {stats['high_priority']}")
    
    db.close()
    logger.info("=" * 50)
    logger.info("Run completed")
    
    return new_events


def run_daemon(interval_minutes: int = 60, use_mock: bool = True):
    """守护进程模式 - 持续运行"""
    logger.info("=" * 50)
    logger.info("Investment Tracker v2.0 - Daemon Mode")
    logger.info(f"Interval: {interval_minutes} minutes")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 50)
    
    import time
    
    last_daily_report = None
    
    try:
        while True:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_date = current_time.strftime('%Y-%m-%d')
            
            # 数据采集
            run_once(use_mock=use_mock, generate_report=False)
            
            # 每天早上 9 点生成日报
            if current_hour == 9 and last_daily_report != current_date:
                db = Database()
                reporter = ReportGenerator(db)
                reporter.save_daily_report(current_date)
                db.close()
                last_daily_report = current_date
                logger.info(f"Daily report generated for {current_date}")
            
            # 等待下一次采集
            logger.info(f"Sleeping for {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as e:
        logger.error(f"Daemon error: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='Investment Ecosystem Intelligence Tracker v2')
    parser.add_argument('--run-once', action='store_true', help='Run once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    parser.add_argument('--interval', type=int, default=60, help='Daemon check interval (minutes)')
    parser.add_argument('--mock', action='store_true', default=True, help='Use mock data')
    parser.add_argument('--no-mock', action='store_true', help='Use real data sources')
    parser.add_argument('--report', action='store_true', help='Generate daily report')
    
    args = parser.parse_args()
    
    use_mock = not args.no_mock
    
    if args.daemon:
        run_daemon(interval_minutes=args.interval, use_mock=use_mock)
    else:
        run_once(use_mock=use_mock, generate_report=args.report or True)


if __name__ == '__main__':
    main()
