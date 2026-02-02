# Kigurumi Market Intelligence - Phase 1

## 项目概述
Kigurumi（着ぐるみ）市场情报项目 - 第一阶段：Telegram 社区监测

## 文件结构

```
research/kigurumi/
├── telegram-sources.md          # Telegram 社区资源清单
├── community-data/
│   ├── messages.jsonl           # 抓取的消息数据（JSON Lines 格式）
│   ├── stats.json               # 统计数据
│   └── seen_ids.json            # 已处理消息ID（去重）
└── README.md                    # 本文件

scripts/
└── kigurumi-monitor.py          # 监测脚本
```

## 快速开始

### 1. 运行监测脚本

```bash
cd /home/remi/.openclaw/workspace
python3 scripts/kigurumi-monitor.py
```

### 2. 查看数据

```bash
# 查看消息数据
cat research/kigurumi/community-data/messages.jsonl | jq .

# 查看统计
cat research/kigurumi/community-data/stats.json | jq .
```

## 数据格式

### 消息记录 (messages.jsonl)

```json
{
  "id": "消息唯一ID",
  "source": "频道/群组名",
  "source_type": "channel|group",
  "author": "发布者",
  "content": "消息内容",
  "timestamp": "发布时间",
  "keywords_found": ["匹配的关键词"],
  "hashtags": ["#话题标签"],
  "urls": ["链接"],
  "media_type": "photo|video|document|null",
  "collected_at": "采集时间"
}
```

### 统计数据 (stats.json)

```json
{
  "total_collected": 总消息数,
  "by_source": { "来源": 数量 },
  "by_keyword": { "关键词": 出现次数 },
  "by_date": { "日期": 数量 },
  "last_run": "最后运行时间"
}
```

## 监测关键词

### 核心关键词
- `kigurumi` / `着ぐるみ` / `キグルミ` - 主关键词
- `kig` / `kiger` - 简称
- `头壳` - 中文社区

### 扩展关键词
- `animegao` / `アニメ顔` - 动画脸
- `mask` / `面具` - 面具
- `hadalabo` / `肌ラボ` - 相关品牌
- `bodysuit` - 紧身衣

### 场景关键词
- `sale` / `出售` / `转让` / `販売` - 交易
- `event` / `活动` / `展会` / `convention` - 活动

## 扩展监测源

### Telegram 搜索方法
1. 在 Telegram 搜索栏输入关键词：`Kigurumi`, `着ぐるみ`
2. 切换"频道"、"群组"标签筛选
3. 访问 https://tgstat.com/ 进行高级搜索

### Discord 服务器
- 使用 https://disboard.org/ 搜索 "Kigurumi"
- 查找公开邀请链接

### 其他数据源
- Twitter/X hashtag 监测
- Reddit r/Kigurumi
- Pixiv 标签: 着ぐるみ

## 技术说明

### 当前实现
- ✅ 本地数据处理框架
- ✅ 关键词提取和匹配
- ✅ 数据存储（JSON Lines）
- ✅ 统计分析
- ✅ 去重机制

### 需要 Telegram API 集成
当前脚本使用模拟数据进行演示。实际 Telegram 监测需要：

**方案 A: Bot API（简单，仅限公开频道）**
```python
# 需要: pip install python-telegram-bot
# 通过 @BotFather 获取 Token
```

**方案 B: MTProto API（Telethon，更强大）**
```python
# 需要: pip install telethon
# 需要手机号验证
# 可访问公开和私有频道
```

### 推荐的实时监测架构
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Telegram   │────▶│   Monitor   │────▶│   JSONL     │
│   Source    │     │   Script    │     │   Storage   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                       ┌────────────────────────┘
                       ▼
              ┌─────────────────┐
              │  Analytics &    │
              │  Reporting      │
              └─────────────────┘
```

## 隐私与合规

- ✅ 仅监测公开可访问的频道/群组
- ✅ 不涉及私人消息或受限内容
- ✅ 遵守 Telegram 服务条款
- ✅ 数据仅用于市场情报分析

## 下一阶段计划

1. 验证并补充 Telegram 频道清单
2. 集成 Telegram API 进行实时抓取
3. 添加情感分析功能
4. 构建可视化仪表板
5. 设置定时任务（Cron）

---

*生成时间: 2026-02-02*
*项目: Kigurumi Market Intelligence #10*
