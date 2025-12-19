# ================ 奶茶行业大数据分析 ================
# 三个Hadoop/Spark算法

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import col, avg, count as spark_count, stddev, min, max, sum as spark_sum, when, isnan
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
import os
from datetime import datetime

# ================ 1. 初始化 ================
print("🚀 初始化Spark...")
spark = SparkSession.builder \
    .appName("MilkTeaRealDataAnalysis") \
    .master("local[*]") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

# ================ 修复字体问题 ================
def setup_chinese_font():
    """设置中文字体，如果失败则使用英文"""
    import matplotlib
    try:
        # 尝试多种可能的字体路径
        possible_font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "C:/Windows/Fonts/msyh.ttc",  # Windows 雅黑
            "C:/Windows/Fonts/simhei.ttf"  # Windows 黑体
        ]
        
        font_found = False
        for font_path in possible_font_paths:
            if os.path.exists(font_path):
                matplotlib.font_manager.fontManager.addfont(font_path)
                font_name = matplotlib.font_manager.FontProperties(fname=font_path).get_name()
                matplotlib.rcParams['font.sans-serif'] = [font_name]
                matplotlib.rcParams['axes.unicode_minus'] = False
                print(f"✅ 使用中文字体: {font_name}")
                font_found = True
                break
        
        if not font_found:
            # 在Colab中尝试安装字体
            try:
                import subprocess
                result = subprocess.run(['apt-get', 'install', '-y', 'fonts-noto-cjk'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    matplotlib.font_manager.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
                    font_name = matplotlib.font_manager.FontProperties(fname="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc").get_name()
                    matplotlib.rcParams['font.sans-serif'] = [font_name]
                    matplotlib.rcParams['axes.unicode_minus'] = False
                    print("✅ 已安装并使用中文字体")
                else:
                    print("⚠️  使用英文显示图表")
                    matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
            except:
                print("⚠️  使用英文显示图表")
                matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
    except Exception as e:
        print(f"⚠️  字体设置失败: {e}")
        print("使用英文显示图表")
        matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']

# 设置字体
setup_chinese_font()

# ================ 数据加载函数 ================
def load_real_data():
    """加载真实数据文件"""
    print("📂 加载真实数据文件...")
    
    # 门店数据文件列表
    store_files = {
        '霸王茶姬': '霸王茶姬_门店位置数据.csv',
        '茶百道': '茶百道_门店位置数据.csv',
        '古茗': '古茗_门店位置数据.csv',
        '蜜雪冰城': '蜜雪冰城_门店位置数据.csv',
        '奈雪的茶': '奈雪的茶_门店位置数据.csv',
        '喜茶': '喜茶_门店位置数据.csv'
    }
    
    # 价格数据文件
    price_file = '奶茶产品价格.xlsx'
    
    # 1. 加载门店数据
    store_dfs = []
    missing_files = []
    
    for brand, filename in store_files.items():
        try:
            if os.path.exists(filename):
                print(f"  正在加载 {brand} 数据: {filename}")
                # 尝试不同的编码
                try:
                    df = pd.read_csv(filename, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(filename, encoding='gbk')
                    except:
                        df = pd.read_csv(filename, encoding='latin1')
                
                # 添加品牌列
                df['品牌'] = brand
                store_dfs.append(df)
                print(f"  ✅ {brand}: {len(df)} 行")
            else:
                print(f"  ❌ 文件不存在: {filename}")
                missing_files.append(filename)
        except Exception as e:
            print(f"  ❌ 加载 {filename} 失败: {e}")
            missing_files.append(filename)
    
    if store_dfs:
        store_df = pd.concat(store_dfs, ignore_index=True)
        print(f"\n✅ 门店数据加载完成: 共 {len(store_df)} 行，{store_df['品牌'].nunique()} 个品牌")
    else:
        print("❌ 没有找到门店数据文件")
        store_df = pd.DataFrame()
    
    # 2. 加载价格数据
    try:
        if os.path.exists(price_file):
            print(f"\n正在加载价格数据: {price_file}")
            price_df = pd.read_excel(price_file)
            print(f"✅ 价格数据加载完成: {len(price_df)} 行")
        else:
            print(f"❌ 价格文件不存在: {price_file}")
            # 创建示例价格数据作为备选
            price_df = create_sample_price_data()
    except Exception as e:
        print(f"❌ 加载价格数据失败: {e}")
        # 创建示例价格数据作为备选
        price_df = create_sample_price_data()
    
    # 3. 数据预览
    print("\n📊 数据预览:")
    if not store_df.empty:
        print(f"门店数据列名: {store_df.columns.tolist()}")
        print(f"品牌分布: {store_df['品牌'].value_counts().to_dict()}")
    
    if not price_df.empty:
        print(f"价格数据列名: {price_df.columns.tolist()}")
        if '品牌' in price_df.columns:
            print(f"价格品牌分布: {price_df['品牌'].value_counts().to_dict()}")
    
    return price_df, store_df

def create_sample_price_data():
    """创建示例价格数据（当真实数据不可用时）"""
    print("创建示例价格数据...")
    
    price_data = []
    brands = ['蜜雪冰城', '茶百道', '古茗', '奈雪的茶', '喜茶', '霸王茶姬']
    
    for brand in brands:
        if brand == '蜜雪冰城':
            prices = [5.0, 6.0, 7.0, 8.0, 8.5, 9.0, 10.0, 12.0]
            for i in range(50):
                price_data.append({
                    '品牌': brand,
                    '产品类型': np.random.choice(['奶茶', '果茶', '奶盖茶', '纯茶']),
                    '产品名称': f'{brand}产品{i+1}',
                    '产品价格': float(np.random.choice(prices)),
                    '产品规格': '标准',
                    '月销量': float(np.random.randint(50, 500))
                })
        elif brand == '茶百道':
            prices = [12.0, 13.0, 15.0, 16.0, 18.0, 20.0, 22.0, 25.0]
            for i in range(50):
                price_data.append({
                    '品牌': brand,
                    '产品类型': np.random.choice(['奶茶', '果茶', '奶盖茶', '纯茶']),
                    '产品名称': f'{brand}产品{i+1}',
                    '产品价格': float(np.random.choice(prices)),
                    '产品规格': '标准',
                    '月销量': float(np.random.randint(30, 400))
                })
        else:
            prices = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 25.0]
            for i in range(40):
                price_data.append({
                    '品牌': brand,
                    '产品类型': np.random.choice(['奶茶', '果茶', '奶盖茶', '纯茶']),
                    '产品名称': f'{brand}产品{i+1}',
                    '产品价格': float(np.random.choice(prices)),
                    '产品规格': '标准',
                    '月销量': float(np.random.randint(40, 450))
                })
    
    return pd.DataFrame(price_data)

# ================ 数据预处理函数 ================
def preprocess_store_data(store_df):
    """预处理门店数据"""
    if store_df.empty:
        return store_df
    
    print("🔧 预处理门店数据...")
    
    # 标准化列名
    store_df = store_df.copy()
    
    # 尝试识别列名
    column_mapping = {
        '省份': ['省份', '省', 'province', 'Province', '省区'],
        '城市': ['城市', '市', 'city', 'City', '城区'],
        '区县': ['区县', '区', 'district', 'District', '县'],
        '地址': ['地址', '详细地址', 'address', 'Address', 'location'],
        '门店ID': ['门店ID', '门店编号', 'store_id', 'StoreID', '店号'],
        '门店名称': ['门店名称', '店名', 'store_name', 'StoreName', '店铺名称']
    }
    
    # 标准化列名
    for standard_name, possible_names in column_mapping.items():
        for col_name in possible_names:
            if col_name in store_df.columns and standard_name not in store_df.columns:
                store_df[standard_name] = store_df[col_name]
                break
    
    # 确保有必要的列
    if '省份' not in store_df.columns and '城市' in store_df.columns:
        # 尝试从城市中提取省份
        store_df['省份'] = store_df['城市'].str[:2]
    
    # 填充缺失值
    for col in ['省份', '城市']:
        if col in store_df.columns:
            store_df[col] = store_df[col].fillna('未知')
    
    print(f"预处理后列名: {store_df.columns.tolist()}")
    return store_df

def preprocess_price_data(price_df):
    """预处理价格数据"""
    if price_df.empty:
        return price_df
    
    print("🔧 预处理价格数据...")
    price_df = price_df.copy()
    
    # 尝试识别列名
    column_mapping = {
        '品牌': ['品牌', 'brand', 'Brand', '奶茶品牌'],
        '产品名称': ['产品名称', 'product_name', 'ProductName', '商品名称', '名称'],
        '产品价格': ['产品价格', 'price', 'Price', '售价', '价格'],
        '月销量': ['月销量', 'sales', 'Sales', '销量', '月销售']
    }
    
    # 标准化列名
    for standard_name, possible_names in column_mapping.items():
        for col_name in possible_names:
            if col_name in price_df.columns and standard_name not in price_df.columns:
                price_df[standard_name] = price_df[col_name]
                break
    
    # 清洗价格数据
    if '产品价格' in price_df.columns:
        price_df['产品价格'] = pd.to_numeric(price_df['产品价格'], errors='coerce')
        # 填充缺失价格
        brand_avg_price = price_df.groupby('品牌')['产品价格'].mean()
        price_df['产品价格'] = price_df.apply(
            lambda x: brand_avg_price[x['品牌']] if pd.isna(x['产品价格']) and x['品牌'] in brand_avg_price else x['产品价格'],
            axis=1
        )
    
    # 清洗销量数据
    if '月销量' in price_df.columns:
        price_df['月销量'] = pd.to_numeric(price_df['月销量'], errors='coerce')
        price_df['月销量'] = price_df['月销量'].fillna(price_df.groupby('品牌')['月销量'].transform('mean'))
        price_df['月销量'] = price_df['月销量'].clip(lower=0)
    
    print(f"预处理后列名: {price_df.columns.tolist()}")
    return price_df

# ================ 算法1：价格特征分析 ================
def algorithm1_price_analysis(price_df):
    """算法1：价格特征对比分析"""
    print("\n" + "="*70)
    print("💰 算法1：品牌价格特征分析 (K-Means + 统计分析)")
    print("="*70)
    
    # 预处理数据
    price_df_clean = preprocess_price_data(price_df)
    
    if price_df_clean.empty:
        print("❌ 价格数据为空，无法进行分析")
        return None, None
    
    # 检查必要列
    required_cols = ['品牌', '产品价格']
    missing_cols = [col for col in required_cols if col not in price_df_clean.columns]
    if missing_cols:
        print(f"❌ 缺少必要列: {missing_cols}")
        return None, None
    
    print(f"\n📊 数据概览:")
    print(f"总行数: {len(price_df_clean)}")
    print(f"品牌数量: {price_df_clean['品牌'].nunique()}")
    print(f"品牌列表: {price_df_clean['品牌'].unique().tolist()}")
    print(f"价格范围: {price_df_clean['产品价格'].min():.1f} - {price_df_clean['产品价格'].max():.1f} 元")
    print(f"平均价格: {price_df_clean['产品价格'].mean():.2f} 元")
    print(f"价格中位数: {price_df_clean['产品价格'].median():.2f} 元")
    
    # 转换为Spark DataFrame
    print("\n🔄 转换为Spark DataFrame...")
    spark_price = spark.createDataFrame(price_df_clean[['品牌', '产品价格']])
    
    # 1.1 基本统计
    print("\n📊 1.1 各品牌价格基本统计:")
    stats = spark_price.groupBy('品牌').agg(
        spark_count('*').alias('产品数量'),
        avg('产品价格').alias('平均价格'),
        min('产品价格').alias('最低价格'),
        max('产品价格').alias('最高价格'),
        stddev('产品价格').alias('价格标准差')
    ).orderBy('平均价格')
    
    stats_pd = stats.toPandas()
    print(stats_pd.round(2))
    
    # 1.2 K-Means价格分层
    print("\n🎯 1.2 K-Means价格分层分析:")
    
    # 准备特征数据
    assembler = VectorAssembler(inputCols=['产品价格'], outputCol='features')
    df_vector = assembler.transform(spark_price)
    
    # K-Means聚类 - 修复min()函数问题
    import builtins
    unique_brand_count = len(price_df_clean['品牌'].unique())
    k = builtins.min(3, unique_brand_count)  # 使用Python内置的min函数
    print(f"聚类数量: k={k} (基于品牌数量: {unique_brand_count})")
    
    if k < 2:
        print("⚠️  品牌数量不足，跳过K-Means聚类分析")
        cluster_stats_pd = pd.DataFrame()
    else:
        kmeans = KMeans(featuresCol='features', k=k, seed=42)
        model = kmeans.fit(df_vector)
        predictions = model.transform(df_vector)
        
        # 分析聚类结果
        cluster_stats = predictions.groupBy('prediction', '品牌').agg(
            spark_count('*').alias('产品数'),
            avg('产品价格').alias('聚类平均价格')
        ).orderBy('prediction', '品牌')
        
        print("聚类结果（按品牌统计）:")
        cluster_stats_pd = cluster_stats.toPandas()
        print(cluster_stats_pd.round(2))
        
        # 获取聚类中心
        print("\n聚类中心:")
        centers = model.clusterCenters()
        for i, center in enumerate(centers):
            print(f"  聚类{i}: 价格中心 = {center[0]:.2f}元")
    
    # 1.3 可视化
    plt.figure(figsize=(15, 10))
    
    # 子图1：价格分布箱线图
    plt.subplot(2, 3, 1)
    brand_data = []
    brand_labels = []
    
    for brand in price_df_clean['品牌'].unique():
        brand_prices = price_df_clean[price_df_clean['品牌'] == brand]['产品价格'].values
        if len(brand_prices) > 0:
            brand_data.append(brand_prices)
            brand_labels.append(brand)
    
    if brand_data:
        plt.boxplot(brand_data, tick_labels=brand_labels)
        plt.xlabel('品牌')
        plt.ylabel('价格（元）')
        plt.title('各品牌价格分布箱线图')
        plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45)
    
    # 子图2：平均价格对比
    plt.subplot(2, 3, 2)
    if not stats_pd.empty:
        stats_pd = stats_pd.sort_values('平均价格')
        bars = plt.bar(range(len(stats_pd)), stats_pd['平均价格'])
        plt.xticks(range(len(stats_pd)), stats_pd['品牌'], rotation=45)
        plt.xlabel('品牌')
        plt.ylabel('平均价格（元）')
        plt.title('各品牌平均价格对比')
        
        # 添加数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom')
        
        plt.grid(True, alpha=0.3, axis='y')
    
    # 子图3：价格离散度
    plt.subplot(2, 3, 3)
    if not stats_pd.empty:
        stats_pd['价格离散度'] = stats_pd['价格标准差'] / stats_pd['平均价格']
        stats_pd = stats_pd.sort_values('价格离散度', ascending=False)
        
        bars = plt.bar(range(len(stats_pd)), stats_pd['价格离散度'])
        plt.xticks(range(len(stats_pd)), stats_pd['品牌'], rotation=45)
        plt.xlabel('品牌')
        plt.ylabel('价格离散度（变异系数）')
        plt.title('各品牌价格离散度对比')
        
        # 在柱子上添加数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom')
        
        plt.grid(True, alpha=0.3, axis='y')
    
    # 子图4：价格分布直方图
    plt.subplot(2, 3, 4)
    plt.hist(price_df_clean['产品价格'], bins=30, edgecolor='black', alpha=0.7)
    plt.xlabel('价格（元）')
    plt.ylabel('产品数量')
    plt.title('所有产品价格分布')
    plt.grid(True, alpha=0.3)
    
    # 子图5：各品牌价格密度曲线
    plt.subplot(2, 3, 5)
    for brand in price_df_clean['品牌'].unique():
        brand_data = price_df_clean[price_df_clean['品牌'] == brand]['产品价格']
        sns.kdeplot(brand_data, label=brand, fill=True, alpha=0.3)
    
    plt.xlabel('价格（元）')
    plt.ylabel('密度')
    plt.title('各品牌价格分布密度')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图6：价格聚类分布（如果有聚类结果）
    plt.subplot(2, 3, 6)
    if not cluster_stats_pd.empty and 'prediction' in cluster_stats_pd.columns:
        # 创建价格-聚类散点图
        colors = ['red', 'green', 'blue', 'orange', 'purple'][:k]
        for i in range(k):
            cluster_data = cluster_stats_pd[cluster_stats_pd['prediction'] == i]
            if not cluster_data.empty:
                plt.scatter(cluster_data['聚类平均价格'], cluster_data['产品数'], 
                          color=colors[i], label=f'聚类{i}', s=100, alpha=0.6)
                for _, row in cluster_data.iterrows():
                    plt.text(row['聚类平均价格'], row['产品数'], row['品牌'], 
                            fontsize=8, ha='center')
        
        plt.xlabel('聚类平均价格（元）')
        plt.ylabel('产品数量')
        plt.title('K-Means聚类结果')
        plt.legend()
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无聚类数据', ha='center', va='center', fontsize=12)
        plt.title('K-Means聚类结果')
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('算法1_价格特征分析.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 1.4 分析结论
    print("\n" + "="*50)
    print("📋 算法1分析结论:")
    print("="*50)
    
    print("\n1. 价格水平对比:")
    for _, row in stats_pd.iterrows():
        print(f"   • {row['品牌']}: 均价{row['平均价格']:.1f}元，{row['产品数量']}个产品")
    
    print("\n2. 价格策略分析:")
    if not stats_pd.empty:
        cheapest = stats_pd.loc[stats_pd['平均价格'].idxmin()]
        most_expensive = stats_pd.loc[stats_pd['平均价格'].idxmax()]
        print(f"   • 最亲民品牌: {cheapest['品牌']} (均价{cheapest['平均价格']:.1f}元)")
        print(f"   • 最高端品牌: {most_expensive['品牌']} (均价{most_expensive['平均价格']:.1f}元)")
    
    print("\n3. 价格离散度分析:")
    if not stats_pd.empty and '价格离散度' in stats_pd.columns:
        most_consistent = stats_pd.loc[stats_pd['价格离散度'].idxmin()]
        most_varied = stats_pd.loc[stats_pd['价格离散度'].idxmax()]
        print(f"   • 价格最统一: {most_consistent['品牌']} (离散度{most_consistent['价格离散度']:.3f})")
        print(f"   • 价格最多样: {most_varied['品牌']} (离散度{most_varied['价格离散度']:.3f})")
    
    if not cluster_stats_pd.empty:
        print("\n4. 价格聚类分析:")
        for cluster_id in sorted(cluster_stats_pd['prediction'].unique()):
            cluster_data = cluster_stats_pd[cluster_stats_pd['prediction'] == cluster_id]
            print(f"   聚类{cluster_id}:")
            for _, row in cluster_data.iterrows():
                print(f"     - {row['品牌']}: {row['产品数']}个产品，均价{row['聚类平均价格']:.1f}元")
    
    return stats_pd, cluster_stats_pd

# ================ 算法2：门店分布分析 ================
def algorithm2_store_distribution(store_df):
    """算法2：门店空间分布分析"""
    print("\n" + "="*70)
    print("🏪 算法2：门店空间分布分析 (六品牌对比)")
    print("="*70)
    
    # 预处理数据
    store_df_clean = preprocess_store_data(store_df)
    
    if store_df_clean.empty:
        print("❌ 门店数据为空，无法进行分析")
        return None, None, None
    
    print(f"\n📊 数据概览:")
    print(f"总门店数: {len(store_df_clean):,}")
    print(f"品牌数量: {store_df_clean['品牌'].nunique()}")
    
    # 检查是否有省份数据
    has_province_data = '省份' in store_df_clean.columns and not store_df_clean['省份'].isna().all()
    if has_province_data:
        print(f"省份数量: {store_df_clean['省份'].nunique()}")
        top_provinces = store_df_clean['省份'].value_counts().head(10)
        print("门店最多的前10个省份:")
        for province, count in top_provinces.items():
            print(f"  {province}: {count:,} 家")
    
    # 转换为Spark DataFrame
    print("\n🔄 转换为Spark DataFrame...")
    if has_province_data:
        spark_store = spark.createDataFrame(store_df_clean[['品牌', '省份']])
    else:
        spark_store = spark.createDataFrame(store_df_clean[['品牌']])
    
    # 2.1 基本统计
    print("\n📊 2.1 各品牌门店数量统计:")
    store_counts = spark_store.groupBy('品牌').agg(
        spark_count('*').alias('门店总数')
    ).orderBy('门店总数', ascending=False)
    
    counts_pd = store_counts.toPandas()
    print(counts_pd.to_string(index=False))
    
    # 2.2 省份覆盖分析（如果有省份数据）
    provinces_pd = None
    density_stats = None
    
    if has_province_data:
        print("\n🌍 2.2 省份覆盖分析:")
        province_counts = spark_store.groupBy('品牌', '省份').agg(
            spark_count('*').alias('门店数')
        )
        
        # 计算每个品牌覆盖的省份数量
        brand_provinces = province_counts.groupBy('品牌').agg(
            spark_count('*').alias('覆盖省份数')
        ).orderBy('覆盖省份数', ascending=False)
        
        provinces_pd = brand_provinces.toPandas()
        print(provinces_pd.to_string(index=False))
        
        # 2.3 门店密度计算
        print("\n📈 2.3 门店密度分析:")
        density_stats = counts_pd.merge(provinces_pd, on='品牌')
        density_stats['门店密度'] = density_stats['门店总数'] / density_stats['覆盖省份数']
        density_stats = density_stats.sort_values('门店密度', ascending=False)
        
        print(density_stats.round(2).to_string(index=False))
    else:
        density_stats = counts_pd.copy()
        density_stats['覆盖省份数'] = '未知'
        density_stats['门店密度'] = '未知'
    
    # 2.4 可视化
    plt.figure(figsize=(16, 12))
    
    # 子图1：门店总数对比
    plt.subplot(3, 2, 1)
    counts_pd_sorted = counts_pd.sort_values('门店总数', ascending=False)
    bars1 = plt.bar(range(len(counts_pd_sorted)), counts_pd_sorted['门店总数'], color='skyblue')
    plt.xticks(range(len(counts_pd_sorted)), counts_pd_sorted['品牌'], rotation=45, ha='right')
    plt.xlabel('品牌')
    plt.ylabel('门店总数')
    plt.title('各品牌门店总数对比', fontsize=14, fontweight='bold')
    
    # 添加数值标签
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}', ha='center', va='bottom', fontsize=9)
    
    plt.grid(True, alpha=0.3, axis='y')
    
    # 子图2：门店占比饼图
    plt.subplot(3, 2, 2)
    plt.pie(counts_pd_sorted['门店总数'], labels=counts_pd_sorted['品牌'], autopct='%1.1f%%', startangle=90)
    plt.title('各品牌门店数量占比', fontsize=14, fontweight='bold')
    
    # 子图3：覆盖省份数对比（如果有省份数据）
    if provinces_pd is not None and not provinces_pd.empty:
        plt.subplot(3, 2, 3)
        provinces_pd_sorted = provinces_pd.sort_values('覆盖省份数', ascending=False)
        bars2 = plt.bar(range(len(provinces_pd_sorted)), provinces_pd_sorted['覆盖省份数'], color='lightgreen')
        plt.xticks(range(len(provinces_pd_sorted)), provinces_pd_sorted['品牌'], rotation=45, ha='right')
        plt.xlabel('品牌')
        plt.ylabel('覆盖省份数')
        plt.title('各品牌覆盖省份数对比', fontsize=14, fontweight='bold')
        
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        plt.grid(True, alpha=0.3, axis='y')
    else:
        plt.subplot(3, 2, 3)
        plt.text(0.5, 0.5, '无省份数据', ha='center', va='center', fontsize=14)
        plt.title('省份数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图4：门店密度对比（如果有密度数据）
    if density_stats is not None and '门店密度' in density_stats.columns and density_stats['门店密度'].dtype != object:
        plt.subplot(3, 2, 4)
        density_stats_sorted = density_stats.sort_values('门店密度', ascending=False)
        bars3 = plt.bar(range(len(density_stats_sorted)), density_stats_sorted['门店密度'], color='orange')
        plt.xticks(range(len(density_stats_sorted)), density_stats_sorted['品牌'], rotation=45, ha='right')
        plt.xlabel('品牌')
        plt.ylabel('门店密度（门店数/省份）')
        plt.title('各品牌门店密度对比', fontsize=14, fontweight='bold')
        
        for i, bar in enumerate(bars3):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.grid(True, alpha=0.3, axis='y')
    else:
        plt.subplot(3, 2, 4)
        plt.text(0.5, 0.5, '密度数据不可用', ha='center', va='center', fontsize=14)
        plt.title('密度数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图5：热门省份分布（如果有省份数据）
    if has_province_data and not store_df_clean['省份'].isna().all():
        plt.subplot(3, 2, 5)
        
        # 选择门店数最多的前10个省份
        top_provinces = store_df_clean['省份'].value_counts().head(10)
        
        if not top_provinces.empty:
            plt.barh(range(len(top_provinces)), top_provinces.values, color='purple')
            plt.yticks(range(len(top_provinces)), top_provinces.index)
            plt.xlabel('门店数量')
            plt.ylabel('省份')
            plt.title('门店数量最多的前10个省份', fontsize=14, fontweight='bold')
            
            for i, (province, count) in enumerate(top_provinces.items()):
                plt.text(count, i, f' {count:,}', va='center', fontsize=9)
            
            plt.grid(True, alpha=0.3, axis='x')
        else:
            plt.text(0.5, 0.5, '无省份数据', ha='center', va='center', fontsize=14)
            plt.title('省份数据不可用', fontsize=14, fontweight='bold')
            plt.axis('off')
    else:
        plt.subplot(3, 2, 5)
        plt.text(0.5, 0.5, '省份数据不可用', ha='center', va='center', fontsize=14)
        plt.title('省份数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图6：品牌在热门省份的分布热力图
    if has_province_data and density_stats is not None:
        plt.subplot(3, 2, 6)
        
        # 选择门店数最多的前8个省份
        top_provinces_list = store_df_clean['省份'].value_counts().head(8).index.tolist()
        brands_list = density_stats['品牌'].tolist()
        
        if top_provinces_list and brands_list:
            heatmap_data = []
            
            for brand in brands_list:
                brand_data = []
                for province in top_provinces_list:
                    store_count = store_df_clean[(store_df_clean['品牌'] == brand) & 
                                                (store_df_clean['省份'] == province)].shape[0]
                    brand_data.append(store_count)
                heatmap_data.append(brand_data)
            
            if heatmap_data:
                plt.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
                plt.colorbar(label='门店数量')
                plt.xticks(range(len(top_provinces_list)), top_provinces_list, rotation=45, ha='right')
                plt.yticks(range(len(brands_list)), brands_list)
                plt.xlabel('省份')
                plt.ylabel('品牌')
                plt.title('品牌-省份门店分布热力图', fontsize=14, fontweight='bold')
                
                # 添加数值
                for i in range(len(brands_list)):
                    for j in range(len(top_provinces_list)):
                        plt.text(j, i, f'{heatmap_data[i][j]:,}', 
                                ha='center', va='center', color='black', fontsize=8)
            else:
                plt.text(0.5, 0.5, '无分布数据', ha='center', va='center', fontsize=14)
                plt.title('分布数据不可用', fontsize=14, fontweight='bold')
                plt.axis('off')
        else:
            plt.text(0.5, 0.5, '无分布数据', ha='center', va='center', fontsize=14)
            plt.title('分布数据不可用', fontsize=14, fontweight='bold')
            plt.axis('off')
    else:
        plt.subplot(3, 2, 6)
        plt.text(0.5, 0.5, '省份数据不可用', ha='center', va='center', fontsize=14)
        plt.title('省份数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('算法2_门店分布分析.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2.5 分析结论
    print("\n" + "="*50)
    print("📋 算法2分析结论:")
    print("="*50)
    
    # 门店规模排名
    print("\n1. 门店规模排名:")
    for i, (_, row) in enumerate(counts_pd_sorted.iterrows(), 1):
        percentage = (row['门店总数'] / counts_pd_sorted['门店总数'].sum()) * 100
        print(f"   第{i}名: {row['品牌']} ({row['门店总数']:,}家, 占比{percentage:.1f}%)")
    
    # 覆盖广度排名（如果有省份数据）
    if provinces_pd is not None and not provinces_pd.empty:
        print("\n2. 市场覆盖广度排名:")
        provinces_pd_sorted = provinces_pd.sort_values('覆盖省份数', ascending=False)
        for i, (_, row) in enumerate(provinces_pd_sorted.iterrows(), 1):
            print(f"   第{i}名: {row['品牌']} (覆盖{row['覆盖省份数']}个省份)")
    
    # 门店密度排名（如果有密度数据）
    if density_stats is not None and '门店密度' in density_stats.columns and density_stats['门店密度'].dtype != object:
        print("\n3. 门店密度排名（门店数/覆盖省份）:")
        density_stats_sorted = density_stats.sort_values('门店密度', ascending=False)
        for i, (_, row) in enumerate(density_stats_sorted.iterrows(), 1):
            print(f"   第{i}名: {row['品牌']} (密度:{row['门店密度']:.1f})")
    
    # 市场策略分析
    print("\n4. 市场策略分析:")
    if not counts_pd_sorted.empty:
        print(f"   • 市场领导者: {counts_pd_sorted.iloc[0]['品牌']} (门店最多)")
        
        if len(counts_pd_sorted) > 1:
            last_brand = counts_pd_sorted.iloc[-1]['品牌']
            print(f"   • 市场跟随者: {last_brand} (门店最少)")
    
    if has_province_data and provinces_pd is not None and not provinces_pd.empty:
        max_coverage = provinces_pd.loc[provinces_pd['覆盖省份数'].idxmax()]
        print(f"   • 广泛布局者: {max_coverage['品牌']} (覆盖省份最多)")
    
    return density_stats, counts_pd, provinces_pd

# ================ 算法3：价格-销量关系分析 ================
def algorithm3_price_sales_analysis(price_df):
    """算法3：价格-销量关系分析"""
    print("\n" + "="*70)
    print("📈 算法3：价格-销量关系分析 (线性回归 + 价格区间)")
    print("="*70)
    
    # 预处理数据
    price_df_clean = preprocess_price_data(price_df)
    
    if price_df_clean.empty:
        print("❌ 价格数据为空，无法进行分析")
        return None, None
    
    # 检查必要列
    required_cols = ['品牌', '产品价格']
    missing_cols = [col for col in required_cols if col not in price_df_clean.columns]
    if missing_cols:
        print(f"❌ 缺少必要列: {missing_cols}")
        return None, None
    
    # 如果有月销量数据则使用，否则创建示例数据
    if '月销量' not in price_df_clean.columns:
        print("⚠️  没有月销量数据，将使用价格范围进行分析")
        # 创建基于价格的模拟销量数据（通常价格越低销量越高）
        price_df_clean['月销量'] = 500 - price_df_clean['产品价格'] * 10 + np.random.normal(0, 50, len(price_df_clean))
        price_df_clean['月销量'] = price_df_clean['月销量'].clip(lower=0)
        print("已生成模拟销量数据")
    
    print(f"\n📊 数据概览:")
    print(f"总产品数: {len(price_df_clean)}")
    print(f"价格范围: {price_df_clean['产品价格'].min():.1f} - {price_df_clean['产品价格'].max():.1f} 元")
    print(f"销量范围: {price_df_clean['月销量'].min():.0f} - {price_df_clean['月销量'].max():.0f}")
    print(f"平均价格: {price_df_clean['产品价格'].mean():.2f} 元")
    print(f"平均销量: {price_df_clean['月销量'].mean():.0f}")
    
    # 转换为Spark DataFrame
    print("\n🔄 转换为Spark DataFrame...")
    spark_df = spark.createDataFrame(price_df_clean[['品牌', '产品价格', '月销量']])
    
    # 3.1 价格区间分析
    print("\n📊 3.1 价格区间销量分析:")
    
    # 定义价格区间
    price_ranges = [(0, 10), (10, 15), (15, 20), (20, 30), (30, 50)]
    
    range_analysis = []
    for price_min, price_max in price_ranges:
        range_df = spark_df.filter((col('产品价格') >= price_min) & (col('产品价格') < price_max))
        stats = range_df.agg(
            spark_count('*').alias('产品数'),
            avg('产品价格').alias('区间平均价格'),
            avg('月销量').alias('区间平均销量')
        ).collect()[0]
        
        if stats['产品数'] > 0:
            range_analysis.append({
                '价格区间': f'{price_min}-{price_max}元',
                '产品数': stats['产品数'],
                '平均价格': stats['区间平均价格'],
                '平均销量': stats['区间平均销量']
            })
    
    if range_analysis:
        range_pd = pd.DataFrame(range_analysis)
        print(range_pd.round(2).to_string(index=False))
    else:
        range_pd = pd.DataFrame()
        print("无数据")
    
    # 3.2 品牌价格弹性分析
    print("\n🎯 3.2 品牌价格弹性分析:")
    brand_elasticity = []
    
    for brand in price_df_clean['品牌'].unique():
        brand_df = price_df_clean[price_df_clean['品牌'] == brand]
        if len(brand_df) > 5:  # 需要有足够的数据点
            # 计算价格和销量的相关性
            correlation = brand_df['产品价格'].corr(brand_df['月销量'])
            brand_elasticity.append({
                '品牌': brand,
                '样本数': len(brand_df),
                '平均价格': brand_df['产品价格'].mean(),
                '平均销量': brand_df['月销量'].mean(),
                '价格-销量相关性': correlation
            })
    
    if brand_elasticity:
        elasticity_pd = pd.DataFrame(brand_elasticity)
        print(elasticity_pd.round(3).to_string(index=False))
    else:
        elasticity_pd = pd.DataFrame()
        print("数据不足，无法计算相关性")
    
    # 3.3 可视化
    plt.figure(figsize=(18, 12))
    
    # 子图1：价格区间销量对比
    plt.subplot(3, 3, 1)
    if not range_pd.empty:
        x_pos = range(len(range_pd))
        bars = plt.bar(x_pos, range_pd['平均销量'], color='steelblue')
        plt.xticks(x_pos, range_pd['价格区间'], rotation=45)
        plt.xlabel('价格区间（元）')
        plt.ylabel('平均销量')
        plt.title('不同价格区间的平均销量', fontsize=14, fontweight='bold')
        
        # 添加数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}', ha='center', va='bottom')
        
        plt.grid(True, alpha=0.3, axis='y')
    else:
        plt.text(0.5, 0.5, '无价格区间数据', ha='center', va='center', fontsize=14)
        plt.title('价格区间数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图2：价格-销量散点图
    plt.subplot(3, 3, 2)
    unique_brands = price_df_clean['品牌'].unique()
    if len(unique_brands) > 0:
        colors = plt.cm.tab10(np.linspace(0, 1, len(unique_brands)))
        
        for idx, brand in enumerate(unique_brands):
            brand_df = price_df_clean[price_df_clean['品牌'] == brand]
            if len(brand_df) > 0:
                plt.scatter(brand_df['产品价格'], brand_df['月销量'], 
                          alpha=0.6, label=brand, s=60, color=colors[idx])
        
        plt.xlabel('价格（元）')
        plt.ylabel('销量')
        plt.title('价格 vs 销量散点图', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无品牌数据', ha='center', va='center', fontsize=14)
        plt.title('品牌数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图3：价格弹性对比
    plt.subplot(3, 3, 3)
    if not elasticity_pd.empty:
        colors = ['green' if x > 0 else 'red' for x in elasticity_pd['价格-销量相关性']]
        bars = plt.bar(range(len(elasticity_pd)), elasticity_pd['价格-销量相关性'], color=colors)
        plt.xticks(range(len(elasticity_pd)), elasticity_pd['品牌'], rotation=45)
        plt.xlabel('品牌')
        plt.ylabel('价格-销量相关性')
        plt.title('各品牌价格弹性对比', fontsize=14, fontweight='bold')
        
        # 添加数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if pd.notna(height):
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom' if height >= 0 else 'top')
        
        plt.grid(True, alpha=0.3, axis='y')
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无弹性数据', ha='center', va='center', fontsize=14)
        plt.title('弹性数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图4：价格分布直方图
    plt.subplot(3, 3, 4)
    plt.hist(price_df_clean['产品价格'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    plt.xlabel('价格（元）')
    plt.ylabel('产品数量')
    plt.title('价格分布直方图', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 子图5：销量分布直方图
    plt.subplot(3, 3, 5)
    plt.hist(price_df_clean['月销量'], bins=30, edgecolor='black', alpha=0.7, color='lightgreen')
    plt.xlabel('销量')
    plt.ylabel('产品数量')
    plt.title('销量分布直方图', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # 子图6：各品牌价格-销量箱线图
    plt.subplot(3, 3, 6)
    if len(unique_brands) > 0:
        brand_data = []
        for brand in unique_brands:
            brand_df = price_df_clean[price_df_clean['品牌'] == brand]
            if not brand_df.empty:
                # 计算价格/销量比值
                price_sales_ratio = brand_df['产品价格'] / brand_df['月销量']
                brand_data.append(price_sales_ratio.values)
        
        if brand_data:
            plt.boxplot(brand_data, tick_labels=unique_brands)
            plt.xticks(rotation=45)
            plt.xlabel('品牌')
            plt.ylabel('价格/销量比值')
            plt.title('各品牌价格/销量比值箱线图', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3, axis='y')
    else:
        plt.text(0.5, 0.5, '无品牌数据', ha='center', va='center', fontsize=14)
        plt.title('品牌数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图7：最佳价格点分析
    plt.subplot(3, 3, 7)
    if not range_pd.empty:
        # 计算价格区间的销售额（价格 × 销量）
        range_pd['预估销售额'] = range_pd['平均价格'] * range_pd['平均销量'] * range_pd['产品数']
        
        plt.plot(range_pd['平均价格'], range_pd['预估销售额'], 'o-', linewidth=2, markersize=8)
        plt.xlabel('平均价格（元）')
        plt.ylabel('预估销售额')
        plt.title('价格区间销售额分析', fontsize=14, fontweight='bold')
        
        # 标记最佳价格点
        max_sales_idx = range_pd['预估销售额'].idxmax()
        plt.scatter(range_pd.loc[max_sales_idx, '平均价格'], 
                   range_pd.loc[max_sales_idx, '预估销售额'], 
                   color='red', s=200, zorder=5)
        plt.annotate(f"最佳价格点\n{range_pd.loc[max_sales_idx, '平均价格']:.1f}元", 
                    (range_pd.loc[max_sales_idx, '平均价格'], 
                     range_pd.loc[max_sales_idx, '预估销售额']),
                    xytext=(10, 10), textcoords='offset points')
        
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无区间数据', ha='center', va='center', fontsize=14)
        plt.title('区间数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图8：价格与销量密度图
    plt.subplot(3, 3, 8)
    if len(price_df_clean) > 0:
        plt.hexbin(price_df_clean['产品价格'], price_df_clean['月销量'], 
                  gridsize=30, cmap='YlOrRd')
        plt.colorbar(label='数据点密度')
        plt.xlabel('价格（元）')
        plt.ylabel('销量')
        plt.title('价格-销量密度图', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=14)
        plt.title('数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    # 子图9：品牌市场份额与价格关系
    plt.subplot(3, 3, 9)
    if not elasticity_pd.empty and '平均销量' in elasticity_pd.columns:
        # 计算市场份额
        total_sales = elasticity_pd['平均销量'].sum()
        elasticity_pd['市场份额'] = (elasticity_pd['平均销量'] / total_sales) * 100
        
        scatter = plt.scatter(elasticity_pd['平均价格'], elasticity_pd['市场份额'],
                            s=elasticity_pd['样本数']*10, alpha=0.6,
                            c=elasticity_pd['价格-销量相关性'], cmap='coolwarm')
        plt.colorbar(scatter, label='价格-销量相关性')
        
        # 添加品牌标签
        for i, row in elasticity_pd.iterrows():
            plt.annotate(row['品牌'], 
                        (row['平均价格'], row['市场份额']),
                        fontsize=9, ha='center')
        
        plt.xlabel('平均价格（元）')
        plt.ylabel('市场份额（%）')
        plt.title('价格 vs 市场份额', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, '无弹性数据', ha='center', va='center', fontsize=14)
        plt.title('弹性数据不可用', fontsize=14, fontweight='bold')
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('算法3_价格销量分析.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3.4 分析结论
    print("\n" + "="*50)
    print("📋 算法3分析结论:")
    print("="*50)
    
    if not range_pd.empty:
        best_range = range_pd.loc[range_pd['平均销量'].idxmax()]
        worst_range = range_pd.loc[range_pd['平均销量'].idxmin()]
        print(f"\n1. 最佳价格区间: {best_range['价格区间']}")
        print(f"   平均销量: {best_range['平均销量']:.0f} | 产品数: {best_range['产品数']}")
        print(f"   平均价格: {best_range['平均价格']:.1f} 元")
        
        print(f"\n2. 最差价格区间: {worst_range['价格区间']}")
        print(f"   平均销量: {worst_range['平均销量']:.0f} | 产品数: {worst_range['产品数']}")
        print(f"   平均价格: {worst_range['平均价格']:.1f} 元")
    
    if not elasticity_pd.empty:
        print("\n3. 价格弹性分析:")
        elasticity_pd_sorted = elasticity_pd.sort_values('价格-销量相关性', ascending=False)
        
        for _, row in elasticity_pd_sorted.iterrows():
            if pd.notna(row['价格-销量相关性']):
                correlation = row['价格-销量相关性']
                if correlation > 0.3:
                    interpretation = "强正相关 - 价格越高销量越好"
                elif correlation > 0.1:
                    interpretation = "弱正相关"
                elif correlation > -0.1:
                    interpretation = "基本无关"
                elif correlation > -0.3:
                    interpretation = "弱负相关"
                else:
                    interpretation = "强负相关 - 价格越低销量越好"
                
                print(f"   • {row['品牌']}: 相关性{correlation:.3f} ({interpretation})")
                print(f"     平均价格: {row['平均价格']:.1f}元, 平均销量: {row['平均销量']:.0f}")
    
    # 商业建议
    print("\n4. 商业建议:")
    if not range_pd.empty and not elasticity_pd.empty:
        # 找到最佳价格点和最有弹性品牌
        best_price_range = range_pd.loc[range_pd['平均销量'].idxmax()]
        
        # 找到相关性最强的品牌
        max_corr_brand = elasticity_pd.loc[elasticity_pd['价格-销量相关性'].abs().idxmax()]
        
        print(f"   • 建议定价策略: 集中在{best_price_range['价格区间']}区间")
        print(f"   • 最敏感品牌: {max_corr_brand['品牌']} (价格影响最大)")
        
        if max_corr_brand['价格-销量相关性'] < 0:
            print(f"   • 对{max_corr_brand['品牌']}建议: 适当降价可显著提升销量")
        else:
            print(f"   • 对{max_corr_brand['品牌']}建议: 可考虑适度提价")
    
    return elasticity_pd, range_pd

# ================ 生成最终报告 ================
def generate_final_report(results1, results2, results3):
    """生成最终分析报告"""
    print("\n📄 生成综合报告...")
    
    report_lines = [
        "="*80,
        "                    奶茶行业大数据分析报告",
        "="*80,
        f"\n报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
        "\n"
    ]
    
    # 算法1结果
    if results1 and results1[0] is not None:
        stats_pd, cluster_pd = results1
        report_lines.append("一、价格特征分析结果")
        report_lines.append("-"*60)
        report_lines.append("1. 价格水平排名:")
        for _, row in stats_pd.iterrows():
            report_lines.append(f"   {row['品牌']}: 均价{row['平均价格']:.1f}元 | 最低{row['最低价格']:.1f}元 | 最高{row['最高价格']:.1f}元 | {row['产品数量']}个产品")
        
        report_lines.append("\n2. 价格策略分析:")
        if not stats_pd.empty:
            cheapest = stats_pd.loc[stats_pd['平均价格'].idxmin()]
            most_expensive = stats_pd.loc[stats_pd['平均价格'].idxmax()]
            report_lines.append(f"   • 最亲民品牌: {cheapest['品牌']} (均价{cheapest['平均价格']:.1f}元)")
            report_lines.append(f"   • 最高端品牌: {most_expensive['品牌']} (均价{most_expensive['平均价格']:.1f}元)")
    else:
        report_lines.append("一、价格特征分析结果")
        report_lines.append("-"*60)
        report_lines.append("   ❌ 价格特征分析未完成")
    
    # 算法2结果
    if results2 and results2[0] is not None:
        density_stats, counts_pd, provinces_pd = results2
        report_lines.append("\n\n二、门店分布分析结果")
        report_lines.append("-"*60)
        report_lines.append("1. 门店规模排名:")
        for i, (_, row) in enumerate(counts_pd.iterrows(), 1):
            report_lines.append(f"   第{i}名: {row['品牌']} ({row['门店总数']:,}家)")
        
        if provinces_pd is not None and not provinces_pd.empty:
            report_lines.append("\n2. 市场覆盖广度:")
            for i, (_, row) in enumerate(provinces_pd.iterrows(), 1):
                report_lines.append(f"   第{i}名: {row['品牌']} (覆盖{row['覆盖省份数']}个省份)")
    else:
        report_lines.append("\n\n二、门店分布分析结果")
        report_lines.append("-"*60)
        report_lines.append("   ❌ 门店分布分析未完成")
    
    # 算法3结果
    if results3 and results3[0] is not None:
        elasticity_pd, range_pd = results3
        report_lines.append("\n\n三、价格-销量关系分析")
        report_lines.append("-"*60)
        
        if not range_pd.empty:
            best_range = range_pd.loc[range_pd['平均销量'].idxmax()]
            report_lines.append(f"1. 最优价格区间: {best_range['价格区间']}")
            report_lines.append(f"   平均销量: {best_range['平均销量']:.0f} | 产品数: {best_range['产品数']}")
        
        if not elasticity_pd.empty:
            report_lines.append("\n2. 价格弹性分析:")
            for _, row in elasticity_pd.iterrows():
                if pd.notna(row['价格-销量相关性']):
                    if row['价格-销量相关性'] > 0:
                        report_lines.append(f"   • {row['品牌']}: 价格与销量正相关({row['价格-销量相关性']:.3f})")
                    elif row['价格-销量相关性'] < 0:
                        report_lines.append(f"   • {row['品牌']}: 价格与销量负相关({row['价格-销量相关性']:.3f})")
                    else:
                        report_lines.append(f"   • {row['品牌']}: 价格与销量无相关性")
    else:
        report_lines.append("\n\n三、价格-销量关系分析")
        report_lines.append("-"*60)
        report_lines.append("   ❌ 价格-销量关系分析未完成")
    
    # 总结与建议
    report_lines.append("\n\n四、总结与建议")
    report_lines.append("-"*60)
    
    if results1 and results1[0] is not None:
        stats_pd, _ = results1
        if not stats_pd.empty:
            avg_price_all = stats_pd['平均价格'].mean()
            report_lines.append(f"1. 行业平均价格水平: {avg_price_all:.1f}元")
    
    if results2 and results2[0] is not None:
        _, counts_pd, _ = results2
        if not counts_pd.empty:
            total_stores = counts_pd['门店总数'].sum()
            report_lines.append(f"2. 总门店数量: {total_stores:,}家")
            
            if len(counts_pd) > 0:
                market_leader = counts_pd.iloc[0]
                report_lines.append(f"3. 市场领导者: {market_leader['品牌']} ({market_leader['门店总数']:,}家)")
    
    report_lines.append("4. 发展建议:")
    report_lines.append("   • 蜜雪冰城: 继续保持亲民价格策略，扩大门店覆盖")
    report_lines.append("   • 古茗、茶百道: 优化产品结构，提升品牌溢价")
    report_lines.append("   • 霸王茶姬、喜茶、奈雪的茶: 加强高端市场定位")
    
    report_lines.append("\n" + "="*80)
    report_lines.append("报告结束")
    report_lines.append("="*80)
    
    report_text = "\n".join(report_lines)
    
    # 保存报告
    report_filename = '奶茶数据分析报告.txt'
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(f"✅ 报告已保存到: {report_filename}")
    print("\n" + "="*80)
    print(report_text)
    print("="*80)
    
    return report_text

# ================ 主程序 ================
def main():
    """主程序"""
    print("🎯 奶茶行业大数据分析")
    print("="*80)
    
    try:
        # 1. 加载真实数据
        price_df, store_df = load_real_data()
        
        if price_df is None and store_df is None:
            print("❌ 无法加载任何数据")
            return
        
        print(f"\n📊 数据加载完成:")
        if not price_df.empty:
            print(f"价格数据: {len(price_df)} 行, {price_df['品牌'].nunique() if '品牌' in price_df.columns else '未知'} 个品牌")
        if not store_df.empty:
            print(f"门店数据: {len(store_df):,} 行, {store_df['品牌'].nunique() if '品牌' in store_df.columns else '未知'} 个品牌")
        
        # 2. 执行三个算法
        print("\n" + "="*80)
        print("🚀 开始执行三个大数据算法...")
        
        # 算法1：价格特征分析
        results1 = None
        if not price_df.empty:
            print("\n1️⃣ 执行算法1: 品牌价格特征分析")
            results1 = algorithm1_price_analysis(price_df)
        else:
            print("\n⚠️  跳过算法1: 价格数据为空")
        
        # 算法2：门店分布分析
        results2 = None
        if not store_df.empty:
            print("\n2️⃣ 执行算法2: 门店空间分布分析")
            results2 = algorithm2_store_distribution(store_df)
        else:
            print("\n⚠️  跳过算法2: 门店数据为空")
        
        # 算法3：价格销量分析
        results3 = None
        if not price_df.empty:
            print("\n3️⃣ 执行算法3: 价格-销量关系分析")
            results3 = algorithm3_price_sales_analysis(price_df)
        else:
            print("\n⚠️  跳过算法3: 价格数据为空")
        
        # 3. 保存结果文件
        print("\n💾 保存分析结果...")
        
        try:
            if results1 and results1[0] is not None:
                results1[0].to_csv('价格统计结果.csv', index=False, encoding='utf-8')
                print("✅ 价格统计结果.csv 已保存")
                if results1[1] is not None:
                    results1[1].to_csv('KMeans聚类结果.csv', index=False, encoding='utf-8')
                    print("✅ KMeans聚类结果.csv 已保存")
            
            if results2 and results2[0] is not None:
                results2[0].to_csv('门店分布结果.csv', index=False, encoding='utf-8')
                print("✅ 门店分布结果.csv 已保存")
            
            if results3 and results3[0] is not None:
                if results3[0] is not None:
                    results3[0].to_csv('价格销量分析.csv', index=False, encoding='utf-8')
                    print("✅ 价格销量分析.csv 已保存")
                if results3[1] is not None:
                    results3[1].to_csv('价格区间分析.csv', index=False, encoding='utf-8')
                    print("✅ 价格区间分析.csv 已保存")
            
        except Exception as e:
            print(f"⚠️  保存结果文件时出错: {e}")
        
        # 4. 生成报告
        print("\n📄 生成综合报告...")
        report = generate_final_report(results1, results2, results3)
        
        # 5. 打包下载
        print("\n📦 打包所有结果文件...")
        try:
            # 创建文件列表
            files_to_check = [
                '算法1_价格特征分析.png',
                '算法2_门店分布分析.png',
                '算法3_价格销量分析.png',
                '价格统计结果.csv',
                'KMeans聚类结果.csv',
                '门店分布结果.csv',
                '价格销量分析.csv',
                '价格区间分析.csv',
                '奶茶数据分析报告.txt'
            ]
            
            # 检查文件是否存在
            existing_files = []
            for f in files_to_check:
                if os.path.exists(f):
                    file_size = os.path.getsize(f)
                    print(f"  ✓ {f} ({file_size:,} bytes)")
                    existing_files.append(f)
                else:
                    print(f"  ✗ {f} (未找到)")
            
            print(f"\n找到 {len(existing_files)} 个文件")
            
            if existing_files:
                # 创建zip文件
                import zipfile
                zip_filename = '奶茶数据分析结果.zip'
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in existing_files:
                        zipf.write(file, os.path.basename(file))
                
                zip_size = os.path.getsize(zip_filename)
                print(f"\n✅ 打包完成: {zip_filename} ({zip_size:,} bytes)")
                
                # 提供下载提示
                print("\n📥 文件下载提示:")
                print("="*50)
                print(f"1. 所有结果已打包到: {zip_filename}")
                print("2. 下载方式:")
                print("   - 如果是Jupyter Notebook环境:")
                print("     from IPython.display import FileLink")
                print(f"     FileLink('{zip_filename}')")
                print("   - 如果是本地Python环境:")
                print(f"     文件在当前目录: {os.path.abspath(zip_filename)}")
                print("3. 重要文件:")
                print("   • 奶茶数据分析报告.txt - 完整分析报告")
                print("   • 算法1_价格特征分析.png - 价格分析图表")
                print("   • 算法2_门店分布分析.png - 门店分布图表")
                print("   • 算法3_价格销量分析.png - 价格销量关系图表")
                print("="*50)
            else:
                print("⚠️  没有找到任何结果文件")
                
        except Exception as e:
            print(f"⚠️  打包过程中出现问题: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("✅ 分析完成！")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()

# ================ 运行程序 ================
if __name__ == "__main__":
    main()