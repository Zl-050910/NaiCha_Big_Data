import requests
import csv
import time
import random
import hashlib
import re
from datetime import datetime
from html import unescape

# --- 配置区 ---
COOKIE = "_xsrf=bf4H7Y6qD9M7wFBoSxTuCDuD7vn7bxtE; _zap=96b6e4ca-acf4-4f6a-837d-53bbdd042eb1; d_c0=NJbTLb5_axqPTm67mRgsGRpLAK_maMSrIaw=|1746670734; __snaker__id=QLNKhaZr7j1XMxFJ; __zse_ck=004_CmsIHE7PIeqbw4FpaI8lf4gKckNpGMy6tZdbDRqXrVaxp9nG13e=U/SVZf5b34zQCdQySAAmgB2azmWPCv1wtwikRFRCs46ZiJ85DRS=nNtKaLqAZx3yWI=EauE=6we1-iK1nc9a7PIOm6UUhVjIMXU5OJPEjhYRe7ZBVRjE8XZuO8XOQ449ThFVQNexG7u1yCeAPsLzzoC58hEIohsI5MjYPj2twf8FgbAGI0qBsJGGfPQSAm0O+LNm33ZurBgCKZoCN2Xk5G3vQUuqYJZcx2+CLvel6ONmg4A/Ww32+TII=; Hm_lvt_98beee57fd2ef70ccdd5ca52b9740c49=1763445970,1763734217,1763740085,1763786640; HMACCOUNT=9147B2F8E0928C47; SESSIONID=RCoGcoNXq59qmxJ8thPXPolmIViERuxswSfu96fMXUa; JOID=U1AXC0Jf7tl_cSq3AkBLidK6XN0bBKe8ORpM81Am0uoEHVr0MNNh8x9wKbcJoWuAQqUSJ27n7vyLaLIkfJVaO5w=; osd=VV4VB0xZ4Ntzfyy5AExFj9y4UNMdCqWwNxxC8Vwo1OQGEVTyPtFt_Rl-K7sHp2WCTqsUKWzr4PqFar4qeptYN5I=; gdxidpyhxdE=qM5n0uIRAfLa2a9OeH83eyb%2BdmR6uP%5CC0weqU6%5CUWCMlmlfemG2hSAsrMtaWpmvkQfliTxz2IwsoRG%5ChShxD7S5NtGYEWN%2FJniRDd0pmC4roGCxksLTw53p6vhDu0Pv38cw4KQ7sUOvydjzxMpu0HmLtlavh4zHyjCR2OhVpg4vZsaLQ%3A1763808021199; DATE=1746670751158; cmci9xde=U2FsdGVkX19tdQQCnv0rtRRaf/zqlT5onsUuL0ymlnis1VFtN6KSOsXEBj0WBGlSXQAqptFGB2kgaehoq2qNhw==; pmck9xge=U2FsdGVkX19UzmN5jwCZtXHpmFxFffB5HgVsbYdx0Iw=; crystal=U2FsdGVkX1++UR5zsuOu9U8oMBsSwidDLhhtE0kvvvCdJTzDV7l0lYKvNXmDugimY8IIRE38AcjIXpHWRj0HrUleH6beUjLFw1ZKdAAv66r+ymF+CerfKql261jU0/l1lBrVJ+Bes/S2f6zZ1e+cBENk8E+1HJGSDJ4qjlLV6croyCU/2hCB5lLV+M85ToVz1Qou8TZwgxX9J0q0Tlm88vfw/88iT3ijz21uh4dBzCs2zJ5uaqpYDmJ9EJmqwdzU; vmce9xdq=U2FsdGVkX19IwmK/zrUOPt9Mco4TRb3M2L+6i/5Z0tKW7o1plNWz78+sCwpSaZPCteZ86oQNI8uPO6Kv4WxHmRCx/6hQbIq7fc6FP83yXLOWode/SioKaX/28Cz7aMSyPdszH5ltKUsky8oibGW0PCPNIY3z76NMRrmf+zHFtC0=; assva6=U2FsdGVkX1+vR4KMqE7266ayvBoUyt6I+RcGoAr902U=; assva5=U2FsdGVkX187Ht7kxxWkuCenvIc0yiishHPmr/zf4y/JceQYp0Kx7l9bNIP2EWZivyZioVFMr1e+t5YohKjN6Q==; captcha_session_v2=2|1:0|10:1763807122|18:captcha_session_v2|88:a0pYU1ZyRG1xQ2N4MndTQ0NDMVBhZWFIZWM4Ynh3YzJOYklSWjVxRDJ3azlvN0lHNmhNWmNLZkI2RFhMb3E1NQ==|ea032e4aaff88a3a281c0a2875f59b62056f47e5d62138fbd39fab1c9eac8cd4; q_c1=d8324a63cc754aff80fade25925f89be|1763807155000|1763807155000; z_c0=2|1:0|10:1763807157|4:z_c0|92:Mi4xVDNsRlZ3QUFBQUEwbHRNdHZuOXJHaVlBQUFCZ0FsVk5zOTBPYWdBTlN4WTl2b2cxdFA5YmJBamlkUzNGa0dkWUh3|32c566a69784b0144dac1169f62cb8ad49750f53e0ff2173a7ad72456e89b028; BEC=46faae78ffea44ab7c29d705bdab5c18; unlock_ticket=APCR4dvkXxkmAAAAYAJVTYqvIWn1VHORhNthtTrwMFKzFjNmx4d3cw==; Hm_lpvt_98beee57fd2ef70ccdd5ca52b9740c49=1763813545"
BRAND_KEYWORDS = {
    '霸王茶姬': [
        '霸王茶姬 口感', '霸王茶姬 味道', '霸王茶姬 性价比', '霸王茶姬 测评',
        '霸王茶姬 甜度', '霸王茶姬 茶底', '霸王茶姬 出餐速度', '霸王茶姬 外卖'
    ],
    '喜茶': [
        '喜茶 口感', '喜茶 味道', '喜茶 性价比', '喜茶 测评',
        '喜茶 甜度', '喜茶 茶底', '喜茶 服务态度', '喜茶 门店体验'
    ],
    '奈雪的茶': [
        '奈雪的茶 口感', '奈雪的茶 味道', '奈雪的茶 性价比', '奈雪的茶 测评',
        '奈雪的茶 配料', '奈雪的茶 产品 评价', '奈雪的茶 出餐速度', '奈雪的茶 外卖'
    ],
    '蜜雪冰城': [
        '蜜雪冰城 口感', '蜜雪冰城 味道', '蜜雪冰城 性价比', '蜜雪冰城 测评',
        '蜜雪冰城 甜度', '蜜雪冰城 配料', '蜜雪冰城 出餐速度', '蜜雪冰城 门店体验'
    ],
    '茶百道': [
        '茶百道 口感', '茶百道 味道', '茶百道 性价比', '茶百道 测评',
        '茶百道 甜度', '茶百道 茶底', '茶百道 服务态度', '茶百道 外卖'
    ],
    '古茗': [
        '古茗 口感', '古茗 味道', '古茗 性价比', '古茗 测评',
        '古茗 甜度', '古茗 配料', '古茗 出餐速度', '古茗 门店体验'
    ]
}
MAX_CONTENT_PAGES = 200    # 每个关键词爬取内容页数
MAX_COMMENT_PAGES = 200    # 每个内容爬取评论页数
START_YEAR = 2019        # 起始年份

# --- 核心优化：丰富的品牌相关产品词 ---
# 包含：所有品牌名、通用行业术语、热门产品类型、服务相关词汇
PRODUCT_KEYWORDS = [
    # 所有目标品牌
    '霸王茶姬', '喜茶', '奈雪的茶', '蜜雪冰城', '茶百道', '古茗','奈雪','茶姬','雪王','蜜雪',
    # 通用行业术语
    '奶茶', '饮品', '茶饮', '果茶', '奶盖', '芝士茶', '水果茶', '烧仙草', '杨枝甘露','柠檬水',
    '珍珠奶茶', '波霸', '芋圆', '椰果', '布丁', '仙草', '茶底', '茶汤', '配料', '小料','甜','糖',
    # 产品包装与形态
    '杯子', '包装', '杯套', '吸管', '手提袋',
    # 线下体验
    '门店', '店面', '装修', '排队', '取餐', '点餐', '服务', '店员','态度',
    # 线上服务
    '外卖', '配送', '骑手', '平台','睡不着',
    # 消费相关
    '价格', '性价比', '贵', '便宜', '划算', '优惠券', '团购', '活动', '打折'
]

# --- 全局变量 ---
crawled_comment_ids = set()  # 评论ID去重集合
comment_content_hashes = set()  # 评论内容MD5去重集合

def clean_html_tags(text):
    """清理HTML标签并解码实体"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_comment_relevant(comment_text, brand):
    """检查评论是否与品牌或行业相关"""
    if not comment_text:
        return False
    comment_text = comment_text.lower()
    
    # 检查是否包含当前爬取的品牌名（优先级最高）
    if brand.lower() in comment_text:
        return True
    
    # 检查是否包含任何行业相关词汇或其他品牌名
    for keyword in PRODUCT_KEYWORDS:
        if keyword.lower() in comment_text:
            return True
    
    return False

def get_content_md5(content):
    """计算文本MD5哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def is_after_start_year(timestamp):
    """检查时间戳是否在START_YEAR年1月1日之后"""
    start_date = datetime(START_YEAR, 1, 1)
    content_date = datetime.fromtimestamp(timestamp)
    return content_date >= start_date

def fetch_content_ids(brand, keyword):
    """获取相关内容ID（2020年至今）"""
    content_ids = []
    offset = 0
    limit = 20

    for page in range(MAX_CONTENT_PAGES):
        print(f"\n=== 正在获取 '{brand}' 关键词 '{keyword}' 的相关内容（第 {page+1}/{MAX_CONTENT_PAGES} 页）===")
        url = "https://www.zhihu.com/api/v4/search_v3"
        params = {
            'gk_version': 'gz-gaokao',
            't': 'general',
            'q': keyword,
            'correction': '1',
            'offset': offset,
            'limit': limit,
            'filter_fields': '',
            'lc_idx': offset,
            'show_all_topics': '0',
            'search_source': 'History'
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params)
            if response.status_code != 200:
                print(f"  获取内容失败，状态码: {response.status_code}")
                break

            data = response.json()
            raw_items = data.get('data', [])
            if not raw_items:
                print(f"  关键词 '{keyword}' 没有更多相关内容了")
                break

            page_valid_count = 0
            for item in raw_items:
                content_obj = item.get('object', {})
                content_type = content_obj.get('type')
                content_id = content_obj.get('id')
                created_time = content_obj.get('created_time', 0)

                if not is_after_start_year(created_time):
                    continue

                if content_type == 'answer':
                    question_id = content_obj.get('question', {}).get('id')
                    title = content_obj.get('question', {}).get('title', '无标题')
                    link = f"https://www.zhihu.com/question/{question_id}/answer/{content_id}"
                elif content_type == 'article':
                    title = content_obj.get('title', '无标题')
                    link = f"https://zhuanlan.zhihu.com/p/{content_id}"
                else:
                    continue

                content_ids.append({
                    'brand': brand,
                    'search_keyword': keyword,
                    'content_type': content_type,
                    'content_id': content_id,
                    'content_title': title,
                    'content_link': link
                })
                page_valid_count += 1

            print(f"  第 {page+1} 页获取到 {len(raw_items)} 条内容，其中 {page_valid_count} 条在 {START_YEAR} 年之后。累计有效内容 {len(content_ids)} 条")
            offset += limit
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"  获取内容ID失败: {str(e)}")
            break

    return content_ids

def fetch_comments(content_info):
    """爬取评论并进行相关性过滤"""
    brand = content_info['brand']
    search_keyword = content_info['search_keyword']
    content_type = content_info['content_type']
    content_id = content_info['content_id']
    content_title = content_info['content_title']
    content_link = content_info['content_link']

    comments = []
    offset = 0
    limit = 20

    if content_type == 'answer':
        comment_api = f"https://www.zhihu.com/api/v4/answers/{content_id}/root_comments"
    elif content_type == 'article':
        comment_api = f"https://www.zhihu.com/api/v4/articles/{content_id}/root_comments"
    else:
        return comments

    print(f"\n--- 正在爬取《{content_title[:30]}...》的评论 ---")

    for page in range(MAX_COMMENT_PAGES):
        params = {
            'order': 'normal',
            'limit': limit,
            'offset': offset,
            'status': 'open'
        }

        try:
            response = requests.get(comment_api, headers=HEADERS, params=params)
            if response.status_code != 200:
                print(f"  爬取评论失败，状态码: {response.status_code}")
                break

            data = response.json()
            raw_comments = data.get('data', [])
            if not raw_comments:
                print(f"  该内容没有更多评论了")
                break

            new_comment_count = 0
            irrelevant_count = 0
            for comm in raw_comments:
                comment_id = comm.get('id')
                comment_content_html = comm.get('content', '').strip()
                comment_content = clean_html_tags(comment_content_html)
                
                if comment_id in crawled_comment_ids:
                    continue
                
                content_hash = get_content_md5(comment_content)
                if content_hash in comment_content_hashes:
                    continue
                
                comment_time = comm.get('created_time', 0)
                if not is_after_start_year(comment_time):
                    continue
                
                # 使用优化后的相关性校验逻辑
                if not is_comment_relevant(comment_content, brand):
                    irrelevant_count += 1
                    continue
                
                crawled_comment_ids.add(comment_id)
                comment_content_hashes.add(content_hash)
                
                author_name = comm.get('author', {}).get('member', {}).get('name', '匿名用户')
                like_count = comm.get('vote_count', 0)
                reply_count = comm.get('comment_count', 0)
                create_time_str = datetime.fromtimestamp(comment_time).strftime('%Y-%m-%d %H:%M:%S')

                comments.append({
                    '品牌': brand,
                    '搜索关键词': search_keyword,
                    '原内容类型': content_type,
                    '原内容标题': content_title,
                    '原内容链接': content_link,
                    '评论ID': comment_id,
                    '评论用户': author_name,
                    '评论内容': comment_content,
                    '评论点赞数': like_count,
                    '评论回复数': reply_count,
                    '评论时间': create_time_str
                })
                new_comment_count += 1

            print(f"  第 {page+1} 页评论：共 {len(raw_comments)} 条，新增 {new_comment_count} 条有效评论，过滤 {irrelevant_count} 条无关评论。")
            offset += limit
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            print(f"  爬取评论失败: {str(e)}")
            break

    return comments

def save_comments_to_csv(all_comments):
    """保存评论到CSV文件"""
    if not all_comments:
        print(f"\n没有爬取到 {START_YEAR} 年至今的有效相关评论数据。")
        return

    filename = f"知乎奶茶品牌评论数据_2020年至今_去重_高相关.csv"
    fieldnames = [
        '品牌', '搜索关键词', '原内容类型', '原内容标题', '原内容链接',
        '评论ID', '评论用户', '评论内容', '评论点赞数', '评论回复数', '评论时间'
    ]

    with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_comments)

    print(f"\n✅ 所有评论爬取完成！")
    print(f"   - 爬取时间范围: {START_YEAR}年1月1日 至今")
    print(f"   - 最终有效相关评论数: {len(all_comments)}")
    print(f"   - 结果已保存到: {filename}")

# --- 请求头 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Cookie': COOKIE,
    'Referer': 'https://www.zhihu.com/',
    'Accept': 'application/json, text/plain, */*',
    'x-zse-93': '101_3_3.0',
    'x-zse-96': '2.0_qcJQ4OHFxKwF26+Z8S+oi8VSgPsaTtX2tW3R6h9hfo6GILr4M6PCyBLuZKnKxPmj'
}

if __name__ == "__main__":
    if COOKIE == "请替换为你的知乎Cookie":
        print("错误：请先设置你的知乎Cookie！")
        exit()

    all_content_info = []
    for brand, keywords in BRAND_KEYWORDS.items():
        for keyword in keywords:
            content_info = fetch_content_ids(brand, keyword)
            all_content_info.extend(content_info)
            
    print(f"\n📊 内容爬取阶段完成，共获取到 {len(all_content_info)} 条 {START_YEAR} 年之后的有效内容，准备爬取评论...")

    all_comments = []
    for idx, content in enumerate(all_content_info, 1):
        print(f"\n===== 处理第 {idx}/{len(all_content_info)} 条内容 =====")
        comments = fetch_comments(content)
        all_comments.extend(comments)

    save_comments_to_csv(all_comments)