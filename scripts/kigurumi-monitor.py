#!/usr/bin/env python3
"""
Kigurumi Market Intelligence Monitor
Phase 1: Telegram Community Monitoring

功能：
- 监测 Kigurumi 相关 Telegram 频道和群组
- 关键词过滤和提取
- 数据存储和分析

注意：仅监测公开可访问的频道/群组
"""

import json
import os
import re
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import logging

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
    source: str  # 频道/群组名
    source_type: str  # channel / group
    author: str
    content: str
    timestamp: str
    keywords_found: List[str]
    hashtags: List[str]
    urls: List[str]
    media_type: Optional[str]  # photo, video, document, None
    collected_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class KigurumiMonitor:
    """Kigurumi 社区监测器"""
    
    # 监测关键词配置
    KEYWORDS = {
        'primary': [
            'kigurumi', '着ぐるみ', 'キグルミ', 
            'kig', '头壳', 'kiger'
        ],
        'secondary': [
            'animegao', 'アニメ顔', 'mask', '面具',
            'hadalabo', '肌ラボ', 'bodysuit'
        ],
        'product': [
            '头壳出售', 'kigurumi sale', '着ぐるみ 販売',
            'mask for sale', 'commission', '委托'
        ],
        'event': [
            'event', '活动', '展会', 'convention',
            'meetup', '聚会', 'cf', 'comiket'
        ]
    }
    
    # 预定义数据源（需要验证和补充）
    SOURCES = {
        'channels': [
            # 格式: {'name': '频道名', 'id': '@username', 'language': 'en/jp/zh'}
            {'name': 'Kigurumi World', 'id': '@kigurumi_world', 'language': 'en'},
            {'name': 'Animegao Kigurumi', 'id': '@animegao_kigurumi', 'language': 'en'},
            {'name': '着ぐるみ情報局', 'id': '@kigurumi_jp_info', 'language': 'jp'},
            {'name': 'Kigurumi 中文圈', 'id': '@kigurumi_cn', 'language': 'zh'},
        ],
        'groups': [
            {'name': 'Kigurumi Fan Club', 'id': '@kigurumifanclub', 'language': 'en'},
            {'name': '着ぐるみ好き', 'id': '@kigurumi_suki', 'language': 'jp'},
            {'name': 'KIG 头壳交流', 'id': '@kig_head_exchange', 'language': 'zh'},
        ]
    }
    
    def __init__(self, data_dir: str = "research/kigurumi/community-data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储文件
        self.messages_file = self.data_dir / "messages.jsonl"
        self.stats_file = self.data_dir / "stats.json"
        self.seen_ids_file = self.data_dir / "seen_ids.json"
        
        # 已处理的消息ID（去重）
        self.seen_ids: Set[str] = self._load_seen_ids()
        
        # 统计信息
        self.stats = self._load_stats()
        
        logger.info(f"Monitor initialized. Data dir: {self.data_dir}")
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
                return json.load(f)
        return {
            'total_collected': 0,
            'by_source': {},
            'by_keyword': {},
            'by_date': {},
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
        return re.findall(r'#\w+', text)
    
    def extract_urls(self, text: str) -> List[str]:
        """提取URL链接"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
    
    def generate_message_id(self, source: str, content: str, timestamp: str) -> str:
        """生成唯一消息ID"""
        data = f"{source}:{content[:100]}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def process_message(self, source: str, source_type: str, 
                       author: str, content: str, 
                       timestamp: str, media_type: Optional[str] = None) -> Optional[MonitoredMessage]:
        """处理单条消息"""
        
        # 生成消息ID
        msg_id = self.generate_message_id(source, content, timestamp)
        
        # 去重检查
        if msg_id in self.seen_ids:
            return None
        
        # 关键词匹配
        keywords_found = self.extract_keywords(content)
        
        # 如果没有匹配关键词，可选择是否跳过
        # if not keywords_found:
        #     return None
        
        # 提取元数据
        hashtags = self.extract_hashtags(content)
        urls = self.extract_urls(content)
        
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
            collected_at=datetime.now().isoformat()
        )
        
        return msg
    
    def save_message(self, msg: MonitoredMessage):
        """保存消息到文件"""
        with open(self.messages_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + '\n')
        
        # 更新已见ID
        self.seen_ids.add(msg.id)
        
        # 更新统计
        self._update_stats(msg)
    
    def _update_stats(self, msg: MonitoredMessage):
        """更新统计数据"""
        self.stats['total_collected'] += 1
        
        # 按来源统计
        source = msg.source
        self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
        
        # 按关键词统计
        for kw in msg.keywords_found:
            self.stats['by_keyword'][kw] = self.stats['by_keyword'].get(kw, 0) + 1
        
        # 按日期统计
        date = msg.collected_at[:10]  # YYYY-MM-DD
        self.stats['by_date'][date] = self.stats['by_date'].get(date, 0) + 1
        
        self.stats['last_run'] = datetime.now().isoformat()
    
    def run_monitoring_cycle(self, messages: List[Dict]):
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
        
        # 保存状态
        self._save_seen_ids()
        self._save_stats()
        
        logger.info(f"Cycle complete. New messages: {len(new_messages)}")
        return new_messages
    
    def get_report(self, days: int = 7) -> Dict:
        """生成监测报告"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        recent_messages = []
        if self.messages_file.exists():
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        msg = json.loads(line.strip())
                        if msg['collected_at'] > cutoff:
                            recent_messages.append(msg)
                    except:
                        continue
        
        return {
            'period_days': days,
            'total_messages': len(recent_messages),
            'unique_sources': len(set(m['source'] for m in recent_messages)),
            'top_keywords': self._get_top_keywords(recent_messages),
            'top_sources': self._get_top_sources(recent_messages),
            'recent_activity': recent_messages[:10]
        }
    
    def _get_top_keywords(self, messages: List[Dict], top_n: int = 10) -> List[Dict]:
        """获取热门关键词"""
        counts = {}
        for msg in messages:
            for kw in msg.get('keywords_found', []):
                counts[kw] = counts.get(kw, 0) + 1
        
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{'keyword': k, 'count': v} for k, v in sorted_items[:top_n]]
    
    def _get_top_sources(self, messages: List[Dict], top_n: int = 10) -> List[Dict]:
        """获取活跃来源"""
        counts = {}
        for msg in messages:
            src = msg.get('source', 'unknown')
            counts[src] = counts.get(src, 0) + 1
        
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{'source': k, 'count': v} for k, v in sorted_items[:top_n]]


class TelegramAPIMonitor(KigurumiMonitor):
    """
    基于 Telegram API 的监测器（需要 API 配置）
    
    使用方法:
    1. 通过 BotFather 创建 Bot，获取 Token
    2. 配置环境变量 TELEGRAM_BOT_TOKEN
    3. 或使用 Telethon 库进行用户账号级别的监测（更强大，但需要手机号验证）
    """
    
    def __init__(self, data_dir: str = "research/kigurumi/community-data"):
        super().__init__(data_dir)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
    def fetch_from_telegram(self, channel_id: str, limit: int = 100) -> List[Dict]:
        """
        从 Telegram 获取消息
        
        注意：这是一个模板方法，实际实现需要：
        - python-telegram-bot 库（Bot API，仅限公开频道）
        - 或 Telethon 库（MTProto API，更强大）
        """
        # 示例返回结构
        return []
    
    def run(self):
        """持续运行监测"""
        logger.info("Starting Telegram monitoring...")
        
        while True:
            try:
                all_messages = []
                
                # 遍历配置的源
                for source in self.SOURCES['channels'] + self.SOURCES['groups']:
                    logger.info(f"Fetching from {source['name']}...")
                    # messages = self.fetch_from_telegram(source['id'])
                    # all_messages.extend(messages)
                
                # 处理消息
                # self.run_monitoring_cycle(all_messages)
                
                logger.info("Cycle complete. Sleeping...")
                time.sleep(300)  # 5分钟间隔
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                time.sleep(60)


def main():
    """主函数 - 演示用法"""
    
    # 初始化监测器
    monitor = KigurumiMonitor()
    
    # 示例：处理模拟数据
    sample_messages = [
        {
            'source': 'Kigurumi World',
            'source_type': 'channel',
            'author': 'admin',
            'content': 'New kigurumi mask available! Check out this hadalabo review #kigurumi #mask',
            'timestamp': datetime.now().isoformat(),
            'media_type': 'photo'
        },
        {
            'source': '着ぐるみ情報局',
            'source_type': 'channel',
            'author': 'editor',
            'content': '今週の着ぐるみイベント情報です。Comiket に参加予定の方はご確認ください。',
            'timestamp': datetime.now().isoformat(),
        },
        {
            'source': 'KIG 头壳交流',
            'source_type': 'group',
            'author': 'user123',
            'content': '有人出售二手头壳吗？预算5000以内，最好是萌系角色',
            'timestamp': datetime.now().isoformat(),
        }
    ]
    
    # 执行监测
    new_msgs = monitor.run_monitoring_cycle(sample_messages)
    
    # 生成报告
    report = monitor.get_report(days=1)
    
    print("\n=== Kigurumi Monitor Report ===")
    print(f"New messages: {len(new_msgs)}")
    print(f"Keywords found: {report['top_keywords']}")
    print(f"Data saved to: {monitor.data_dir}")
    
    return monitor


if __name__ == "__main__":
    monitor = main()
