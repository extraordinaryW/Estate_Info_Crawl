# 房产信息爬虫项目

这是一个结构化的房产信息爬虫项目，包含京东法拍房和链家二手房两个爬虫模块。

## 项目结构

```
estate_info_crawl/
├── config.py                 # 配置文件
├── main.py                   # 主程序入口
├── requirements.txt          # 项目依赖
├── README.md                # 项目说明
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── logger.py            # 日志工具
│   ├── browser.py           # 浏览器工具
│   └── data_storage.py      # 数据存储工具
├── spiders/                 # 爬虫模块
│   ├── __init__.py
│   ├── base_spider.py       # 爬虫基类
│   ├── jd_auction_spider.py # 京东法拍房爬虫
│   └── lianjia_spider.py    # 链家二手房爬虫
├── data/                    # 数据目录
├── logs/                    # 日志目录
└── output/                  # 输出目录
```

## 功能特性

### 京东法拍房爬虫
- 使用undetected-chromedriver绕过反爬虫检测
- 支持手动登录京东账号
- 自动选择地区（广东-深圳）
- 爬取拍卖详情信息
- 自动下载附件和图片
- 支持分页爬取
- **支持截止时间过滤**：当拍卖结束时间早于设定时间时自动停止爬取
- 数据保存为Excel格式

### 链家二手房爬虫
- 支持深圳所有区域的二手房数据爬取
- 自动处理登录验证
- 支持分页爬取
- 数据按区域分别保存
- 支持日期过滤

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 京东法拍房爬虫

首次运行：
```bash
python main.py --spider jd
```
程序会自动：
1. 创建Chrome用户数据目录
2. 打开京东法拍网站
3. 提示您手动登录
4. 登录成功后自动保存登录信息

程序会自动：
1. 检测登录状态
2. 如果已登录，直接开始爬取
3. 如果登录失效，提示重新登录

```bash
# 基本使用
python main.py --spider jd

# 指定开始页码和最大页数
python main.py --spider jd --jd-start-page 5 --jd-max-pages 10

# 使用截止时间功能（只爬取结束时间在指定时间之后的拍卖）
python main.py --spider jd --jd-cutoff-time "2024年01月01日 00:00:00"

# 组合使用多个参数
python main.py --spider jd --jd-start-page 1 --jd-max-pages 20 --jd-cutoff-time "2024年01月01日 12:00:00"
```

### 2. 链家二手房爬虫

```bash
# 爬取所有区域
python main.py --spider lianjia

# 爬取指定区域
python main.py --spider lianjia --lianjia-districts 南山区 福田区

# 限制每个区域的最大页数
python main.py --spider lianjia --lianjia-max-pages 5
```

### 3. 同时运行两个爬虫

```bash
python main.py --spider both
```

### 4. 查看可用区域

```bash
python main.py --show-districts --spider xx
```

## 配置说明

所有配置参数都在 `config.py` 文件中，包括：

- 浏览器配置
- 爬虫参数
- 区域映射
- 日志设置
- 输出路径

## 输出文件

- 京东法拍房数据：`output/京东法拍房_数据.xlsx`
- 链家二手房数据：`output/链家二手房_区域名.xlsx`
- 日志文件：`logs/爬虫名称.log`
- 附件和图片：`output/京东法拍/资产名称/`

## 注意事项

1. **京东法拍房爬虫**：
   - 使用undetected-chromedriver自动启动浏览器
   - 每次运行都需要手动登录京东账号
   - 建议在非工作时间运行，避免被反爬
   - **截止时间功能**：
     - 时间格式必须为：`YYYY年MM月DD日 HH:MM:SS`
     - 例如：`2024年01月15日 12:30:00`
     - 当发现拍卖结束时间早于截止时间时，爬虫会停止并保存已收集的数据
     - 该功能可用于只爬取最近的拍卖数据，提高效率

2. **链家二手房爬虫**：
   - 程序会自动打开浏览器
   - 需要手动完成登录验证
   - 建议设置合理的延时和页数限制

3. **通用注意事项**：
   - 请遵守网站的robots.txt规则
   - 建议设置合理的爬取频率
   - 数据仅供学习研究使用

## 扩展开发

### 添加新的爬虫

1. 继承 `BaseSpider` 类
2. 实现 `run()` 方法
3. 在 `main.py` 中添加相应的参数处理

### 修改配置

直接编辑 `config.py` 文件中的相应配置项。

### 自定义数据存储

继承或修改 `DataStorage` 类来实现自定义的数据存储方式。

## 许可证

本项目仅供学习和研究使用，请遵守相关网站的使用条款。 