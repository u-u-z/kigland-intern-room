#!/usr/bin/env python3
"""
Kigurumi Phase 2 持续监测运行器
Continuous Monitoring Runner

功能：
1. 定期执行社区数据采集
2. 生成每日报告
3. 更新竞品追踪
4. 整合多数据源

运行模式:
- 单次模式: python kigurumi-continuous-monitor.py --once
- 持续模式: python kigurumi-continuous-monitor.py --daemon
"""

import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# 导入监测模块 (处理带连字符的文件名)
sys.path.insert(0, '/home/remi/.openclaw/workspace/scripts')
import importlib.util

# 动态加载 phase2 monitor
spec = importlib.util.spec_from_file_location("phase2_monitor", "/home/remi/.openclaw/workspace/scripts/kigurumi-phase2-monitor.py")
phase2_module = importlib.util.module_from_spec(spec)
sys.modules["phase2_monitor"] = phase2_module
spec.loader.exec_module(phase2_module)
KigurumiPhase2Monitor = phase2_module.KigurumiPhase2Monitor

# 动态加载 competitor tracker
spec2 = importlib.util.spec_from_file_location("competitor_tracker", "/home/remi/.openclaw/workspace/scripts/kigurumi-competitor-tracker.py")
tracker_module = importlib.util.module_from_spec(spec2)
sys.modules["competitor_tracker"] = tracker_module
spec2.loader.exec_module(tracker_module)
CompetitorWebTracker = tracker_module.CompetitorWebTracker


class ContinuousMonitor:
    """持续监测控制器"""
    
    def __init__(self):
        self.monitor = KigurumiPhase2Monitor()
        self.tracker = CompetitorWebTracker()
        self.run_count = 0
        self.last_report_date = None
    
    def collect_telegram_data(self) -> int:
        """收集 Telegram 数据"""
        # 这里应该调用 Telegram API 获取真实数据
        # 目前使用模拟数据演示框架
        
        sample_messages = [
            {
                'source': 'Kigurumi World',
                'source_type': 'channel',
                'author': f'user_{self.run_count}_1',
                'content': f'Looking for kigurumi mask recommendations. Budget around $500. #kigurumi #help',
                'timestamp': datetime.now().isoformat(),
            },
            {
                'source': '着ぐるみ情報局',
                'source_type': 'channel',
                'author': f'jp_user_{self.run_count}',
                'content': f'新作の頭壳が入荷しました！今週のイベント情報も更新しています。',
                'timestamp': datetime.now().isoformat(),
            },
            {
                'source': 'KIG 头壳交流',
                'source_type': 'group',
                'author': f'cn_user_{self.run_count}',
                'content': f'有人用过 KigDom 的新款吗？质量怎么样？求真实反馈',
                'timestamp': datetime.now().isoformat(),
            }
        ]
        
        new_msgs = self.monitor.run_monitoring_cycle(sample_messages)
        return len(new_msgs)
    
    def generate_daily_report_if_needed(self):
        """按需生成每日报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if self.last_report_date != today:
            print(f"[{datetime.now()}] 生成每日报告...")
            report = self.monitor.generate_daily_report()
            self.last_report_date = today
            print(f"  - 今日新消息: {report['summary']['new_messages_today']}")
            print(f"  - 活跃用户: {report['summary']['active_users']}")
            return report
        return None
    
    def update_competitor_intel(self):
        """更新竞品情报"""
        print(f"[{datetime.now()}] 更新竞品情报...")
        analysis = self.tracker.analyze_brand_mentions()
        print(f"  - 检测到 {analysis['total_mentions']} 条竞品提及")
        return analysis
    
    def run_single_cycle(self):
        """执行单次监测周期"""
        self.run_count += 1
        print(f"\n{'='*60}")
        print(f"监测周期 #{self.run_count} - {datetime.now()}")
        print('='*60)
        
        # 1. 收集数据
        new_count = self.collect_telegram_data()
        print(f"[1/3] 数据采集: {new_count} 条新消息")
        
        # 2. 生成报告
        report = self.generate_daily_report_if_needed()
        print(f"[2/3] 报告生成: {'已生成' if report else '跳过(今日已生成)'}")
        
        # 3. 竞品追踪
        intel = self.update_competitor_intel()
        print(f"[3/3] 竞品追踪: {intel['total_mentions']} 条提及")
        
        print(f"周期完成，累计收集: {self.monitor.stats['total_collected']} 条消息")
        return True
    
    def run_continuous(self, interval_minutes: int = 60):
        """持续运行模式"""
        print(f"\n{'='*60}")
        print("Kigurumi Phase 2 - 持续监测模式")
        print(f"监测间隔: {interval_minutes} 分钟")
        print(f"数据目录: {self.monitor.base_dir}")
        print('='*60 + '\n')
        
        try:
            while True:
                self.run_single_cycle()
                
                # 等待下一次监测
                print(f"\n等待 {interval_minutes} 分钟后进行下一次监测...")
                print(f"(按 Ctrl+C 停止)\n")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n监测已手动停止")
            self._save_final_state()
    
    def _save_final_state(self):
        """保存最终状态"""
        state = {
            'total_runs': self.run_count,
            'total_messages': self.monitor.stats['total_collected'],
            'last_run': datetime.now().isoformat(),
            'last_report_date': self.last_report_date
        }
        
        state_file = self.monitor.base_dir / 'monitor_state.json'
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print(f"状态已保存: {state_file}")


def main():
    parser = argparse.ArgumentParser(description='Kigurumi Phase 2 持续监测')
    parser.add_argument('--once', action='store_true', help='单次运行模式')
    parser.add_argument('--daemon', action='store_true', help='持续运行模式')
    parser.add_argument('--interval', type=int, default=60, help='监测间隔(分钟),默认60')
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor()
    
    if args.once:
        # 单次模式
        monitor.run_single_cycle()
    elif args.daemon:
        # 持续模式
        monitor.run_continuous(args.interval)
    else:
        # 默认单次模式
        monitor.run_single_cycle()
        print("\n提示: 使用 --daemon 参数启动持续监测模式")


if __name__ == "__main__":
    main()
