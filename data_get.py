"""
中国奶茶行业大数据分析 - 地理位置数据爬取
使用高德地图API爬取蜜雪冰城、古茗、茶百道三家奶茶店的全国门店位置数据
"""

import requests
import time
import json
import csv
import os
from typing import List, Dict
from datetime import datetime

class TeaShopCrawler:
    """奶茶店地理位置爬虫"""
    
    def __init__(self, api_key: str):
        """
        初始化爬虫
        
        Args:
            api_key: 高德地图API密钥
        """
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/place/text"
        self.delay = 0.2  # 请求延迟，避免频率过高
        # self.brands = ["蜜雪冰城", "古茗", "茶百道"]
        self.brands = ["霸王茶姬", "喜茶", "奈雪的茶"]
        self.data_dir = "data"
        
        # 创建数据目录
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_provinces(self) -> List[str]:
        """
        获取全国所有省份和直辖市列表
        
        Returns:
            省份名称列表
        """
        provinces = [
            "北京", "上海", "天津", "重庆",
            "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
            "江苏", "浙江", "安徽", "福建", "江西", "山东",
            "河南", "湖北", "湖南", "广东", "广西", "海南",
            "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
            "青海", "宁夏", "新疆", "香港", "澳门", "台湾"
        ]
        return provinces
    
    def get_cities(self) -> List[str]:
        """
        获取全国主要城市列表（包括所有地级市）
        使用预定义的城市列表以确保覆盖全面
        
        Returns:
            城市名称列表
        """
        # 完整的城市列表（包括所有地级市）
        cities = [
            # 直辖市
            "北京", "上海", "天津", "重庆",
            # 河北省
            "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
            # 山西省
            "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
            # 内蒙古自治区
            "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安盟", "锡林郭勒盟", "阿拉善盟",
            # 辽宁省
            "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
            # 吉林省
            "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边朝鲜族自治州",
            # 黑龙江省
            "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭地区",
            # 江苏省
            "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
            # 浙江省
            "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
            # 安徽省
            "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山", "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
            # 福建省
            "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
            # 江西省
            "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
            # 山东省
            "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
            # 河南省
            "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店", "济源",
            # 湖北省
            "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施土家族苗族自治州", "仙桃", "潜江", "天门", "神农架林区",
            # 湖南省
            "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西土家族苗族自治州",
            # 广东省
            "广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名", "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
            # 广西壮族自治区
            "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
            # 海南省
            "海口", "三亚", "三沙", "儋州", "五指山", "琼海", "文昌", "万宁", "东方", "定安", "屯昌", "澄迈", "临高", "白沙黎族自治县", "昌江黎族自治县", "乐东黎族自治县", "陵水黎族自治县", "保亭黎族苗族自治县", "琼中黎族苗族自治县",
            # 四川省
            "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州",
            # 贵州省
            "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南布依族苗族自治州", "黔东南苗族侗族自治州", "黔南布依族苗族自治州",
            # 云南省
            "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州", "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州",
            # 西藏自治区
            "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里地区",
            # 陕西省
            "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
            # 甘肃省
            "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏回族自治州", "甘南藏族自治州",
            # 青海省
            "西宁", "海东", "海北藏族自治州", "黄南藏族自治州", "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州", "海西蒙古族藏族自治州",
            # 宁夏回族自治区
            "银川", "石嘴山", "吴忠", "固原", "中卫",
            # 新疆维吾尔自治区
            "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区", "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区", "石河子", "阿拉尔", "图木舒克", "五家渠", "北屯", "铁门关", "双河", "可克达拉", "昆玉", "胡杨河"
        ]
        
        return cities
    
    def search_poi(self, keywords: str, city: str = "全国", page: int = 1, page_size: int = 20) -> Dict:
        """
        搜索POI（兴趣点）
        
        Args:
            keywords: 搜索关键词（如"蜜雪冰城"）
            city: 城市名称，默认为"全国"
            page: 页码，从1开始
            page_size: 每页数量，最大25
        
        Returns:
            API返回的JSON数据
        """
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "offset": page_size,  # 每页记录数
            "page": page,  # 当前页数
            "extensions": "all"  # 返回详细信息
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 检查API返回状态
            if data.get("status") == "1":
                return data
            else:
                print(f"API错误: {data.get('info', '未知错误')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            return None
    
    def parse_poi_data(self, poi_data: Dict, brand: str) -> List[Dict]:
        """
        解析POI数据
        
        Args:
            poi_data: API返回的POI数据
            brand: 品牌名称
        
        Returns:
            解析后的数据列表
        """
        pois = poi_data.get("pois", [])
        parsed_data = []
        
        for poi in pois:
            try:
                # 提取经纬度
                location = poi.get("location", "").split(",")
                longitude = location[0] if len(location) > 0 else ""
                latitude = location[1] if len(location) > 1 else ""
                
                # 提取详细地址信息
                adname = poi.get("adname", "")  # 区县
                cityname = poi.get("cityname", "")  # 城市
                pname = poi.get("pname", "")  # 省份
                
                data_item = {
                    "品牌": brand,
                    "名称": poi.get("name", ""),
                    "地址": poi.get("address", ""),
                    "省份": pname,
                    "城市": cityname,
                    "区县": adname,
                    "经度": longitude,
                    "纬度": latitude,
                    "电话": poi.get("tel", ""),
                    "类型": poi.get("type", ""),
                    "ID": poi.get("id", ""),
                    "爬取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                parsed_data.append(data_item)
                
            except Exception as e:
                print(f"解析数据异常: {e}, POI: {poi}")
                continue
        
        return parsed_data
    
    def crawl_brand_in_city(self, brand: str, city: str = "全国") -> List[Dict]:
        """
        爬取某个品牌在某个城市的所有门店
        
        Args:
            brand: 品牌名称
            city: 城市名称，默认为"全国"
        
        Returns:
            门店数据列表
        """
        all_data = []
        page = 1
        max_pages = 100  # 设置最大页数，防止无限循环
        
        city_label = "全国" if city == "全国" else city
        print(f"  正在爬取 {brand} 在 {city_label} 的门店...")
        
        while page <= max_pages:
            poi_data = self.search_poi(brand, city, page=page)
            
            if not poi_data:
                break
            
            count = int(poi_data.get("count", 0))
            pois = poi_data.get("pois", [])
            
            if not pois:
                break
            
            # 解析数据
            parsed_data = self.parse_poi_data(poi_data, brand)
            all_data.extend(parsed_data)
            
            print(f"    第{page}页: 获取到{len(parsed_data)}条数据，总计{len(all_data)}条，总计{count}条")
            
            # 检查是否还有更多数据
            if len(pois) < 20:  # 如果当前页数据少于20条，说明已经是最后一页
                break
            
            # 判断是否已获取所有数据
            if len(all_data) >= count:
                break
            
            page += 1
            time.sleep(self.delay)  # 延迟，避免请求过快
        
        return all_data
    
    def crawl_all_brands(self, search_mode: str = "province") -> Dict[str, List[Dict]]:
        """
        爬取所有品牌在全国的门店数据
        
        Args:
            search_mode: 搜索模式
                - "province": 按省份搜索（推荐，平衡速度和完整性）
                - "city": 按城市逐个搜索（最全面，但较慢）
                - "nationwide": 直接全国搜索（最快，但可能不够完整）
        
        Returns:
            字典，key为品牌名称，value为门店数据列表
        """
        all_results = {brand: [] for brand in self.brands}
        
        if search_mode == "nationwide":
            # 使用全国搜索（最快，但可能不够完整）
            print(f"开始爬取数据，共{len(self.brands)}个品牌，使用全国搜索模式")
            print("=" * 60)
            
            for brand in self.brands:
                print(f"\n【{brand}】")
                brand_data = self.crawl_brand_in_city(brand, "全国")
                
                # 去重（根据POI ID）
                seen_ids = set()
                unique_data = []
                for item in brand_data:
                    poi_id = item.get("ID", "")
                    if poi_id and poi_id not in seen_ids:
                        seen_ids.add(poi_id)
                        unique_data.append(item)
                
                print(f"\n{brand} 共爬取 {len(brand_data)} 条数据，去重后 {len(unique_data)} 条")
                all_results[brand] = unique_data
                
                # 保存单个品牌数据
                self.save_to_csv(brand, unique_data)
        
        elif search_mode == "province":
            # 按省份搜索（推荐，平衡速度和完整性）
            provinces = self.get_provinces()
            print(f"开始爬取数据，共{len(self.brands)}个品牌，{len(provinces)}个省份/直辖市")
            print("=" * 60)
            
            for brand in self.brands:
                print(f"\n【{brand}】")
                brand_data = []
                
                for i, province in enumerate(provinces, 1):
                    print(f"[{i}/{len(provinces)}] 省份: {province}")
                    province_data = self.crawl_brand_in_city(brand, province)
                    brand_data.extend(province_data)
                    
                    # 避免请求过快
                    time.sleep(self.delay)
                
                # 去重（根据POI ID）
                seen_ids = set()
                unique_data = []
                for item in brand_data:
                    poi_id = item.get("ID", "")
                    if poi_id and poi_id not in seen_ids:
                        seen_ids.add(poi_id)
                        unique_data.append(item)
                
                print(f"\n{brand} 共爬取 {len(brand_data)} 条数据，去重后 {len(unique_data)} 条")
                all_results[brand] = unique_data
                
                # 保存单个品牌数据
                self.save_to_csv(brand, unique_data)
        
        else:  # search_mode == "city"
            # 按城市逐个搜索（最全面，但较慢）
            cities = self.get_cities()
            print(f"开始爬取数据，共{len(self.brands)}个品牌，{len(cities)}个城市")
            print("=" * 60)
            
            for brand in self.brands:
                print(f"\n【{brand}】")
                brand_data = []
                
                for i, city in enumerate(cities, 1):
                    print(f"[{i}/{len(cities)}] 城市: {city}")
                    city_data = self.crawl_brand_in_city(brand, city)
                    brand_data.extend(city_data)
                    
                    # 避免请求过快
                    time.sleep(self.delay)
                
                # 去重（根据POI ID）
                seen_ids = set()
                unique_data = []
                for item in brand_data:
                    poi_id = item.get("ID", "")
                    if poi_id and poi_id not in seen_ids:
                        seen_ids.add(poi_id)
                        unique_data.append(item)
                
                print(f"\n{brand} 共爬取 {len(brand_data)} 条数据，去重后 {len(unique_data)} 条")
                all_results[brand] = unique_data
                
                # 保存单个品牌数据
                self.save_to_csv(brand, unique_data)
        
        return all_results
    
    def save_to_csv(self, brand: str, data: List[Dict]):
        """
        保存数据到CSV文件
        
        Args:
            brand: 品牌名称
            data: 数据列表
        """
        if not data:
            print(f"  {brand} 无数据可保存")
            return
        
        filename = os.path.join(self.data_dir, f"{brand}_门店位置数据.csv")
        
        # 获取所有字段名
        fieldnames = list(data[0].keys())
        
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"  {brand} 数据已保存到: {filename}")
    
    def save_to_json(self, data: Dict[str, List[Dict]]):
        """
        保存所有数据到JSON文件
        
        Args:
            data: 所有品牌的数据字典
        """
        filename = os.path.join(self.data_dir, "所有品牌门店位置数据.json")
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n所有数据已保存到JSON文件: {filename}")
    
    def merge_all_data(self, data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        合并所有品牌的数据
        
        Args:
            data: 所有品牌的数据字典
        
        Returns:
            合并后的数据列表
        """
        merged = []
        for brand_data in data.values():
            merged.extend(brand_data)
        return merged
    
    def save_merged_csv(self, data: Dict[str, List[Dict]]):
        """
        保存合并后的所有数据到CSV
        
        Args:
            data: 所有品牌的数据字典
        """
        merged_data = self.merge_all_data(data)
        
        if not merged_data:
            print("无数据可保存")
            return
        
        filename = os.path.join(self.data_dir, "所有品牌门店位置数据_合并.csv")
        fieldnames = list(merged_data[0].keys())
        
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_data)
        
        print(f"合并数据已保存到: {filename}")
        print(f"总计 {len(merged_data)} 条门店数据")


def main():
    """主函数"""
    # 尝试从配置文件读取API密钥
    API_KEY = None
    try:
        import config
        API_KEY = getattr(config, 'AMAP_API_KEY', None)
    except ImportError:
        pass
    
    # 如果配置文件中没有，使用默认值
    if not API_KEY or API_KEY == "YOUR_AMAP_API_KEY_HERE":
        API_KEY = "YOUR_AMAP_API_KEY"
    
    # 检查API密钥是否已设置
    if API_KEY == "YOUR_AMAP_API_KEY" or not API_KEY:
        print("=" * 60)
        print("错误: 请先设置高德地图API密钥！")
        print("=" * 60)
        print("方法1: 创建 config.py 文件，添加 AMAP_API_KEY = '你的密钥'")
        print("方法2: 直接修改 data_get.py 中的 API_KEY 变量")
        print("=" * 60)
        print("申请API密钥步骤:")
        print("1. 访问 https://lbs.amap.com/ 注册账号")
        print("2. 创建应用并申请Web服务API密钥")
        print("3. 将API密钥添加到配置中")
        print("=" * 60)
        return
    
    # 创建爬虫实例
    crawler = TeaShopCrawler(API_KEY)
    
    # 开始爬取
    print("开始爬取奶茶店地理位置数据...")
    print("=" * 60)
    
    # 询问使用哪种搜索模式
    print("\n请选择搜索模式:")
    print("1. 按省份搜索（推荐，平衡速度和完整性）")
    print("2. 按城市搜索（最全面，覆盖所有城市，但较慢）")
    print("3. 全国搜索（最快，但可能不够完整）")
    choice = input("请输入选择 (1/2/3，默认1): ").strip() or "1"
    
    if choice == "1":
        search_mode = "province"
    elif choice == "2":
        search_mode = "city"
    else:
        search_mode = "nationwide"
    
    try:
        # 爬取所有品牌数据
        all_data = crawler.crawl_all_brands(search_mode=search_mode)
        
        # 保存JSON格式
        crawler.save_to_json(all_data)
        
        # 保存合并CSV
        crawler.save_merged_csv(all_data)
        
        # 统计信息
        print("\n" + "=" * 60)
        print("爬取完成！数据统计:")
        print("=" * 60)
        for brand, data in all_data.items():
            print(f"{brand}: {len(data)} 条数据")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n用户中断爬取")
    except Exception as e:
        print(f"\n\n爬取过程出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

