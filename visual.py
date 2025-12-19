# -*- coding: utf-8 -*-
# 全新可视化大屏系统
# 功能：奶茶品牌地理分布、中国人口分布、人口与门店对比分析

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import requests
import json
import jieba
import jieba.analyse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io
import re

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="奶茶门店与人口数据可视化大屏",
    page_icon="🍵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== 全局样式 ====================
st.markdown("""
<style>
    /* 全局深色背景 */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #0f172a 50%, #1a1f3a 100%);
    }
    
    /* 主容器 */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* 列间距优化 - 更紧凑 */
    .stColumns {
        gap: 0.1rem !important;
    }
    
    /* 地图和词云图容器间距优化 */
    .chart-wrapper {
        margin: 0.5rem !important;
    }
    
    /* 特定列间距优化 */
    div[data-testid="column"] {
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
    }
    
    /* 隐藏默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 顶部导航栏样式 */
    .top-nav {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        border-bottom: 2px solid #38bdf8;
        padding: 1rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .nav-title {
        font-size: 4.5rem;
        font-weight: bold;
        color: #38bdf8;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
        margin: 0;
    }
    
    .nav-selector {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    /* 内容卡片 */
    .content-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* KPI卡片 */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #475569;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .kpi-value {
        font-size: 4.0rem;
        font-weight: bold;
        color: #38bdf8;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 2.6rem;
        color: #94a3b8;
        margin: 0;
    }
    
    /* 图表容器 */
    .chart-wrapper {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        height: 100%;
    }
    
    /* 地图和词云图容器特殊样式 - 减小间距 */
    .map-wordcloud-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .map-wordcloud-container .chart-wrapper {
        margin: 0.5rem 0.1rem !important;
    }
    
    /* 确保图表容器内容垂直居中 */
    .chart-wrapper > div {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    /* 标题样式 */
    .section-title {
        color: #60a5fa;
        font-size: 4.0rem;
        font-weight: bold;
        margin: 0.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #475569;
    }
    
    /* 文本颜色 */
    h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    
    p, span, div, label {
        color: #e2e8f0;
    }
    
    /* 选择框样式 - 深色主题优化（使用更强的选择器） */
    /* 标签样式 - 使用更多选择器确保覆盖 */
    .stSelectbox label,
    .stSelectbox > label,
    div[data-baseweb="select"] + label,
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    .element-container label,
    .element-container > label,
    div[data-testid="stWidgetLabel"],
    div[data-testid="stWidgetLabel"] p,
    /* 更通用的选择器 */
    p[data-testid="stWidgetLabel"],
    span[data-testid="stWidgetLabel"],
    /* 针对Streamlit的特定结构 */
    div[data-testid="column"] label,
    div[data-testid="column"] > label,
    /* 使用最通用的选择器，但限制在选择框附近 */
    .stSelectbox ~ label,
    .stSelectbox + label,
    /* 直接针对所有label，但只在选择框容器内 */
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] > label {
        color: #e2e8f0 !important;
        font-size: 2.3rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 额外针对Streamlit生成的label结构 */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] > div > label,
    div[data-testid="stSelectbox"] p {
        color: #e2e8f0 !important;
        font-size: 2.3rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 选择框输入区域 - 使用多种选择器确保覆盖 */
    .stSelectbox > div > div,
    .stSelectbox div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div,
    [data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
        min-height: 44px !important;
        font-size: 2.0rem !important;
    }
    
    .stSelectbox > div > div:hover,
    div[data-baseweb="select"] > div:hover {
        border-color: #38bdf8 !important;
        background-color: #334155 !important;
    }
    
    /* 选择框内的文本和值 */
    .stSelectbox [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] [role="combobox"],
    div[data-baseweb="select"] [role="combobox"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        font-size: 2.0rem !important;
    }
    
    /* 选择框内显示的文本 - 使用多种选择器确保覆盖 */
    .stSelectbox [data-baseweb="select"] [role="combobox"] span,
    [data-baseweb="select"] [role="combobox"] span,
    div[data-baseweb="select"] [role="combobox"] span,
    .stSelectbox [data-baseweb="select"] [role="combobox"] div,
    [data-baseweb="select"] [role="combobox"] div,
    div[data-baseweb="select"] [role="combobox"] div,
    .stSelectbox [data-baseweb="select"] [role="combobox"] p,
    [data-baseweb="select"] [role="combobox"] p,
    div[data-baseweb="select"] [role="combobox"] p,
    /* 针对所有可能的文本容器 */
    .stSelectbox [data-baseweb="select"] *,
    [data-baseweb="select"] *,
    div[data-baseweb="select"] * {
        font-size: 2.0rem !important;
        color: #ffffff !important;
    }
    
    /* 下拉箭头颜色 */
    .stSelectbox svg,
    .stSelectbox [data-baseweb="icon"],
    [data-baseweb="select"] svg {
        color: #e2e8f0 !important;
        fill: #e2e8f0 !important;
    }
    
    /* 下拉列表容器 - 使用更强的选择器 */
    .stSelectbox [role="listbox"],
    [role="listbox"],
    div[role="listbox"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
        margin-top: 4px !important;
    }
    
    /* 下拉选项 - 使用更强的选择器 */
    .stSelectbox [role="option"],
    [role="option"],
    div[role="option"],
    li[role="option"] {
        color: #ffffff !important;
        background-color: #1e293b !important;
        padding: 1.2rem 1.5rem !important;
        font-size: 1.8rem !important;
        line-height: 1.8 !important;
        min-height: 3.5rem !important;
    }
    
    .stSelectbox [role="option"]:hover,
    [role="option"]:hover,
    div[role="option"]:hover {
        background-color: #334155 !important;
        color: #38bdf8 !important;
        font-size: 1.8rem !important;
        padding: 1.2rem 1.5rem !important;
        line-height: 1.8 !important;
    }
    
    /* 选中的选项 */
    .stSelectbox [aria-selected="true"][role="option"],
    [aria-selected="true"][role="option"] {
        background-color: #0f172a !important;
        color: #38bdf8 !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        padding: 1.2rem 1.5rem !important;
        line-height: 1.8 !important;
    }
    
    /* 下拉选项内的文本元素 */
    .stSelectbox [role="option"] span,
    [role="option"] span,
    div[role="option"] span,
    li[role="option"] span,
    .stSelectbox [role="option"] div,
    [role="option"] div,
    div[role="option"] div,
    li[role="option"] div {
        font-size: 1.8rem !important;
        color: inherit !important;
        line-height: 1.8 !important;
    }
    
    /* 覆盖所有可能的文本颜色 */
    .stSelectbox *,
    [data-baseweb="select"] * {
        color: inherit !important;
    }
    
    /* 确保选择框文本为白色 */
    .stSelectbox [data-baseweb="select"] {
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        color: #ffffff !important;
    }
    
    /* 针对Streamlit特定的类名 */
    .css-1d391kg .stSelectbox > div > div,
    .element-container .stSelectbox > div > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 数据加载 ====================
@st.cache_data
def load_data():
    """加载所有数据文件"""
    import os
    
    # 使用绝对路径
    base_path = Path("F:/visualization/data")
    
    # 如果绝对路径不存在，尝试相对路径
    if not base_path.exists():
        base_path = Path("data")
        if not base_path.exists():
            base_path = Path.cwd() / "data"
    
    data = {}
    
    # 加载人口数据
    pop_file = base_path / 'population.csv'
    if pop_file.exists():
        try:
            data['population'] = pd.read_csv(pop_file, encoding='utf-8')
        except Exception as e:
            try:
                # 尝试其他编码
                data['population'] = pd.read_csv(pop_file, encoding='gbk')
            except Exception as e2:
                data['population'] = None
    else:
        data['population'] = None
    
    # 加载评论数据
    discussion_file = base_path / 'discussion.csv'
    if discussion_file.exists():
        try:
            data['discussion'] = pd.read_csv(discussion_file, encoding='utf-8')
        except Exception as e:
            try:
                data['discussion'] = pd.read_csv(discussion_file, encoding='gbk')
            except Exception as e2:
                data['discussion'] = None
    else:
        data['discussion'] = None
    
    # 加载所有奶茶品牌数据
    brand_files = {
        '蜜雪冰城': 'mixue.csv',
        '古茗': 'guming.csv',
        '茶百道': 'chabaidao.csv',
        '霸王茶姬': 'bawangchaji.csv',
        '奈雪的茶': 'naixuedecha.csv',
        '喜茶': 'xicha.csv'
    }
    
    for brand, filename in brand_files.items():
        brand_file = base_path / filename
        if brand_file.exists():
            try:
                df = pd.read_csv(brand_file, encoding='utf-8')
                if not df.empty:
                    data[brand] = df
            except Exception as e:
                try:
                    # 尝试其他编码
                    df = pd.read_csv(brand_file, encoding='gbk')
                    if not df.empty:
                        data[brand] = df
                except Exception as e2:
                    data[brand] = None
        else:
            data[brand] = None
    
    return data

@st.cache_data
def get_china_geojson():
    """获取中国省份GeoJSON数据"""
    try:
        url = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# ==================== 数据处理 ====================
def preprocess_brand_data(df):
    """预处理品牌数据"""
    if df is None or df.empty:
        return None
    
    # 确保经纬度是数值类型
    if '经度' in df.columns and '纬度' in df.columns:
        df = df.copy()
        df['经度'] = pd.to_numeric(df['经度'], errors='coerce')
        df['纬度'] = pd.to_numeric(df['纬度'], errors='coerce')
        df = df.dropna(subset=['经度', '纬度'])
    
    return df

def get_province_stats(df):
    """按省份统计门店数量"""
    if df is None or df.empty or '省份' not in df.columns:
        return pd.DataFrame()
    
    stats = df['省份'].value_counts().reset_index()
    stats.columns = ['省份', '门店数量']
    return stats.sort_values('门店数量', ascending=False)

# ==================== 地图可视化 ====================
def create_brand_map(shop_data, brand_name, geojson_data):
    """创建品牌分布地图"""
    if shop_data is None or shop_data.empty:
        return None
    
    # 按省份统计
    province_stats = {}
    for _, row in shop_data.iterrows():
        province = row.get('省份', '未知')
        if province in province_stats:
            province_stats[province] += 1
        else:
            province_stats[province] = 1
    
    # 创建地图
    m = folium.Map(
        location=[35, 105],
        zoom_start=4,
        tiles='CartoDB dark_matter',
        attr='CartoDB'
    )
    
    # 省份名称映射
    province_mapping = {
        '北京市': '北京', '天津市': '天津', '河北省': '河北', '山西省': '山西',
        '内蒙古自治区': '内蒙古', '辽宁省': '辽宁', '吉林省': '吉林', '黑龙江省': '黑龙江',
        '上海市': '上海', '江苏省': '江苏', '浙江省': '浙江', '安徽省': '安徽',
        '福建省': '福建', '江西省': '江西', '山东省': '山东', '河南省': '河南',
        '湖北省': '湖北', '湖南省': '湖南', '广东省': '广东', '广西壮族自治区': '广西',
        '海南省': '海南', '重庆市': '重庆', '四川省': '四川', '贵州省': '贵州',
        '云南省': '云南', '西藏自治区': '西藏', '陕西省': '陕西', '甘肃省': '甘肃',
        '青海省': '青海', '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆'
    }
    
    # 品牌配色方案
    color_schemes = {
        '蜜雪冰城': ['#FFF0F5', '#FFD1DC', '#FF9EBC', '#FF6B9D', '#E63977'],
        '古茗': ['#F0F9FF', '#C3E3FF', '#8AC8FF', '#5AADFF', '#2A8FE6'],
        '茶百道': ['#F0FFF5', '#C3FFD9', '#8AFFB3', '#5AFF8C', '#2AE65C'],
        '霸王茶姬': ['#FEF3C7', '#FDE68A', '#FCD34D', '#FBBF24', '#F59E0B'],
        '奈雪的茶': ['#FCE7F3', '#FBCFE8', '#F9A8D4', '#F472B6', '#EC4899'],
        '喜茶': ['#E0E7FF', '#C7D2FE', '#A5B4FC', '#818CF8', '#6366F1']
    }
    
    colors = color_schemes.get(brand_name, color_schemes['蜜雪冰城'])
    
    if geojson_data:
        for feature in geojson_data['features']:
            province_name = feature['properties']['name']
            shop_count = 0
            
            # 匹配省份
            for full_name, short_name in province_mapping.items():
                if short_name in province_name or province_name in short_name:
                    for shop_province, count in province_stats.items():
                        if short_name in shop_province or shop_province in short_name:
                            shop_count = count
                            break
                    if shop_count > 0:
                        break
            
            # 根据门店数量选择颜色
            if shop_count > 0:
                if shop_count < 100:
                    fill_color = colors[0]
                elif shop_count < 500:
                    fill_color = colors[1]
                elif shop_count < 1000:
                    fill_color = colors[2]
                elif shop_count < 2000:
                    fill_color = colors[3]
                else:
                    fill_color = colors[4]
                
                popup_html = f"""
                <div style='font-family: Arial; padding: 10px;'>
                    <h4 style='margin: 0 0 10px 0; color: #333; font-size: 24px; font-weight: bold;'>{province_name}</h4>
                    <p style='margin: 5px 0; font-size: 20px;'><b>品牌:</b> {brand_name}</p>
                    <p style='margin: 5px 0; font-size: 22px;'><b>门店数量:</b> <span style='color: #e63977; font-weight: bold;'>{shop_count}</span></p>
                </div>
                """
                
                folium.GeoJson(
                    feature,
                    style_function=lambda x, fill=fill_color: {
                        'fillColor': fill,
                        'color': '#666666',
                        'weight': 1,
                        'fillOpacity': 0.8,
                        'opacity': 0.9
                    },
                    popup=folium.Popup(popup_html, max_width=280)
                ).add_to(m)
            else:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#f5f5f5',
                        'color': '#cccccc',
                        'weight': 1,
                        'fillOpacity': 0.3,
                        'opacity': 0.5
                    }
                ).add_to(m)
    
    return m

# ==================== 人口分布地图 ====================
def create_population_map(population_data, year, geojson_data):
    """创建人口分布地图"""
    if population_data is None or population_data.empty:
        return None
    
    # 获取年份对应的列名
    year_column = f'人口（{year}/11/1人口普查）'
    
    if year_column not in population_data.columns:
        return None
    
    # 城市到省份的映射（用于聚合数据）
    city_to_province = {
        '北京市': '北京', '天津市': '天津', 
        '石家庄市': '河北', '唐山市': '河北', '秦皇岛市': '河北', '邯郸市': '河北', 
        '邢台市': '河北', '保定市': '河北', '张家口市': '河北', '承德市': '河北', 
        '沧州市': '河北', '廊坊市': '河北', '衡水市': '河北',
        '太原市': '山西', '大同市': '山西', '阳泉市': '山西', '长治市': '山西',
        '晋城市': '山西', '朔州市': '山西', '晋中市': '山西', '运城市': '山西',
        '忻州市': '山西', '临汾市': '山西', '吕梁市': '山西',
        '呼和浩特市': '内蒙古', '包头市': '内蒙古', '乌海市': '内蒙古',
        '赤峰市': '内蒙古', '通辽市': '内蒙古', '鄂尔多斯市': '内蒙古',
        '呼伦贝尔市': '内蒙古', '巴彦淖尔市': '内蒙古', '乌兰察布市': '内蒙古',
        '沈阳市': '辽宁', '大连市': '辽宁', '鞍山市': '辽宁', '抚顺市': '辽宁',
        '本溪市': '辽宁', '丹东市': '辽宁', '锦州市': '辽宁', '营口市': '辽宁',
        '阜新市': '辽宁', '辽阳市': '辽宁', '盘锦市': '辽宁', '铁岭市': '辽宁',
        '朝阳市': '辽宁', '葫芦岛市': '辽宁',
        '长春市': '吉林', '吉林市': '吉林', '四平市': '吉林', '辽源市': '吉林',
        '通化市': '吉林', '白山市': '吉林', '松原市': '吉林', '白城市': '吉林',
        '哈尔滨市': '黑龙江', '齐齐哈尔市': '黑龙江', '鸡西市': '黑龙江',
        '鹤岗市': '黑龙江', '双鸭山市': '黑龙江', '大庆市': '黑龙江',
        '伊春市': '黑龙江', '佳木斯市': '黑龙江', '七台河市': '黑龙江',
        '牡丹江市': '黑龙江', '黑河市': '黑龙江', '绥化市': '黑龙江',
        '上海市': '上海',
        '南京市': '江苏', '无锡市': '江苏', '徐州市': '江苏', '常州市': '江苏',
        '苏州市': '江苏', '南通市': '江苏', '连云港市': '江苏', '淮安市': '江苏',
        '盐城市': '江苏', '扬州市': '江苏', '镇江市': '江苏', '泰州市': '江苏',
        '宿迁市': '江苏',
        '杭州市': '浙江', '宁波市': '浙江', '温州市': '浙江', '嘉兴市': '浙江',
        '湖州市': '浙江', '绍兴市': '浙江', '金华市': '浙江', '衢州市': '浙江',
        '舟山市': '浙江', '台州市': '浙江', '丽水市': '浙江',
        '合肥市': '安徽', '芜湖市': '安徽', '蚌埠市': '安徽', '淮南市': '安徽',
        '马鞍山市': '安徽', '淮北市': '安徽', '铜陵市': '安徽', '安庆市': '安徽',
        '黄山市': '安徽', '滁州市': '安徽', '阜阳市': '安徽', '宿州市': '安徽',
        '六安市': '安徽', '亳州市': '安徽', '池州市': '安徽', '宣城市': '安徽',
        '福州市': '福建', '厦门市': '福建', '莆田市': '福建', '三明市': '福建',
        '泉州市': '福建', '漳州市': '福建', '南平市': '福建', '龙岩市': '福建',
        '宁德市': '福建',
        '南昌市': '江西', '景德镇市': '江西', '萍乡市': '江西', '九江市': '江西',
        '新余市': '江西', '鹰潭市': '江西', '赣州市': '江西', '吉安市': '江西',
        '宜春市': '江西', '抚州市': '江西', '上饶市': '江西',
        '济南市': '山东', '青岛市': '山东', '淄博市': '山东', '枣庄市': '山东',
        '东营市': '山东', '烟台市': '山东', '潍坊市': '山东', '济宁市': '山东',
        '泰安市': '山东', '威海市': '山东', '日照市': '山东', '临沂市': '山东',
        '德州市': '山东', '聊城市': '山东', '滨州市': '山东', '菏泽市': '山东',
        '郑州市': '河南', '开封市': '河南', '洛阳市': '河南', '平顶山市': '河南',
        '安阳市': '河南', '鹤壁市': '河南', '新乡市': '河南', '焦作市': '河南',
        '濮阳市': '河南', '许昌市': '河南', '漯河市': '河南', '三门峡市': '河南',
        '南阳市': '河南', '商丘市': '河南', '信阳市': '河南', '周口市': '河南',
        '驻马店市': '河南',
        '武汉市': '湖北', '黄石市': '湖北', '十堰市': '湖北', '宜昌市': '湖北',
        '襄阳市': '湖北', '鄂州市': '湖北', '荆门市': '湖北', '孝感市': '湖北',
        '荆州市': '湖北', '黄冈市': '湖北', '咸宁市': '湖北', '随州市': '湖北',
        '长沙市': '湖南', '株洲市': '湖南', '湘潭市': '湖南', '衡阳市': '湖南',
        '邵阳市': '湖南', '岳阳市': '湖南', '常德市': '湖南', '张家界市': '湖南',
        '益阳市': '湖南', '郴州市': '湖南', '永州市': '湖南', '怀化市': '湖南',
        '娄底市': '湖南',
        '广州市': '广东', '韶关市': '广东', '深圳市': '广东', '珠海市': '广东',
        '汕头市': '广东', '佛山市': '广东', '江门市': '广东', '湛江市': '广东',
        '茂名市': '广东', '肇庆市': '广东', '惠州市': '广东', '梅州市': '广东',
        '汕尾市': '广东', '河源市': '广东', '阳江市': '广东', '清远市': '广东',
        '东莞市': '广东', '中山市': '广东', '潮州市': '广东', '揭阳市': '广东',
        '云浮市': '广东',
        '南宁市': '广西', '柳州市': '广西', '桂林市': '广西', '梧州市': '广西',
        '北海市': '广西', '防城港市': '广西', '钦州市': '广西', '贵港市': '广西',
        '玉林市': '广西', '百色市': '广西', '贺州市': '广西', '河池市': '广西',
        '来宾市': '广西', '崇左市': '广西',
        '海口市': '海南', '三亚市': '海南',
        '重庆市': '重庆',
        '成都市': '四川', '自贡市': '四川', '攀枝花市': '四川', '泸州市': '四川',
        '德阳市': '四川', '绵阳市': '四川', '广元市': '四川', '遂宁市': '四川',
        '内江市': '四川', '乐山市': '四川', '南充市': '四川', '眉山市': '四川',
        '宜宾市': '四川', '广安市': '四川', '达州市': '四川', '雅安市': '四川',
        '巴中市': '四川', '资阳市': '四川',
        '贵阳市': '贵州', '六盘水市': '贵州', '遵义市': '贵州', '安顺市': '贵州',
        '毕节市': '贵州', '铜仁市': '贵州',
        '昆明市': '云南', '曲靖市': '云南', '玉溪市': '云南', '保山市': '云南',
        '昭通市': '云南', '丽江市': '云南', '普洱市': '云南', '临沧市': '云南',
        '拉萨市': '西藏', '日喀则市': '西藏', '昌都市': '西藏', '林芝市': '西藏',
        '山南市': '西藏', '那曲市': '西藏',
        '西安市': '陕西', '铜川市': '陕西', '宝鸡市': '陕西', '咸阳市': '陕西',
        '渭南市': '陕西', '延安市': '陕西', '汉中市': '陕西', '榆林市': '陕西',
        '安康市': '陕西', '商洛市': '陕西',
        '兰州市': '甘肃', '嘉峪关市': '甘肃', '金昌市': '甘肃', '白银市': '甘肃',
        '天水市': '甘肃', '武威市': '甘肃', '张掖市': '甘肃', '平凉市': '甘肃',
        '酒泉市': '甘肃', '庆阳市': '甘肃', '定西市': '甘肃', '陇南市': '甘肃',
        '西宁市': '青海', '海东市': '青海',
        '银川市': '宁夏', '石嘴山市': '宁夏', '吴忠市': '宁夏', '固原市': '宁夏',
        '中卫市': '宁夏',
        '乌鲁木齐市': '新疆', '克拉玛依市': '新疆'
    }
    
    # 添加省份列并聚合数据
    temp_data = population_data.copy()
    temp_data['省份'] = temp_data['地名'].map(city_to_province)
    
    # 对于已经是省份的数据，直接使用
    province_data = temp_data[temp_data['类型'] == '省'].copy()
    if not province_data.empty:
        province_data['省份'] = province_data['地名'].str.replace('省', '').str.replace('自治区', '').str.replace('维吾尔自治区', '').str.replace('壮族自治区', '').str.replace('回族自治区', '')
    
    # 按省份聚合城市数据
    city_data = temp_data[temp_data['类型'] == '市'].copy()
    if not city_data.empty:
        province_population = city_data.groupby('省份')[year_column].sum().reset_index()
        province_population.columns = ['省份', '人口数量']
    else:
        province_population = pd.DataFrame(columns=['省份', '人口数量'])
    
    # 合并省份数据
    if not province_data.empty:
        for _, row in province_data.iterrows():
            province_name = row['省份']
            pop_value = row[year_column]
            if province_name in province_population['省份'].values:
                province_population.loc[province_population['省份'] == province_name, '人口数量'] += pop_value
            else:
                province_population = pd.concat([province_population, pd.DataFrame({'省份': [province_name], '人口数量': [pop_value]})], ignore_index=True)
    
    # 创建地图
    m = folium.Map(
        location=[35, 105],
        zoom_start=4,
        tiles='CartoDB dark_matter',
        attr='CartoDB'
    )
    
    # 省份名称映射
    province_mapping = {
        '北京市': '北京', '天津市': '天津', '河北省': '河北', '山西省': '山西',
        '内蒙古自治区': '内蒙古', '辽宁省': '辽宁', '吉林省': '吉林', '黑龙江省': '黑龙江',
        '上海市': '上海', '江苏省': '江苏', '浙江省': '浙江', '安徽省': '安徽',
        '福建省': '福建', '江西省': '江西', '山东省': '山东', '河南省': '河南',
        '湖北省': '湖北', '湖南省': '湖南', '广东省': '广东', '广西壮族自治区': '广西',
        '海南省': '海南', '重庆市': '重庆', '四川省': '四川', '贵州省': '贵州',
        '云南省': '云南', '西藏自治区': '西藏', '陕西省': '陕西', '甘肃省': '甘肃',
        '青海省': '青海', '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆'
    }
    
    # 人口颜色方案（蓝色系渐变）
    def get_population_color(population):
        if population < 1000000:
            return '#1a237e'  # 深蓝
        elif population < 5000000:
            return '#283593'
        elif population < 10000000:
            return '#303f9f'
        elif population < 20000000:
            return '#3949ab'
        elif population < 40000000:
            return '#3f51b5'
        elif population < 60000000:
            return '#5c6bc0'
        elif population < 80000000:
            return '#7986cb'
        else:
            return '#9fa8da'  # 浅蓝
    
    if geojson_data:
        for feature in geojson_data['features']:
            province_name = feature['properties']['name']
            population = 0
            matched = False
            
            # 匹配省份
            for full_name, short_name in province_mapping.items():
                if short_name in province_name or province_name in short_name:
                    match_data = province_population[province_population['省份'].str.contains(short_name, na=False)]
                    if not match_data.empty:
                        population = match_data['人口数量'].values[0]
                        matched = True
                        break
            
            if matched and population > 0:
                color = get_population_color(population)
                
                popup_html = f"""
                <div style='font-family: Arial; padding: 10px;'>
                    <h4 style='margin: 0 0 10px 0; color: #333; font-size: 24px; font-weight: bold;'>{province_name}</h4>
                    <p style='margin: 5px 0; font-size: 20px;'><b>年份:</b> {year}年</p>
                    <p style='margin: 5px 0; font-size: 22px;'><b>人口数量:</b> <span style='color: #3f51b5; font-weight: bold;'>{population:,}</span></p>
                </div>
                """
                
                folium.GeoJson(
                    feature,
                    style_function=lambda x, fill=color: {
                        'fillColor': fill,
                        'color': '#00ffff',  # 荧光蓝边框
                        'weight': 1.5,
                        'fillOpacity': 0.7,
                        'opacity': 0.9
                    },
                    popup=folium.Popup(popup_html, max_width=280)
                ).add_to(m)
            else:
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        'fillColor': '#f5f5f5',
                        'color': '#cccccc',
                        'weight': 1,
                        'fillOpacity': 0.3,
                        'opacity': 0.5
                    }
                ).add_to(m)
    
    return m, province_population

# ==================== 图表可视化 ====================
def create_province_bar_chart(province_stats, brand_name, top_n=15):
    """创建省份分布条形图"""
    if province_stats.empty:
        return None
    
    top_provinces = province_stats.head(top_n).sort_values('门店数量')
    
    # 品牌配色（使用有效的 Plotly colorscale）
    color_map = {
        '蜜雪冰城': 'Reds',
        '古茗': 'Blues',
        '茶百道': 'Greens',
        '霸王茶姬': 'Oranges',
        '奈雪的茶': 'pinkyl',  # 使用有效的 colorscale
        '喜茶': 'Purples'
    }
    
    color_scale = color_map.get(brand_name, 'Reds')
    
    fig = px.bar(
        top_provinces,
        x='门店数量',
        y='省份',
        orientation='h',
        title=f'{brand_name}各省门店数量 TOP{top_n}',
        color='门店数量',
        color_continuous_scale=color_scale,
        height=400
    )
    
    fig.update_layout(
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='#e2e8f0',
        title_font_color='#38bdf8',
        title_font_size=25,
        xaxis=dict(gridcolor='#475569'),
        yaxis=dict(gridcolor='#475569'),
        margin=dict(l=100, r=20, t=50, b=20)
    )
    
    return fig

def create_city_distribution_pie(shop_data, brand_name, top_n=10):
    """创建城市分布饼图"""
    if shop_data is None or shop_data.empty or '城市' not in shop_data.columns:
        return None
    
    city_counts = shop_data['城市'].value_counts().head(top_n)
    
    # 创建饼图
    fig = px.pie(
        values=city_counts.values,
        names=city_counts.index,
        title=f'{brand_name}TOP{top_n}城市分布',
        height=500  # 增大高度
    )
    
    # 更新文本样式，显示城市名称和百分比
    fig.update_traces(
        textinfo='label+percent',  # 显示城市名称和百分比
        textposition='auto',  # 自动调整文本位置
        textfont_size=12,
        textfont_color='#ffffff',
        textfont_family='Arial',
        hovertemplate='<b>%{label}</b><br>门店数量: %{value}<br>占比: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='#e2e8f0',
        title_font_color='#38bdf8',
        title_font_size=25,
        showlegend=True,
        legend=dict(
            font=dict(color='#e2e8f0', size=11),
            bgcolor='rgba(30, 41, 59, 0.8)',
            bordercolor='#475569',
            borderwidth=1
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_population_bar_chart(province_population, year, top_n=15):
    """创建人口分布条形图"""
    if province_population.empty:
        return None
    
    top_provinces = province_population.nlargest(top_n, '人口数量').sort_values('人口数量')
    
    fig = px.bar(
        top_provinces,
        x='人口数量',
        y='省份',
        orientation='h',
        title=f'{year}年各省人口数量 TOP{top_n}',
        color='人口数量',
        color_continuous_scale='Blues',
        height=400
    )
    
    fig.update_layout(
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='#e2e8f0',
        title_font_color='#38bdf8',
        title_font_size=25,
        xaxis=dict(gridcolor='#475569', title='人口数量'),
        yaxis=dict(gridcolor='#475569'),
        margin=dict(l=100, r=20, t=50, b=20)
    )
    
    return fig

def create_population_trend(population_data):
    """创建人口趋势图（2000-2020）"""
    if population_data is None or population_data.empty:
        return None
    
    # 获取省份数据
    province_data = population_data[population_data['类型'] == '省'].copy()
    if province_data.empty:
        return None
    
    # 准备数据
    years = [2000, 2010, 2020]
    year_columns = [f'人口（{year}/11/1人口普查）' for year in years]
    
    # 选择TOP10省份
    top10_provinces = province_data.nlargest(10, '人口（2020/11/1人口普查）')['地名'].tolist()
    
    # 创建趋势数据
    trend_data = []
    for province in top10_provinces:
        province_row = province_data[province_data['地名'] == province]
        if not province_row.empty:
            for year, col in zip(years, year_columns):
                if col in province_row.columns:
                    pop_value = province_row[col].values[0]
                    trend_data.append({
                        '省份': province.replace('省', '').replace('自治区', '').replace('维吾尔自治区', '').replace('壮族自治区', '').replace('回族自治区', ''),
                        '年份': year,
                        '人口数量': pop_value
                    })
    
    if not trend_data:
        return None
    
    trend_df = pd.DataFrame(trend_data)
    
    fig = px.line(
        trend_df,
        x='年份',
        y='人口数量',
        color='省份',
        title='TOP10省份人口变化趋势（2000-2020）',
        markers=True,
        height=400
    )
    
    fig.update_layout(
        paper_bgcolor='#1e293b',
        plot_bgcolor='#1e293b',
        font_color='#e2e8f0',
        title_font_color='#38bdf8',
        title_font_size=25,
        xaxis=dict(gridcolor='#475569', title='年份'),
        yaxis=dict(gridcolor='#475569', title='人口数量'),
        legend=dict(font=dict(color='#e2e8f0'), bgcolor='rgba(30, 41, 59, 0.8)'),
        margin=dict(l=60, r=20, t=50, b=20)
    )
    
    return fig

def create_wordcloud(discussion_data, brand_name):
    """根据品牌评论生成词云图"""
    if discussion_data is None or discussion_data.empty:
        return None
    
    if '品牌' not in discussion_data.columns or '评论内容' not in discussion_data.columns:
        return None
    
    # 筛选对应品牌的评论
    brand_comments = discussion_data[discussion_data['品牌'] == brand_name].copy()
    
    if brand_comments.empty:
        return None
    
    # 合并所有评论内容
    all_text = ' '.join(brand_comments['评论内容'].dropna().astype(str).tolist())
    
    if not all_text or len(all_text.strip()) < 10:
        return None
    
    # 中文停用词列表
    stopwords = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
        '奶茶', '品牌', '这个', '那个', '什么', '怎么', '可以', '还是', '就是', '如果', '因为', '所以', '但是', '不过', '而且', '然后', '现在', '已经', '还是', '真的',
        '喝', '买', '点', '吃', '做', '用', '来', '去', '说', '看', '想', '觉得', '感觉', '认为', '知道', '觉得', '感觉', '认为', '知道',
        '店', '家', '杯', '次', '个', '块', '元', '钱', '价', '格', '便宜', '贵', '好', '坏', '不错', '一般', '还行', '很好', '非常好',
        '蜜雪冰城', '古茗', '茶百道', '霸王茶姬', '奈雪的茶', '喜茶', '奶茶店', '茶饮', '饮品'
    }
    
    # 使用jieba分词
    try:
        # 提取关键词
        keywords = jieba.analyse.extract_tags(all_text, topK=100, withWeight=False)
        
        # 过滤停用词和单字
        filtered_keywords = [w for w in keywords if len(w) > 1 and w not in stopwords]
        
        if not filtered_keywords:
            # 如果关键词提取失败，使用普通分词
            words = jieba.cut(all_text)
            filtered_keywords = [w for w in words if len(w) > 1 and w not in stopwords and w.strip()]
        
        if not filtered_keywords:
            return None
        
        # 生成词频字典
        word_freq = {}
        for word in filtered_keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 品牌配色方案
        color_schemes = {
            '蜜雪冰城': ['#FF6B9D', '#FF9EBC', '#FFD1DC', '#E63977'],
            '古茗': ['#5AADFF', '#8AC8FF', '#C3E3FF', '#2A8FE6'],
            '茶百道': ['#5AFF8C', '#8AFFB3', '#C3FFD9', '#2AE65C'],
            '霸王茶姬': ['#FBBF24', '#FCD34D', '#FDE68A', '#F59E0B'],
            '奈雪的茶': ['#F472B6', '#F9A8D4', '#FBCFE8', '#EC4899'],
            '喜茶': ['#818CF8', '#A5B4FC', '#C7D2FE', '#6366F1']
        }
        
        colors = color_schemes.get(brand_name, ['#38bdf8', '#60a5fa', '#93c5fd', '#0ea5e9'])
        
        # 创建词云图
        def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            return np.random.choice(colors)
        
        # 设置中文字体
        try:
            import platform
            if platform.system() == 'Windows':
                font_path = 'C:/Windows/Fonts/simhei.ttf'  # 黑体
                if not Path(font_path).exists():
                    font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微软雅黑
            else:
                font_path = None
        except:
            font_path = None
        
        wordcloud = WordCloud(
            width=850,
            height=500,
            background_color='#1e293b',  # 深色背景
            max_words=100,
            relative_scaling=0.5,
            colormap=None,
            color_func=color_func,
            font_path=font_path,
            prefer_horizontal=0.7,
            min_font_size=10,
            max_font_size=60,
            collocations=False
        ).generate_from_frequencies(word_freq)
        
        # 转换为图像
        fig, ax = plt.subplots(figsize=(12.5, 8.3), facecolor='#1e293b')
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_facecolor('#1e293b')
        fig.patch.set_facecolor('#1e293b')
        
        # 转换为PIL图像以便在Streamlit中显示
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor='#1e293b', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        return None

def create_population_comparison(population_data, shop_data, brand_name):
    """创建人口与门店对比散点图"""
    if shop_data is None or shop_data.empty:
        return None, None
    
    # 检查是否有城市列
    if '城市' not in shop_data.columns:
        return None, None
    
    # 按城市统计门店
    city_shop_count = shop_data['城市'].value_counts().reset_index()
    city_shop_count.columns = ['城市', '门店数量']
    
    # 合并人口数据
    if population_data is not None and not population_data.empty:
        city_pop = population_data[population_data['类型'] == '市'].copy()
        city_pop = city_pop.drop_duplicates(subset=['地名'])
        
        merged = city_pop.merge(
            city_shop_count,
            left_on='地名',
            right_on='城市',
            how='inner'
        )
        
        if not merged.empty:
            # 计算相关系数
            pop_values = merged['人口（2020/11/1人口普查）'].values
            shop_values = merged['门店数量'].values
            correlation = np.corrcoef(pop_values, shop_values)[0, 1]
            
            # 品牌配色方案（与地图配色对应）
            brand_color_schemes = {
                '蜜雪冰城': ['#FFF0F5', '#FFD1DC', '#FF9EBC', '#FF6B9D', '#E63977'],
                '古茗': ['#F0F9FF', '#C3E3FF', '#8AC8FF', '#5AADFF', '#2A8FE6'],
                '茶百道': ['#F0FFF5', '#C3FFD9', '#8AFFB3', '#5AFF8C', '#2AE65C'],
                '霸王茶姬': ['#FEF3C7', '#FDE68A', '#FCD34D', '#FBBF24', '#F59E0B'],
                '奈雪的茶': ['#FCE7F3', '#FBCFE8', '#F9A8D4', '#F472B6', '#EC4899'],
                '喜茶': ['#E0E7FF', '#C7D2FE', '#A5B4FC', '#818CF8', '#6366F1']
            }
            
            # 获取品牌配色方案
            brand_colors = brand_color_schemes.get(brand_name, brand_color_schemes['蜜雪冰城'])
            
            # 创建自定义colorscale（从浅到深，使用品牌配色）
            # Plotly的color_continuous_scale需要特定格式：[[0, 'color1'], [0.5, 'color2'], [1, 'color3']]
            n_colors = len(brand_colors)
            custom_colorscale = []
            for i, color in enumerate(brand_colors):
                ratio = i / (n_colors - 1) if n_colors > 1 else 0
                custom_colorscale.append([ratio, color])
            
            # 创建散点图
            fig = px.scatter(
                merged,
                x='人口（2020/11/1人口普查）',
                y='门店数量',
                size='门店数量',
                color='门店数量',
                hover_name='城市',
                title=f'{brand_name}门店数量与人口关系（相关系数: {correlation:.3f}）',
                trendline="ols",
                height=350,
                color_continuous_scale=custom_colorscale
            )
            
            fig.update_layout(
                paper_bgcolor='#1e293b',
                plot_bgcolor='#1e293b',
                font_color='#e2e8f0',
                title_font_color='#38bdf8',
                title_font_size=30,
                xaxis=dict(gridcolor='#475569', title='人口数量'),
                yaxis=dict(gridcolor='#475569', title='门店数量')
            )
            
            # 添加相关系数注释
            fig.add_annotation(
                x=0.02,
                y=0.98,
                xref='paper',
                yref='paper',
                text=f'相关系数: {correlation:.3f}',
                showarrow=False,
                font=dict(size=30, color='#38bdf8', family='Arial'),
                bgcolor='rgba(30, 41, 59, 0.8)',
                bordercolor='#475569',
                borderwidth=1,
                borderpad=4
            )
            
            return fig, correlation
    
    return None, None

# ==================== Logo加载 ====================
def get_brand_logo_base64(brand_name):
    """获取品牌logo的base64编码"""
    import os
    import base64
    from pathlib import Path
    
    # 品牌名称到logo文件名的映射
    brand_logo_map = {
        '蜜雪冰城': 'mixue.jpg',
        '古茗': 'guming.jpg',
        '茶百道': 'chabaidao.jpg',
        '霸王茶姬': 'bawangchaji.jpg',
        '奈雪的茶': 'naixuedecha.jpg',
        '喜茶': 'xicha.jpg'
    }
    
    logo_filename = brand_logo_map.get(brand_name)
    if not logo_filename:
        return None
    
    # 尝试多个路径
    base_paths = [
        Path("F:/visualization/logo"),  # 绝对路径
        Path("logo"),  # 相对路径
        Path.cwd() / "logo"  # 当前工作目录
    ]
    
    for base_path in base_paths:
        logo_path = base_path / logo_filename
        if logo_path.exists():
            try:
                # 读取图片并转换为base64
                with open(logo_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    # 根据文件扩展名确定MIME类型
                    ext = logo_path.suffix.lower()
                    mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png' if ext == '.png' else 'image/jpeg'
                    return f"data:{mime_type};base64,{img_base64}"
            except Exception as e:
                print(f"Error reading logo file: {e}")
                return None
    
    return None

def get_brand_logo_path(brand_name):
    """获取品牌logo路径（备用方法）"""
    import os
    from pathlib import Path
    
    # 品牌名称到logo文件名的映射
    brand_logo_map = {
        '蜜雪冰城': 'mixue.jpg',
        '古茗': 'guming.jpg',
        '茶百道': 'chabaidao.jpg',
        '霸王茶姬': 'bawangchaji.jpg',
        '奈雪的茶': 'naixuedecha.jpg',
        '喜茶': 'xicha.jpg'
    }
    
    logo_filename = brand_logo_map.get(brand_name)
    if not logo_filename:
        return None
    
    # 尝试多个路径
    base_paths = [
        Path("F:/visualization/logo"),  # 绝对路径
        Path("logo"),  # 相对路径
        Path.cwd() / "logo"  # 当前工作目录
    ]
    
    for base_path in base_paths:
        logo_path = base_path / logo_filename
        if logo_path.exists():
            return str(logo_path)
    
    return None

# ==================== 主应用 ====================
def main():
    # 加载数据
    with st.spinner('正在加载数据...'):
        data = load_data()
    
    # 检查数据加载情况
    pop_data = data.get('population')
    if pop_data is None:
        st.error("❌ 无法加载人口数据")
        
        # 显示路径信息
        import os
        abs_path = Path("F:/visualization/data/population.csv")
        rel_path = Path("data/population.csv")
        cwd_path = Path.cwd() / "data" / "population.csv"
        
        st.info(f"""
        💡 请检查数据文件路径：
        - 绝对路径: {abs_path} (存在: {abs_path.exists()})
        - 相对路径: {rel_path} (存在: {rel_path.exists()})
        - 工作目录路径: {cwd_path} (存在: {cwd_path.exists()})
        - 当前工作目录: {os.getcwd()}
        """)
        return
    
    if isinstance(pop_data, pd.DataFrame) and pop_data.empty:
        st.error("❌ 人口数据文件为空")
        return
    
    # 获取可用品牌
    available_brands = [k for k, v in data.items() if k != 'population' and k != 'discussion' and v is not None and isinstance(v, pd.DataFrame) and not v.empty]
    
    if not available_brands:
        st.error("❌ 没有可用的品牌数据")
        st.info("💡 请检查 data 文件夹中是否有品牌数据文件（如 mixue.csv, guming.csv, chabaidao.csv 等）")
        return
    
    # ==================== 顶部导航栏 ====================
    st.markdown("""
    <div class="top-nav">
        <div class="nav-title">🍵 中国奶茶店分布与人口数据可视化大屏</div>
        <div class="nav-selector"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 顶部选择器
    col1, col2, col3 = st.columns([1, 1, 6])
    
    with col1:
        view_type = st.selectbox(
            "视图类型",
            ["品牌分布", "人口分布", "对比分析"],
            label_visibility="visible"
        )
    
    with col2:
        if view_type == "品牌分布":
            selected_brand = st.selectbox(
                "选择品牌",
                available_brands,
                label_visibility="visible"
            )
        elif view_type == "人口分布":
            selected_year = st.selectbox(
                "选择年份",
                [2020, 2010, 2000],
                index=0,
                label_visibility="visible"
            )
        else:
            selected_brand = st.selectbox(
                "选择品牌",
                available_brands,
                label_visibility="visible"
            )
    
    # ==================== 主内容区域 ====================
    if view_type == "品牌分布":
        # 获取品牌数据
        brand_data = preprocess_brand_data(data[selected_brand])
        
        if brand_data is None or brand_data.empty:
            st.warning(f"{selected_brand}数据为空")
            return
        
        # 获取GeoJSON
        geojson = get_china_geojson()
        
        # 计算统计数据
        province_stats = get_province_stats(brand_data)
        total_shops = len(brand_data)
        total_cities = brand_data['城市'].nunique() if '城市' in brand_data.columns else 0
        total_provinces = brand_data['省份'].nunique() if '省份' in brand_data.columns else 0
        
        # ==================== KPI指标 ====================
        st.markdown('<div style="margin: 1rem 0;">', unsafe_allow_html=True)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{total_shops:,}</div>
                <div class="kpi-label">🏪 总门店数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{total_cities:,}</div>
                <div class="kpi-label">🏙️ 覆盖城市数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{total_provinces:,}</div>
                <div class="kpi-label">🗺️ 覆盖省份数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi4:
            coverage = (total_provinces / 34 * 100) if total_provinces > 0 else 0
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{coverage:.1f}%</div>
                <div class="kpi-label">📈 省份覆盖率</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== 主地图区域（中心地图+周围小图布局）====================
        st.markdown(f"""
        <div style="margin: 1.5rem 0;">
            <h3 class="section-title">🗺️ {selected_brand}全国分布地图</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 创建地图
        brand_map = create_brand_map(brand_data, selected_brand, geojson)
        
        if brand_map:
            # 使用网格布局：上方小图、中间地图、下方小图
            # 第一行：上方小图
            col_top1, col_top2, col_top3, col_top4 = st.columns(4)
            
            with col_top1:
                if not province_stats.empty:
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥇 TOP1</div>', unsafe_allow_html=True)
                    top1 = province_stats.iloc[0]
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#38bdf8; margin:0.5rem 0;"><b>{top1["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#94a3b8; margin:0;">{top1["门店数量"]:,}家</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top2:
                if len(province_stats) > 1:
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥈 TOP2</div>', unsafe_allow_html=True)
                    top2 = province_stats.iloc[1]
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#38bdf8; margin:0.5rem 0;"><b>{top2["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#94a3b8; margin:0;">{top2["门店数量"]:,}家</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top3:
                if len(province_stats) > 2:
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥉 TOP3</div>', unsafe_allow_html=True)
                    top3 = province_stats.iloc[2]
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#38bdf8; margin:0.5rem 0;"><b>{top3["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:3.0rem; color:#94a3b8; margin:0;">{top3["门店数量"]:,}家</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top4:
                # 统计信息显示在上方空白框中
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 统计信息</div>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">总门店: <span style="color:#38bdf8;">{total_shops:,}</span></p>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">覆盖城市: <span style="color:#38bdf8;">{total_cities:,}</span></p>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">覆盖省份: <span style="color:#38bdf8;">{total_provinces:,}</span></p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 中间：主地图、logo和词云图（三列布局）
            # 使用自定义样式优化布局 - 移除absolute定位，确保logo在column内
            st.markdown("""
            <style>
                /* Logo容器样式 - 不使用absolute定位，确保在column内正常显示 */
                .logo-container {
                    text-align: center;
                    padding: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 700px;
                }
                .logo-img {
                    width: 100%;
                    height: auto;
                    max-height: 800px;
                    object-fit: contain;
                    border-radius: 8px;
                }
                /* 地图容器 */
                .map-container {
                    margin-right: 0.3rem !important;
                }
                /* 词云容器 */
                .wordcloud-container {
                    margin-left: 0.3rem !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            # 三列布局：地图、logo、词云图
            col_map_left, col_logo, col_map_right = st.columns([1,1,1], gap="small")
            
            with col_map_left:
                st.markdown('<div class="chart-wrapper map-container" style="margin: 1rem 0.3rem 1rem 0;">', unsafe_allow_html=True)
                folium_static(brand_map, width=1400, height=700)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_logo:
                # Logo显示在中间列（红色矩形框位置）
                # 确保logo完全在column内部，不使用absolute定位
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                logo_base64 = get_brand_logo_base64(selected_brand)
                if logo_base64:
                    # 优先使用base64编码显示图片 - 直接在column内渲染
                    logo_html = f'<div class="logo-container"><img src="{logo_base64}" class="logo-img" /></div>'
                    st.markdown(logo_html, unsafe_allow_html=True)
                else:
                    # 备用方法：尝试使用文件路径
                    logo_path = get_brand_logo_path(selected_brand)
                    if logo_path:
                        try:
                            from pathlib import Path
                            logo_file = Path(logo_path)
                            if logo_file.exists():
                                # 使用st.image在column内显示
                                st.markdown('<div class="logo-container">', unsafe_allow_html=True)
                                # 尝试使用相对路径
                                rel_path = f"logo/{logo_file.name}"
                                if Path(rel_path).exists():
                                    st.image(rel_path, use_container_width=True)
                                else:
                                    # 使用绝对路径
                                    st.image(str(logo_file), use_container_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                            else:
                                st.info(f"Logo文件未找到: {logo_path}")
                        except Exception as e:
                            st.error(f"加载logo时出错: {str(e)}")
                    else:
                        st.info(f"暂无{selected_brand}的logo")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_map_right:
                # 词云图
                st.markdown('<div class="chart-wrapper wordcloud-container" style="margin: 1rem 0 1rem 0.5rem;">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">💬 评论词云</div>', unsafe_allow_html=True)
                
                # 生成词云图
                wordcloud_buf = create_wordcloud(data.get('discussion'), selected_brand)
                if wordcloud_buf:
                    st.image(wordcloud_buf, width=None)
                else:
                    st.info("暂无评论数据或评论数据不足")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 下方：左右分布的小图
            col_bottom_left, col_bottom_right = st.columns(2)
            
            with col_bottom_left:
                # 省份分布条形图
                if not province_stats.empty:
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">📊 各省门店数量 TOP15</div>', unsafe_allow_html=True)
                    bar_fig = create_province_bar_chart(province_stats, selected_brand, top_n=15)
                    if bar_fig:
                        st.plotly_chart(bar_fig, use_container_width=True, config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_bottom_right:
                # 城市分布饼图
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">🏙️ TOP10城市分布</div>', unsafe_allow_html=True)
                pie_fig = create_city_distribution_pie(brand_data, selected_brand, top_n=10)
                if pie_fig:
                    st.plotly_chart(pie_fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 人口对比图（单独一行）
            pop_fig, correlation = create_population_comparison(data['population'], brand_data, selected_brand)
            if pop_fig:
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">👥 门店数量与人口关系分析</div>', unsafe_allow_html=True)
                if correlation is not None:
                    st.markdown(f'<p style="font-size: 2.0rem; color: #38bdf8; margin-bottom: 0.5rem;">📊 相关系数: <strong>{correlation:.3f}</strong></p>', unsafe_allow_html=True)
                st.plotly_chart(pop_fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
        
    elif view_type == "人口分布":
        # 获取人口数据
        pop_data = data.get('population')
        
        if pop_data is None or pop_data.empty:
            st.error("无法加载人口数据")
            return
        
        # 获取GeoJSON
        geojson = get_china_geojson()
        
        # 创建人口分布地图
        population_map, province_population = create_population_map(pop_data, selected_year, geojson)
        
        if population_map is None:
            st.error("无法创建人口分布地图")
            return
        
        # 计算统计数据
        total_population = province_population['人口数量'].sum() if not province_population.empty else 0
        avg_population = province_population['人口数量'].mean() if not province_population.empty else 0
        max_province = province_population.loc[province_population['人口数量'].idxmax()] if not province_population.empty else None
        min_province = province_population.loc[province_population['人口数量'].idxmin()] if not province_population.empty else None
        
        # ==================== KPI指标 ====================
        st.markdown('<div style="margin: 1rem 0;">', unsafe_allow_html=True)
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{total_population/100000000:.2f}亿</div>
                <div class="kpi-label">👥 总人口数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{avg_population/10000:.0f}万</div>
                <div class="kpi-label">📊 平均人口</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3:
            if max_province is not None:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{max_province['省份']}</div>
                    <div class="kpi-label">🥇 人口最多</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="kpi-card">
                    <div class="kpi-value">-</div>
                    <div class="kpi-label">🥇 人口最多</div>
                </div>
                """, unsafe_allow_html=True)
        
        with kpi4:
            if min_province is not None:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{min_province['省份']}</div>
                    <div class="kpi-label">🥉 人口最少</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="kpi-card">
                    <div class="kpi-value">-</div>
                    <div class="kpi-label">🥉 人口最少</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ==================== 主地图区域 ====================
        st.markdown(f"""
        <div style="margin: 1.5rem 0;">
            <h3 class="section-title">🗺️ {selected_year}年中国人口分布地图</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 上方：TOP3省份
        col_top1, col_top2, col_top3, col_top4 = st.columns(4)
        
        if not province_population.empty:
            top3_provinces = province_population.nlargest(3, '人口数量')
            
            with col_top1:
                if len(top3_provinces) > 0:
                    top1 = top3_provinces.iloc[0]
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥇 TOP1</div>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#38bdf8; margin:0.5rem 0;"><b>{top1["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#94a3b8; margin:0;">{top1["人口数量"]/10000:.0f}万人</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top2:
                if len(top3_provinces) > 1:
                    top2 = top3_provinces.iloc[1]
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥈 TOP2</div>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#38bdf8; margin:0.5rem 0;"><b>{top2["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#94a3b8; margin:0;">{top2["人口数量"]/10000:.0f}万人</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top3:
                if len(top3_provinces) > 2:
                    top3 = top3_provinces.iloc[2]
                    st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">🥉 TOP3</div>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#38bdf8; margin:0.5rem 0;"><b>{top3["省份"]}</b></p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="text-align:center; font-size:2.5rem; color:#94a3b8; margin:0;">{top3["人口数量"]/10000:.0f}万人</p>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            with col_top4:
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 统计信息</div>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">总人口: <span style="color:#38bdf8;">{total_population/100000000:.2f}亿</span></p>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">省份数: <span style="color:#38bdf8;">{len(province_population)}</span></p>', unsafe_allow_html=True)
                st.markdown(f'<p style="margin:0.5rem 0; font-size:2.5rem;">平均人口: <span style="color:#38bdf8;">{avg_population/10000:.0f}万</span></p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 中间：主地图
        st.markdown('<div class="chart-wrapper" style="margin: 1rem 0;">', unsafe_allow_html=True)
        folium_static(population_map, width=1200, height=700)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 下方：左右分布的小图
        col_bottom_left, col_bottom_right = st.columns(2)
        
        with col_bottom_left:
            # 人口分布条形图
            if not province_population.empty:
                st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 各省人口数量 TOP15</div>', unsafe_allow_html=True)
                bar_fig = create_population_bar_chart(province_population, selected_year, top_n=15)
                if bar_fig:
                    st.plotly_chart(bar_fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col_bottom_right:
            # 人口趋势图
            st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📈 人口变化趋势（2000-2020）</div>', unsafe_allow_html=True)
            trend_fig = create_population_trend(pop_data)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # 对比分析
        brand_data = preprocess_brand_data(data[selected_brand])
        if brand_data is not None and not brand_data.empty:
            st.markdown(f"""
            <div style="margin: 1.5rem 0;">
                <h3 class="section-title">📊 {selected_brand}与人口分布对比分析</h3>
            </div>
            """, unsafe_allow_html=True)
            
            comparison_fig, correlation = create_population_comparison(data['population'], brand_data, selected_brand)
            if comparison_fig:
                if correlation is not None:
                    st.markdown(f'<p style="font-size: 2.5rem; color: #38bdf8; margin-bottom: 0.5rem;">📊 相关系数: <strong>{correlation:.3f}</strong></p>', unsafe_allow_html=True)
                st.plotly_chart(comparison_fig, use_container_width=True)

if __name__ == "__main__":
    main()

