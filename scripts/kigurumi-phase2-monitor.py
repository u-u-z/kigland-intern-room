#!/usr/bin/env python3
"""
Kigurumi Market Intelligence Monitor - Phase 2
持续社区监测运营系统

功能：
1. Telegram 社区数据采集（使用 OpenClaw message API）
2. Web 搜索竞品追踪
3. 用户画像分析
4. 每日报告生成

Author: AI Agent
Phase: 2 (Continuous Monitoring)
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
import logging
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MonitoredMessage:
    """监测到的消息数据结构"""
    id: str
    source: str
    source_type: str  # channel / group / search
    author: str
    content: str
    timestamp: str
    keywords_found: List[str]
    hashtags: List[str]
    urls: List[str]
    media_type: Optional[str]
    sentiment: Optional[str]  # positive / neutral / negative
    message_type: str  # discussion / sale / event / review / other
    collected_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CompetitorIntel:
    """竞品情报数据结构"""
    name: str
    source: str
    mention_date: str
    context: str
    product_type: Optional[str]
    price_range: Optional[str]
    sentiment: str
    urls: List[str]
    collected_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class KigurumiPhase2Monitor:
    """Kigurumi Phase 2 持续监测器"""
    
    # 监测关键词配置 - 扩展版
    KEYWORDS = {
        'primary': [
            'kigurumi', '着ぐるみ', 'キグルミ', 
            'kig', '头壳', 'kiger', '着ぐるみさん'
        ],
        'secondary': [
            'animegao', 'アニメ顔', 'mask', '面具',
            'hadalabo', '肌ラボ', 'bodysuit', '紧身衣'
        ],
        'product': [
            '头壳出售', 'kigurumi sale', '着ぐるみ 販売',
            'mask for sale', 'commission', '委托', '定制',
            '二手', '转让', '求购', 'buy', 'sell', 'trade'
        ],
        'event': [
            'event', '活动', '展会', 'convention',
            'meetup', '聚会', 'cf', 'comiket', '漫展',
            'cosplay event', 'kigurumi meet'
        ],
        'brands': [
            'dollkii', 'nfd', 'niya', 'kigmask',
            'kigurumi-online', 'animegao mall',
            'damegami', 'kigland', 'kigdom',
            'hiyasuya', '魔导', 'kigstudio'
        ]
    }
    
    # 已知 Kigurumi 品牌/工作室（竞品）
    COMPETITORS = {
        '头壳制作工作室': [
            'Dollkii', 'NFD Studio', 'Niya Kigurumi', 
            'KigMask', 'KigLand', 'KigDom', 'Hiyasuya',
            '魔导具工作室', 'KigStudio', 'AniMask'
        ],
        '服装/配件': [
            'Hadalabo', '肌ラボ', 'Kigurumi-Online',
            'Animegao Mall', 'Damegami', 'Kigurumi Shop'
        ],
        '综合平台': [
            'Booth.pm', 'Twitter/X Kigurumi', 
            'Pixiv 着ぐるみ', 'Reddit r/Kigurumi'
        ]
    }
    
    # Telegram 监测源配置
    SOURCES = {
        'channels': [
            {'name': 'Kigurumi World', 'id': '@kigurumi_world', 'language': 'en', 'active': True},
            {'name': 'Animegao Kigurumi', 'id': '@animegao_kigurumi', 'language': 'en', 'active': True},
            {'name': '着ぐるみ情報局', 'id': '@kigurumi_jp_info', 'language': 'jp', 'active': True},
            {'name': 'Kigurumi 中文圈', 'id': '@kigurumi_cn', 'language': 'zh', 'active': True},
            {'name': 'Kigurumi Sale', 'id': '@kigurumi_sale', 'language': 'en', 'active': False},
        ],
        'groups': [
            {'name': 'Kigurumi Fan Club', 'id': '@kigurumifanclub', 'language': 'en', 'active': True},
            {'name': '着ぐるみ好き', 'id': '@kigurumi_suki', 'language': 'jp', 'active': True},
            {'name': 'KIG 头壳交流', 'id': '@kig_head_exchange', 'language': 'zh', 'active': True},
            {'name': 'Kigurumi Buy/Sell', 'id': '@kigurumi_trade', 'language': 'en', 'active': False},
        ]
    }
    
    def __init__(self, base_dir: str = "research/kigurumi"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.data_dir = self.base_dir / "community-data"
        self.reports_dir = self.base_dir / "daily-reports"
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # 存储文件
        self.messages_file = self.data_dir / "messages.jsonl"
        self.competitor_file = self.data_dir / "competitor_intel.jsonl"
        self.stats_file = self.data_dir / "stats.json"
        self.seen_ids_file = self.data_dir / "seen_ids.json"
        
        # 已处理的消息ID
        self.seen_ids: Set[str] = self._load_seen_ids()
        
        # 统计信息
        self.stats = self._load_stats()
        
        # 用户画像数据
        self.user_profiles: Dict[str, Dict] = {}
        
        logger.info(f"Phase 2 Monitor initialized")
        logger.info(f"Base dir: {self.base_dir}")
        logger.info(f"Seen messages: {len(self.seen_ids)}")
    
    def _load_seen_ids(self) -> Set[str]:
        """加载已处理的消息ID"""
        if self.seen_ids_file.exists():
            with open(self.seen_ids_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def _save_seen_ids(self):
        """保存已处理的消息ID"""
        with open(self.seen_ids_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.seen_ids), f, ensure_ascii=False)
    
    def _load_stats(self) -> Dict:
        """加载统计数据"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                # 确保 Phase 2 的新字段存在
                if 'by_message_type' not in stats:
                    stats['by_message_type'] = {}
                return stats
        return {
            'total_collected': 0,
            'by_source': {},
            'by_keyword': {},
            'by_date': {},
            'by_message_type': {},
            'last_run': None
        }
    
    def _save_stats(self):
        """保存统计数据"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def extract_keywords(self, text: str) -> List[str]:
        """从文本中提取匹配的关键词"""
        text_lower = text.lower()
        found = []
        
        for category, keywords in self.KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    found.append(kw)
        
        return list(set(found))
    
    def extract_hashtags(self, text: str) -> List[str]:
        """提取话题标签"""
        return re.findall(r'#[\w\u4e00-\u9fff]+', text)
    
    def extract_urls(self, text: str) -> List[str]:
        """提取URL链接"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def detect_message_type(self, text: str, hashtags: List[str]) -> str:
        """检测消息类型"""
        text_lower = text.lower()
        
        # 交易相关
        sale_keywords = ['出售', '转让', 'sale', 'buy', '求购', '二手', 'price', '价格', '预算', '販売']
        if any(kw in text_lower for kw in sale_keywords):
            return 'sale'
        
        # 活动相关
        event_keywords = ['event', '活动', '展会', 'convention', 'meetup', '聚会', 'comiket', '漫展']
        if any(kw in text_lower for kw in event_keywords):
            return 'event'
        
        # 评测/分享
        review_keywords = ['review', '评测', '测评', '体验', '心得', '推荐']
        if any(kw in text_lower for kw in review_keywords):
            return 'review'
        
        # 技术/制作
        tech_keywords = ['制作', 'diy', '教程', '改造', '喷漆', '化妆', '修复']
        if any(kw in text_lower for kw in tech_keywords):
            return 'technical'
        
        return 'discussion'
    
    def analyze_sentiment(self, text: str) -> str:
        """简单情感分析"""
        positive_words = ['喜欢', 'love', 'amazing', 'great', 'awesome', 'beautiful', 'cute', 
                         '可爱', '赞', '棒', 'perfect', 'wonderful', '感谢', '谢谢']
        negative_words = ['讨厌', 'hate', 'terrible', 'bad', 'awful', 'problem', 'issue',
                         '失望', '差', '贵', '坑', 'scam', 'fraud', '骗']
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def detect_competitors(self, text: str) -> List[Dict]:
        """检测竞品提及"""
        mentions = []
        text_lower = text.lower()
        
        for category, brands in self.COMPETITORS.items():
            for brand in brands:
                if brand.lower() in text_lower:
                    # 提取上下文
                    idx = text_lower.find(brand.lower())
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(brand) + 50)
                    context = text[start:end]
                    
                    mentions.append({
                        'brand': brand,
                        'category': category,
                        'context': context,
                        'sentiment': self.analyze_sentiment(text)
                    })
        
        return mentions
    
    def generate_message_id(self, source: str, content: str, timestamp: str) -> str:
        """生成唯一消息ID"""
        data = f"{source}:{content[:100]}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def process_message(self, source: str, source_type: str, 
                       author: str, content: str, 
                       timestamp: str, media_type: Optional[str] = None) -> Optional[MonitoredMessage]:
        """处理单条消息"""
        
        msg_id = self.generate_message_id(source, content, timestamp)
        
        if msg_id in self.seen_ids:
            return None
        
        keywords_found = self.extract_keywords(content)
        hashtags = self.extract_hashtags(content)
        urls = self.extract_urls(content)
        message_type = self.detect_message_type(content, hashtags)
        sentiment = self.analyze_sentiment(content)
        
        msg = MonitoredMessage(
            id=msg_id,
            source=source,
            source_type=source_type,
            author=author,
            content=content,
            timestamp=timestamp,
            keywords_found=keywords_found,
            hashtags=hashtags,
            urls=urls,
            media_type=media_type,
            sentiment=sentiment,
            message_type=message_type,
            collected_at=datetime.now().isoformat()
        )
        
        return msg
    
    def save_message(self, msg: MonitoredMessage):
        """保存消息到文件"""
        with open(self.messages_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + '\n')
        
        self.seen_ids.add(msg.id)
        self._update_stats(msg)
    
    def save_competitor_intel(self, intel: CompetitorIntel):
        """保存竞品情报"""
        with open(self.competitor_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(intel.to_dict(), ensure_ascii=False) + '\n')
    
    def _update_stats(self, msg: MonitoredMessage):
        """更新统计数据"""
        self.stats['total_collected'] += 1
        
        source = msg.source
        self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
        
        for kw in msg.keywords_found:
            self.stats['by_keyword'][kw] = self.stats['by_keyword'].get(kw, 0) + 1
        
        date = msg.collected_at[:10]
        self.stats['by_date'][date] = self.stats['by_date'].get(date, 0) + 1
        
        msg_type = msg.message_type
        self.stats['by_message_type'][msg_type] = self.stats['by_message_type'].get(msg_type, 0) + 1
        
        self.stats['last_run'] = datetime.now().isoformat()
    
    def load_messages(self, days: int = 30) -> List[Dict]:
        """加载指定天数内的消息"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        messages = []
        
        if self.messages_file.exists():
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        if msg['collected_at'] > cutoff:
                            messages.append(msg)
                    except:
                        continue
        
        return messages
    
    def analyze_user_personas(self, messages: List[Dict]) -> Dict[str, Any]:
        """分析用户画像"""
        user_data = defaultdict(lambda: {
            'message_count': 0,
            'sources': set(),
            'keywords': Counter(),
            'message_types': Counter(),
            'languages': Counter(),
            'avg_message_length': 0,
            'total_length': 0
        })
        
        for msg in messages:
            author = msg.get('author', 'unknown')
            user_data[author]['message_count'] += 1
            user_data[author]['sources'].add(msg.get('source', 'unknown'))
            user_data[author]['keywords'].update(msg.get('keywords_found', []))
            user_data[author]['message_types'].update([msg.get('message_type', 'unknown')])
            
            content = msg.get('content', '')
            user_data[author]['total_length'] += len(content)
            
            # 简单语言检测
            if any('\u4e00' <= c <= '\u9fff' for c in content):
                user_data[author]['languages']['zh'] += 1
            elif any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in content):
                user_data[author]['languages']['jp'] += 1
            else:
                user_data[author]['languages']['en'] += 1
        
        # 计算平均值并转换集合
        for author, data in user_data.items():
            if data['message_count'] > 0:
                data['avg_message_length'] = data['total_length'] // data['message_count']
            data['sources'] = list(data['sources'])
        
        # 分类用户类型
        personas = {
            'enthusiast': [],  # 爱好者 - 活跃讨论
            'buyer': [],       # 买家 - 求购/咨询
            'seller': [],      # 卖家 - 出售/推广
            'creator': [],     # 创作者 - 制作分享
            'lurker': []       # 潜水者 - 低活跃度
        }
        
        for author, data in user_data.items():
            if data['message_count'] >= 5:
                if 'sale' in data['message_types']:
                    personas['seller'].append(author)
                elif data['keywords']['头壳'] + data['keywords']['kigurumi'] > 5:
                    personas['enthusiast'].append(author)
                else:
                    personas['creator'].append(author)
            elif data['message_count'] >= 2:
                personas['buyer'].append(author)
            else:
                personas['lurker'].append(author)
        
        return {
            'user_details': dict(user_data),
            'personas': personas,
            'total_users': len(user_data),
            'active_users': len([u for u in user_data.values() if u['message_count'] >= 3])
        }
    
    def analyze_market_trends(self, messages: List[Dict]) -> Dict[str, Any]:
        """分析市场趋势"""
        # 按日期聚合
        daily_data = defaultdict(lambda: {
            'count': 0,
            'keywords': Counter(),
            'types': Counter(),
            'sentiment': Counter()
        })
        
        for msg in messages:
            date = msg.get('collected_at', '')[:10]
            daily_data[date]['count'] += 1
            daily_data[date]['keywords'].update(msg.get('keywords_found', []))
            daily_data[date]['types'].update([msg.get('message_type', 'unknown')])
            daily_data[date]['sentiment'].update([msg.get('sentiment', 'neutral')])
        
        # 热门话题
        all_keywords = Counter()
        for msg in messages:
            all_keywords.update(msg.get('keywords_found', []))
        
        # 交易趋势
        sale_messages = [m for m in messages if m.get('message_type') == 'sale']
        
        return {
            'daily_activity': dict(daily_data),
            'top_keywords': dict(all_keywords.most_common(20)),
            'message_type_distribution': dict(Counter(m.get('message_type', 'unknown') for m in messages)),
            'sentiment_distribution': dict(Counter(m.get('sentiment', 'neutral') for m in messages)),
            'sale_activity': len(sale_messages),
            'event_mentions': len([m for m in messages if m.get('message_type') == 'event'])
        }
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日监测报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 加载今日和近期数据
        today_messages = [m for m in self.load_messages(days=1) 
                         if m.get('collected_at', '').startswith(today)]
        week_messages = self.load_messages(days=7)
        
        # 用户画像分析
        user_analysis = self.analyze_user_personas(week_messages)
        
        # 市场趋势分析
        market_trends = self.analyze_market_trends(week_messages)
        
        report = {
            'report_date': today,
            'generated_at': datetime.now().isoformat(),
            'period': 'daily',
            'summary': {
                'new_messages_today': len(today_messages),
                'total_messages_week': len(week_messages),
                'active_sources': len(set(m.get('source') for m in today_messages)),
                'active_users': len(set(m.get('author') for m in today_messages))
            },
            'activity': {
                'by_hour': self._aggregate_by_hour(today_messages),
                'by_source': dict(Counter(m.get('source') for m in today_messages)),
                'by_type': dict(Counter(m.get('message_type') for m in today_messages))
            },
            'content_analysis': {
                'top_keywords': market_trends['top_keywords'],
                'trending_hashtags': self._extract_trending_hashtags(today_messages),
                'hot_topics': self._identify_hot_topics(today_messages)
            },
            'user_personas': user_analysis['personas'],
            'market_trends': {
                'sentiment': market_trends['sentiment_distribution'],
                'sale_activity': market_trends['sale_activity'],
                'event_mentions': market_trends['event_mentions']
            }
        }
        
        # 保存报告
        report_file = self.reports_dir / f"report_{today}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 同时生成 Markdown 版本便于阅读
        self._generate_markdown_report(report, today)
        
        logger.info(f"Daily report generated: {report_file}")
        return report
    
    def _aggregate_by_hour(self, messages: List[Dict]) -> Dict[str, int]:
        """按小时聚合消息"""
        hours = defaultdict(int)
        for msg in messages:
            try:
                hour = msg.get('collected_at', '')[11:13]
                if hour:
                    hours[hour] += 1
            except:
                continue
        return dict(hours)
    
    def _extract_trending_hashtags(self, messages: List[Dict]) -> List[Dict]:
        """提取热门标签"""
        hashtags = Counter()
        for msg in messages:
            hashtags.update(msg.get('hashtags', []))
        return [{'tag': tag, 'count': count} for tag, count in hashtags.most_common(10)]
    
    def _identify_hot_topics(self, messages: List[Dict]) -> List[str]:
        """识别热门话题"""
        # 基于关键词组合识别话题
        topics = []
        
        sale_msgs = [m for m in messages if m.get('message_type') == 'sale']
        if len(sale_msgs) >= 2:
            topics.append(f"交易讨论 ({len(sale_msgs)} 条)")
        
        event_msgs = [m for m in messages if m.get('message_type') == 'event']
        if len(event_msgs) >= 1:
            topics.append(f"活动信息 ({len(event_msgs)} 条)")
        
        review_msgs = [m for m in messages if m.get('message_type') == 'review']
        if len(review_msgs) >= 1:
            topics.append(f"评测分享 ({len(review_msgs)} 条)")
        
        return topics
    
    def _generate_markdown_report(self, report: Dict, date: str):
        """生成 Markdown 格式报告"""
        md_content = f"""# Kigurumi 社区监测日报 - {date}

> 生成时间: {report['generated_at']}

## 📊 数据概览

| 指标 | 数值 |
|------|------|
| 今日新消息 | {report['summary']['new_messages_today']} |
| 本周总消息 | {report['summary']['total_messages_week']} |
| 活跃来源 | {report['summary']['active_sources']} |
| 活跃用户 | {report['summary']['active_users']} |

## 📈 活跃度分析

### 消息类型分布
"""
        
        for msg_type, count in report['activity']['by_type'].items():
            md_content += f"- {msg_type}: {count}\n"
        
        md_content += "\n### 活跃来源\n"
        for source, count in report['activity']['by_source'].items():
            md_content += f"- {source}: {count}\n"
        
        md_content += "\n## 🔥 热门内容\n\n### 热门关键词\n"
        for kw, count in list(report['content_analysis']['top_keywords'].items())[:10]:
            md_content += f"- `{kw}`: {count} 次\n"
        
        md_content += "\n### 热门话题\n"
        for topic in report['content_analysis']['hot_topics']:
            md_content += f"- {topic}\n"
        
        md_content += "\n## 👥 用户画像\n"
        for persona_type, users in report['user_personas'].items():
            md_content += f"\n### {persona_type} ({len(users)} 人)\n"
            for user in users[:5]:
                md_content += f"- {user}\n"
            if len(users) > 5:
                md_content += f"- ... 等共 {len(users)} 人\n"
        
        md_content += f"""
## 💹 市场趋势

- 整体情感倾向: {report['market_trends']['sentiment']}
- 交易活跃度: {report['market_trends']['sale_activity']} 条相关讨论
- 活动提及: {report['market_trends']['event_mentions']} 次

---
*本报告由 Kigurumi Market Intelligence Phase 2 系统自动生成*
"""
        
        md_file = self.reports_dir / f"report_{date}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Markdown report generated: {md_file}")
    
    def run_monitoring_cycle(self, messages: List[Dict]) -> List[MonitoredMessage]:
        """执行一轮监测"""
        new_messages = []
        
        for raw_msg in messages:
            msg = self.process_message(
                source=raw_msg.get('source', 'unknown'),
                source_type=raw_msg.get('source_type', 'channel'),
                author=raw_msg.get('author', 'unknown'),
                content=raw_msg.get('content', ''),
                timestamp=raw_msg.get('timestamp', datetime.now().isoformat()),
                media_type=raw_msg.get('media_type')
            )
            
            if msg:
                self.save_message(msg)
                new_messages.append(msg)
                
                # 检测竞品提及
                competitors = self.detect_competitors(msg.content)
                for comp in competitors:
                    intel = CompetitorIntel(
                        name=comp['brand'],
                        source=msg.source,
                        mention_date=msg.timestamp[:10],
                        context=comp['context'],
                        product_type=None,
                        price_range=None,
                        sentiment=comp['sentiment'],
                        urls=msg.urls,
                        collected_at=datetime.now().isoformat()
                    )
                    self.save_competitor_intel(intel)
        
        self._save_seen_ids()
        self._save_stats()
        
        logger.info(f"Monitoring cycle complete. New messages: {len(new_messages)}")
        return new_messages


def main():
    """主函数 - Phase 2 监测入口"""
    
    monitor = KigurumiPhase2Monitor()
    
    # 示例：处理一批模拟数据（实际运行时替换为真实数据）
    sample_messages = [
        {
            'source': 'Kigurumi World',
            'source_type': 'channel',
            'author': 'kig_fan_01',
            'content': 'Just received my new Dollkii mask! The quality is amazing and the hadalabo skin looks so natural. #kigurumi #dollkii',
            'timestamp': datetime.now().isoformat(),
            'media_type': 'photo'
        },
        {
            'source': '着ぐるみ情報局',
            'source_type': 'channel',
            'author': 'jp_editor',
            'content': '今週末のコミケで着ぐるみ展示があります。NFD Studioの新作も展示される予定です。ぜひお越しください！',
            'timestamp': datetime.now().isoformat(),
        },
        {
            'source': 'KIG 头壳交流',
            'source_type': 'group',
            'author': 'user_cn_123',
            'content': '有人知道KigLand的定制价格吗？想做一个萌系角色的头壳，预算大概8000-12000，求推荐靠谱的工作室',
            'timestamp': datetime.now().isoformat(),
        },
        {
            'source': 'Kigurumi Fan Club',
            'source_type': 'group',
            'author': 'kig_collector',
            'content': 'Selling my Niya kigurumi set, barely used. Includes mask, bodysuit and accessories. DM for price. #forsale #kigurumi',
            'timestamp': datetime.now().isoformat(),
        }
    ]
    
    # 执行监测
    new_msgs = monitor.run_monitoring_cycle(sample_messages)
    
    # 生成报告
    report = monitor.generate_daily_report()
    
    print("\n" + "="*60)
    print("Kigurumi Phase 2 Monitor - Run Complete")
    print("="*60)
    print(f"New messages collected: {len(new_msgs)}")
    print(f"Total messages in database: {monitor.stats['total_collected']}")
    print(f"Daily report saved to: {monitor.reports_dir}/report_{datetime.now().strftime('%Y-%m-%d')}.md")
    print(f"\nTop keywords: {list(report['content_analysis']['top_keywords'].keys())[:5]}")
    print(f"User personas identified: {sum(len(v) for v in report['user_personas'].values())} users")
    
    return monitor, report


if __name__ == "__main__":
    monitor, report = main()
