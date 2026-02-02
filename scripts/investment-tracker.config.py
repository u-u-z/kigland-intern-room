# Investment Tracker Configuration
# 投资监测脚本配置

# 数据库路径 (相对或绝对路径)
DB_PATH = "research/investment/investment.db"

# 请求配置
REQUEST_CONFIG = {
    'timeout': 30,
    'retry_times': 3,
    'retry_delay': 1,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 关键词监测配置
KEYWORDS_CONFIG = {
    'early_stage': {
        'keywords': ['天使轮', '种子轮', 'Pre-A轮', '天使+', '种子+', 'A轮'],
        'weight': 10,
        'category': '早期投资'
    },
    'ai': {
        'keywords': [
            'AI', '人工智能', '大模型', 'LLM', 'Agent', 'AIGC', 
            '机器学习', '深度学习', '神经网络', 'ChatGPT', 'Claude'
        ],
        'weight': 10,
        'category': '人工智能'
    },
    'accelerator': {
        'keywords': ['MiraclePlus', '奇绩创坛', 'Y Combinator', 'YC China', '陆奇'],
        'weight': 8,
        'category': '孵化器'
    },
    'niche': {
        'keywords': [
            'Kigurumi', '二次元', 'Cosplay', 'ACG', '动漫', 
            '虚拟偶像', 'Vtuber', '手办', '潮玩', '盲盒', '谷子'
        ],
        'weight': 6,
        'category': '二次元文化'
    },
    'vc_firms': {
        'keywords': [
            '红杉', 'IDG', '高瓴', '源码资本', '五源资本', 
            'GGV', '真格基金', '金沙江', '经纬中国', '启明创投'
        ],
        'weight': 5,
        'category': '知名机构'
    }
}

# 数据源配置
SOURCES = {
    '36kr_rss': {
        'enabled': True,
        'urls': [
            'https://36kr.com/feed',
            'https://36kr.com/feed-newsflash',
            'https://rsshub.app/36kr/newsflashes'
        ]
    },
    '36kr_api': {
        'enabled': False,  # 需要验证码绕过
        'urls': [
            'https://36kr.com/api/newsflash',
            'https://36kr.com/api/search-column/mainsite'
        ]
    },
    'jingdata': {
        'enabled': False,  # 需要登录
        'api_key': '',     # 填入你的 API Key
        'base_url': 'https://www.jingdata.com/api'
    },
    'itjuzi': {
        'enabled': False,  # 需要登录
        'api_key': '',     # 填入你的 API Key
        'base_url': 'https://www.itjuzi.com/api'
    }
}

# 通知配置 (可选)
NOTIFICATION = {
    'enabled': False,
    'min_score': 20,  # 匹配分数达到此值才通知
    'channels': {
        'email': {
            'enabled': False,
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'to': ['your@email.com']
        },
        'slack': {
            'enabled': False,
            'webhook_url': ''
        },
        'telegram': {
            'enabled': False,
            'bot_token': '',
            'chat_id': ''
        }
    }
}

# 导出配置
EXPORT = {
    'enabled': True,
    'format': 'json',  # json, csv
    'output_dir': 'research/investment/sample-data/',
    'filename_pattern': 'funding_events_{date}.{ext}'
}

# 日志配置
LOGGING = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': None  # 设为文件路径以记录到文件
}
