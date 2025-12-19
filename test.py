import requests
import json
import time
import random
import pandas as pd
from datetime import datetime, timedelta
import re
import os
from urllib.parse import unquote

class TeaBrandCommentSpider:
    def __init__(self, cookie):
        """
        初始化奶茶品牌评论爬虫（优化关键词和评价过滤）
        """
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': cookie,
            'Referer': 'https://weibo.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.session.headers.update(self.headers)
        
        # 全局去重集合
        self.crawled_weibo_ids = set()
        self.crawled_comment_ids = set()
        
        # 🔥 优化1：新增品牌与扩展关键词
        self.target_brands = {
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
            # 新增品牌
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
        
        # 🔥 优化2：评价过滤词库（包含这些词的微博才视为有效评价）
        self.evaluation_keywords = {
            '口感', '味道', '好喝', '难喝', '甜度', '茶底', '配料', '奶油', '珍珠', '芋圆',
            '性价比', '太贵', '便宜', '划算', '不值',
            '推荐', '踩雷', '避雷', '种草', '拔草',
            '测评', '体验', '反馈', '评价', '感受',
            '新品', '经典款', '招牌', '出餐速度', '服务态度', '外卖', '门店'
        }
        
        # 🔥 优化3：无关内容过滤词库（包含这些词的微博直接跳过）
        self.filter_keywords = {
            '代言', '明星', '八卦', '营销', '活动', '优惠', '打折', '券',
            '加盟', '招商', '招聘', '行业', '新闻', '财报', '上市',
            '转发', '抽奖', '点赞', '关注', '投票', '助力', '直播'
        }
        
        # 时间范围：近3年
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3*365)
        self.date_range = f"custom:{start_date.strftime('%Y-%m-%d')}-0:{end_date.strftime('%Y-%m-%d')}-23"
    
    def is_valid_evaluation(self, text):
        """
        判断文本是否为有效用户评价（核心过滤逻辑）
        """
        if not text:
            return False
        
        # 1. 过滤无关内容
        for filter_word in self.filter_keywords:
            if filter_word in text:
                return False
        
        # 2. 必须包含至少1个评价词
        for eval_word in self.evaluation_keywords:
            if eval_word in text:
                return True
        
        return False
    
    def search_weibos(self, keyword, pages=3, sort_by='hot'):
        """
        搜索包含关键词的微博（新增评价过滤）
        """
        weibo_list = []
        seen_in_all_pages = set()
        
        for page in range(1, pages + 1):
            try:
                url = "https://s.weibo.com/weibo"
                params = {
                    'q': keyword,
                    'typeall': 1,
                    'suball': 1,
                    'timescope': self.date_range,
                    'Refer': 'g',
                    'page': page
                }
                
                if sort_by == 'hot':
                    params['xsort'] = 'hot'
                
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()  # 如果请求失败则抛出异常
                response.encoding = 'utf-8'
                
                # 正则匹配微博文本和ID
                weibo_pattern = r'<p class="txt".*?>(.*?)</p>.*?weibo\.com/(\d+)/([A-Za-z0-9]{8,10})'
                matches = re.findall(weibo_pattern, response.text, re.DOTALL)
                
                page_new_count = 0
                for weibo_text, user_id, weibo_id in matches:
                    if weibo_id in self.crawled_weibo_ids or weibo_id in seen_in_all_pages:
                        continue
                    
                    clean_text = self.clean_text(weibo_text)
                    if not self.is_valid_evaluation(clean_text):
                        continue
                    
                    seen_in_all_pages.add(weibo_id)
                    weibo_list.append({
                        'weibo_id': weibo_id,
                        'user_id': user_id,
                        'keyword': keyword,
                        'weibo_text': clean_text
                    })
                    self.crawled_weibo_ids.add(weibo_id)
                    page_new_count += 1
                
                print(f"关键词 '{keyword}' 第{page}页搜索完成，找到{page_new_count}条有效评价微博")
                
                if page_new_count == 0 and page > 1:
                    print(f"第{page}页未找到新的有效微博，停止搜索")
                    break
                
                time.sleep(random.uniform(3, 5))
                
            except requests.exceptions.RequestException as e:
                print(f"搜索第{page}页时出错: {e}")
                time.sleep(10)  # 出错时延长等待时间
                continue
            except Exception as e:
                print(f"搜索过程中发生未知错误: {e}")
                continue
                
        return weibo_list
    
    def get_comments(self, weibo_id, weibo_text, brand, keyword):
        """
        获取单条微博的评论（新增评论过滤）
        """
        all_comments = []
        
        for page in range(1, 51):  # 最多获取50页评论
            try:
                url = f"https://weibo.com/ajax/statuses/buildComments"
                params = {
                    'flow': 0,
                    'is_reload': 1,
                    'id': weibo_id,
                    'is_show_bulletin': 2,
                    'is_mix': 0,
                    'count': 20,
                    'page': page
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                comments = data.get('data', [])
                
                if not comments:
                    if page == 1:
                        print(f"    该微博无评论")
                    else:
                        print(f"    第{page}页没有更多评论")
                    break
                
                page_new = 0
                for comment in comments:
                    comment_id = comment.get('id')
                    comment_text = self.clean_text(comment.get('text', ''))
                    
                    if comment_id in self.crawled_comment_ids or not self.is_valid_evaluation(comment_text):
                        continue
                    
                    self.crawled_comment_ids.add(comment_id)
                    comment_info = {
                        'weibo_id': weibo_id,
                        'comment_id': comment_id,
                        'user_id': comment.get('user', {}).get('id'),
                        'user_name': comment.get('user', {}).get('screen_name'),
                        'text': comment_text,
                        'like_count': comment.get('like_count', 0),
                        'created_at': self.parse_time(comment.get('created_at', '')),
                        'reply_count': comment.get('total_number', 0),
                        'source': comment.get('source', ''),
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'brand': brand,
                        'search_keyword': keyword,
                        'weibo_text': weibo_text
                    }
                    all_comments.append(comment_info)
                    page_new += 1
                
                print(f"    微博 {weibo_id} 第{page}页获取 {page_new} 条有效评论（共{len(comments)}条）")
                
                if page_new == 0:
                    print(f"    第{page}页没有新的有效评论，停止获取")
                    break
                
                time.sleep(random.uniform(2, 4))
                
            except requests.exceptions.RequestException as e:
                print(f"    获取第{page}页评论时出错: {e}")
                time.sleep(5)
                continue
            except Exception as e:
                print(f"    获取评论时发生未知错误: {e}")
                continue
        
        print(f"  微博 {weibo_id} 共获取 {len(all_comments)} 条有效评价评论")
        return all_comments
    
    def clean_text(self, text):
        """清理文本，移除HTML标签和多余空格"""
        if not text:
            return ""
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def parse_time(self, time_str):
        """解析微博时间格式"""
        try:
            if '前' in time_str:
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif '-' in time_str:
                return time_str
            else:
                current_year = datetime.now().year
                time_str = f"{current_year}-{time_str}"
                time_str = time_str.replace('月', '-').replace('日', '')
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d %H:%M:%S')
        except:
            return time_str
    
    def scrape_brand_comments(self, pages_per_keyword=3):
        """
        爬取所有目标品牌的评价数据
        """
        all_comments_data = []
        
        print("=" * 60)
        print("奶茶品牌用户评价爬虫 - 近3年数据采集")
        print("=" * 60)
        print(f"目标品牌: {', '.join(self.target_brands.keys())}")
        print(f"时间范围: 近3年")
        print(f"每个关键词搜索页数: {pages_per_keyword}")
        print()
        
        for brand_index, (brand, keywords) in enumerate(self.target_brands.items(), 1):
            print(f"\n【开始爬取品牌 {brand_index}/{len(self.target_brands)}: {brand}】")
            print("-" * 50)
            
            brand_comment_count = 0
            for keyword in keywords:
                print(f"\n  [关键词] {keyword}")
                
                try:
                    weibos = self.search_weibos(keyword, pages=pages_per_keyword, sort_by='hot')
                    
                    print(f"  关键词 '{keyword}' 找到 {len(weibos)} 条有效评价微博")
                    
                    if len(weibos) == 0:
                        continue
                    
                    for i, weibo in enumerate(weibos, 1):
                        print(f"\n    正在获取第{i}条微博的评论: {weibo['weibo_id']}")
                        
                        try:
                            comments = self.get_comments(
                                weibo_id=weibo['weibo_id'],
                                weibo_text=weibo['weibo_text'],
                                brand=brand,
                                keyword=keyword
                            )
                            
                            if not comments:
                                continue
                            
                            all_comments_data.extend(comments)
                            brand_comment_count += len(comments)
                            
                            time.sleep(random.uniform(3, 5))
                            
                        except Exception as e:
                            print(f"    获取评论失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"  处理关键词 '{keyword}' 时出错: {e}")
                    continue
            
            print(f"\n品牌 '{brand}' 共获取 {brand_comment_count} 条有效评价评论")
            
            # 保存进度
            if all_comments_data:
                df = pd.DataFrame(all_comments_data)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                progress_file = f'tea_brand_evaluation_progress_{timestamp}.csv'
                df.to_csv(progress_file, index=False, encoding='utf-8-sig')
                print(f"  进度已保存至: {progress_file}")
            
            # 品牌间延时
            if brand_index < len(self.target_brands):
                wait_time = random.uniform(10, 15)
                print(f"  等待 {wait_time:.1f} 秒后处理下一个品牌...")
                time.sleep(wait_time)
        
        # 最终保存
        if all_comments_data:
            self.save_final_results(all_comments_data)
        else:
            print("\n未获取到任何有效评价数据，请检查Cookie或网络连接")
    
    def save_final_results(self, all_comments_data):
        """保存最终评价数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存为CSV
        final_file = f'tea_brand_evaluations_{timestamp}.csv'
        df = pd.DataFrame(all_comments_data)
        columns = [
            'brand', 'search_keyword', 'weibo_id', 'weibo_text',
            'comment_id', 'user_id', 'user_name', 'text',
            'like_count', 'reply_count', 'created_at', 'source', 'crawl_time'
        ]
        df = df[columns]
        df.to_csv(final_file, index=False, encoding='utf-8-sig')
        
        print("\n" + "=" * 60)
        print("用户评价数据采集完成！")
        print("=" * 60)
        print(f"最终数据文件: {final_file}")
        print(f"共获取 {len(all_comments_data)} 条有效用户评价")
        
        # 数据统计
        print("\n【评价数据统计】")
        print(f"  涉及品牌数量: {df['brand'].nunique()}")
        print(f"  涉及微博数量: {df['weibo_id'].nunique()}")
        print(f"  涉及用户数量: {df['user_id'].nunique()}")
        
        print("\n【各品牌评价数统计】")
        brand_stats = df['brand'].value_counts()
        for brand, count in brand_stats.items():
            print(f"  {brand}: {count} 条评价")
        
        # 保存统计报告
        stats_file = f'tea_brand_evaluation_stats_{timestamp}.txt'
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("奶茶品牌用户评价数据统计报告\n")
            f.write("=" * 60 + "\n")
            f.write(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总有效评价数: {len(all_comments_data)}\n")
            f.write(f"涉及品牌数量: {df['brand'].nunique()}\n")
            f.write(f"涉及微博数量: {df['weibo_id'].nunique()}\n")
            f.write(f"涉及用户数量: {df['user_id'].nunique()}\n")
            f.write("\n各品牌评价数统计:\n")
            for brand, count in brand_stats.items():
                f.write(f"  {brand}: {count} 条\n")
        
        print(f"\n统计报告已保存至: {stats_file}")

def main():
    # --- 请在这里替换为你的微博Cookie ---
    WEIBO_COOKIE = "SCF=An6BpHtrBZ9r6RMg7K3_Gruv6Vlea9s67aBSa_jvwWKnZQlw5gZijnbTDh5HpIQhhED9C-PCwMibXHVwZUGFxns.; SINAGLOBAL=756317002022.9448.1762872932781; ALF=1766333877; SUB=_2A25EJODlDeRhGeBN71oV9yjLzT-IHXVnWHwtrDV8PUJbkNAbLU-nkW1NRHUlwio_ce0VHkLeWQsIJu0zA0TCXsmC; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWC4HGrwcpJkXo-.Dn6RWuQ5JpX5KMhUgL.Foq0ShnXS0qNSoe2dJLoIp-LxK-LB-BL1KBLxK-LBKnL1-q0eh5t; _s_tentry=weibo.com; Apache=4609557664519.774.1763803485398; ULV=1763803485399:3:3:2:4609557664519.774.1763803485398:1763741891547; PC_TOKEN=a9b1aeb647"
    # ----------------------------------
    
    if not WEIBO_COOKIE or "你的微博Cookie" in WEIBO_COOKIE:
        print("错误：请先在代码中替换 '你的微博Cookie' 为你自己的真实Cookie！")
        return

    # 初始化爬虫
    spider = TeaBrandCommentSpider(WEIBO_COOKIE)
    
    # 开始爬取（每个关键词爬取3页，你可以根据需要调整）
    spider.scrape_brand_comments(
        pages_per_keyword=50
    )

def get_cookie_guide():
    """获取微博Cookie的指南"""
    print("""
如何获取微博Cookie:
1. 登录微博网页版 (weibo.com)
2. 按F12打开开发者工具
3. 切换到Network(网络)标签
4. 刷新页面
5. 在网络请求列表中找到任意一个请求（例如：weibo.com）
6. 点击该请求，在右侧面板中找到Request Headers（请求头）
7. 复制Cookie的值
8. 将复制的Cookie值粘贴到代码中 WEIBO_COOKIE 的位置

注意: Cookie有效期通常为几天，过期后需要重新获取。
    """)

if __name__ == "__main__":
    get_cookie_guide()
    
    if input("\n是否已配置好微博Cookie? (y/n): ").lower() == 'y':
        main()
    else:
        print("请先配置好微博Cookie再运行程序。")