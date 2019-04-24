# scrapy_fang
基于Scrapy-Redis架构分布式爬取房天下全国房源信息
本项目为之前学习Scrapy-Redis组件时所用案例，特整理出来以便今后复盘。
#### 安装
```
pip install scrapy-redis
```
#### 其他机器访问本机redis服务器
想要让其他机器访问本机的redis服务器，那么在本机上需要修改redis.conf的配置文件，将bind改成bind [本机的ip或者0.0.0.0]，其他机器才能访问。



---
#### 准备爬取的url分析
1. 获取所有城市的url链接 https://www.fang.com/SoufunFamily.htm
2. 获取所有城市新房的url链接。   
特例：北京：https://bj.fang.com/  
北京新房：https://newhouse.fang.com/house/s/      
一般：上海：https://sh.fang.com/  
上海新房：https://sh.newhouse.fang.com/house/s/
3. 获取所有城市二手房的url链接。   
特例：北京：https://bj.fang.com/  
北京二手房：https://esf.fang.com/  
一般：上海：https://sh.fang.com/   
上海二手房：https://sh.esf.fang.com/




---
### 一、构建常规 Scrapy 爬虫
1. 进入虚拟环境，创建scrapy项目fang，生成爬虫sfw。
```
cd study
cd scrapy
source venv/bin/activate
scrapy startproject fang
cd fang
scrapy genspider sfw "fang.com"
```
2. PyCharm 打开项目 fang，修改文件，创建爬虫。
- middlewares.py
```
import random

class UserAgentDownloadMiddleware(object):
    # user-agent 随机请求头中间件
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'
    ]
    def process_request(self,request,spider):
        user_agent = random.choice(self.USER_AGENTS)
        request.headers['User-Agent'] = user_agent
```
- settings.py
```
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3
DEFAULT_REQUEST_HEADERS = {
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language': 'en',
}

DOWNLOADER_MIDDLEWARES = {
   'fang.middlewares.UserAgentDownloadMiddleware': 543,
}

ITEM_PIPELINES = {
   'fang.pipelines.FangPipeline': 300,
}

```
- items.py
```
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewHouseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 省份
    province = scrapy.Field()
    # 城市
    city = scrapy.Field()
    # 小区的名字
    name = scrapy.Field()
    # 价格
    price = scrapy.Field()
    # 几居室（列表形式）
    rooms = scrapy.Field()
    # 面积
    area = scrapy.Field()
    # 地址
    address = scrapy.Field()
    # 行政区
    district = scrapy.Field()
    # 是否在售
    sale = scrapy.Field()
    # 房源详情页面url
    origin_url = scrapy.Field()
    
class EsfHouseItem(scrapy.Item):
    # 省份
    province = scrapy.Field()
    # 城市
    city = scrapy.Field()
    # 小区名
    name = scrapy.Field()
    # 几室几厅
    rooms = scrapy.Field()
    # 楼层
    floor = scrapy.Field()
    # 朝向
    toward = scrapy.Field()
    # 年代
    year = scrapy.Field()
    # 地址
    address = scrapy.Field()
    # 建筑面积
    area = scrapy.Field()
    # 总价
    price = scrapy.Field()
    # 单价
    unit = scrapy.Field()
    # 房源详情页面url
    origin_url = scrapy.Field()
    

```

- sfw_spider.py
```
# -*- coding: utf-8 -*-
import scrapy
import re
from fang.items import NewHouseItem,EsfHouseItem


class SfwSpider(scrapy.Spider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs = response.xpath('//div[@class="outCont"]//tr')
        province = None
        for tr in trs:
            tds = tr.xpath('.//td[not(@class)]')
            province_td = tds[0]
            province_text = province_td.xpath('.//text()').extract_first()
            province_text = re.sub(r'\s','',province_text)
            if province_text:
                province = province_text
            # 不爬取海外的城市房源
            if province == '其它':
                continue
            
            city_td = tds[1]
            city_links = city_td.xpath('.//a')
            for city_link in city_links:
                city = city_link.xpath('.//text()').extract_first()
                city_url = city_link.xpath('.//@href').extract_first()
                
                url_module = city_url.split('//')
                scheme = url_module[0]
                domain = url_module[1]
                domain_ = domain.split('.')
                domain_0 = domain_[0]+'.'
                domain_1 = domain_[1]+'.'
                domain_2 = domain_[2]
                # 北京特例
                if 'bj.' in domain:
                    newhouse_url = 'https://newhouse.fang.com/house/s/'
                    esf_url = 'https://esf.fang.com/'
            
                else:
                    # 构建新房的url链接
                    newhouse_url = scheme + '//' + domain_0 + 'newhouse.' + domain_1 + domain_2 + 'house/s/'
                    # 构建二手房的url链接
                    esf_url = scheme + '//' + domain_0 + 'esf.' + domain_1 + domain_2
                # print('城市：%s%s'%(province,city))
                # print('新房链接：%s'%newhouse_url)
                # print('二手房链接：%s'%esf_url)
                
                yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={"info":(province,city)})
                
                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={'info':(province,city)},dont_filter=True)
            #     break
            # break
            
    def parse_newhouse(self,response):
        province,city = response.meta.get('info')
        lis = response.xpath('//div[contains(@class,"nl_con")]/ul/li')
        for li in lis:
            name = li.xpath('.//div[@class="nlcd_name"]/a/text()').extract_first()
            if name == None:
                continue
            else:
                name = name.strip()
            house_type_list = li.xpath('.//div[contains(@class,"house_type")]/a/text()').extract()
            house_type_list = list(map(lambda x:re.sub(r'\s','',x),house_type_list))
            # 过滤出正确表示几居室的列表元素
            rooms = list(filter(lambda x:x[1]=='居',house_type_list))
            # 通过 .join 将列表转成字符串
            area_list = li.xpath('.//div[contains(@class,"house_type")]/text()').extract()
            area = ''.join(area_list)
            area = re.sub(r'\s|－|/','',area)
            address = li.xpath('.//div[@class="address"]/a/@title').get()
            district_text = ''.join(li.xpath('.//div[@class="address"]//text()').getall())
            district = re.search(r'.*\[(.+)\].*',district_text).group(1)
            sale = li.xpath('.//div[contains(@class,"fangyuan")]/span/text()').get()
            price = ''.join(li.xpath('.//div[@class="nhouse_price"]//text()').getall())
            price = re.sub(r'\s|广告','',price)
            origin_url = 'https:' + li.xpath('.//div[@class="nlcd_name"]/a/@href').get()

            item = NewHouseItem(province=province,city=city,name=name,rooms=rooms,area=area,address=address,district=district,sale=sale,price=price,origin_url=origin_url)
            yield item

        # 下一页链接
        next_url = response.xpath('//div[@class="page"]//a[@class="next"]/@href').get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_newhouse,meta={'info':(province,city)})
    
    def parse_esf(self,response):
        province,city = response.meta.get('info')
        print(city)
        dls = response.xpath('//div[contains(@class,"shop_list")]/dl')
        for dl in dls:
            name = dl.xpath('.//p[@class="add_shop"]/a/@title').get()
            if name == None:
                continue
            infos = dl.xpath('.//p[@class="tel_shop"]/text()').getall()
            infos = list(map(lambda x:re.sub(r'\s','',x),infos))
            rooms,area,floor,toward,year = None,None,None,None,None
            for info in infos:
                if "室" in info:
                    rooms = info
                elif "㎡" in info:
                    area = info
                elif "层" in info:
                    floor = info
                elif "向" in info:
                    toward = info
                elif "年" in info:
                    year = info
            address = dl.xpath('.//p[@class="add_shop"]/span/text()').get()
            price = ''.join(dl.xpath('.//dd[@class="price_right"]/span[1]//text()').getall())
            unit = dl.xpath('.//dd[@class="price_right"]/span[2]/text()').get()
            origin_url = dl.xpath('.//h4[@class="clearfix"]/a/@href').get()
            origin_url = response.urljoin(origin_url)

            esf_item = EsfHouseItem(province=province, city=city, name=name, rooms=rooms, floor=floor,area=area,toward=toward,year=year,address=address,price=price,unit=unit,origin_url=origin_url)
            yield esf_item

        # 下一页链接
        next_url = response.xpath('//div[@class="page_al"]//a[text()="下一页"]/@href').get()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_esf,
                                 meta={'info': (province, city)})

```
- pipelines.py
```
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exporters import JsonLinesItemExporter
from fang.items import NewHouseItem,EsfHouseItem

class FangPipeline(object):
    def __init__(self):
        self.newhouse_fp = open('newhouse.json','wb')
        self.esfhouse_fp = open('esfhouse.json','wb')
        self.newhouse_exporter = JsonLinesItemExporter(self.newhouse_fp,ensure_ascii=False)
        self.esfhouse_exporter = JsonLinesItemExporter(self.esfhouse_fp,ensure_ascii=False)
    
    
    # 此处sfw.py爬虫脚本中有两种item类，需要先判断item所属类别，再分别存储到json文件中    
    def process_item(self, item, spider):
        if isinstance(item,NewHouseItem):
            self.newhouse_exporter.export_item(item)
            return item
        else:
            self.esfhouse_exporter.export_item(item)
            return item
        
    def close_spider(self,spider):
        self.newhouse_fp.close()
        self.esfhouse_fp.close()

```

3. 创建运行脚本
```
from scrapy import cmdline
cmdline.execute("scrapy crawl sfw".split())
```
### 二、改写成 scrapy-redis 分布式爬虫
1. sfw.py    
将爬虫的类从 scrapy.Spider 变成 scrapy_redis.spiders.RedisSpider；   
或者是从scrapy.CrawlSpider 变成 scrapy_redis.spiders.RedisCrawlSpider
```
from scrapy_redis.spiders import RedisSpider
class SfwSpider(RedisSpider):
```
2. sfw.py
将爬虫中的 start_urls 删掉。增加一个 redis_key="..."。这个 redis_key 是为了以后在redis中控制爬虫启动的。爬虫的第一个url就是在Redis中通过这个发送出去。
```
# start_urls = ....
redis_key = "fang:start_urls"
```
3. settings.py   
在配置文件中增加如下配置：

```
# 设置Scrapy-Redis相关配置
# 确保request存储到redis中
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 确保所有爬虫共享相同的去重指纹
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# 设置redis为item pipeline
ITEM_PIPELINES = {
    'scrapy_redis.pipelines.RedisPipeline':300,
}

# 在redis中保持scrapy-redis用到的队列，不会清理redis中的队列，从而可以实现暂停和恢复的功能。
SCHEDULER_PERSIST = True

# 设置连接redis信息
# REDIS_HOST = '127.0.0.1'
# 使用本机作为redis服务器的时候，下面改为本机ip地址
REDIS_HOST = '192.168.1.6'
REDIS_PORT = 6379
```



### 三、搭建分布式环境
##### 本机作为Redis服务器，Ubuntu虚拟机作为爬虫服务器1，Windows虚拟机作为爬虫服务器2。
1. 配置Ubuntu环境：  
在 ubuntu 上安装scrapy之前，需要先安装以下依赖：(以下命令在ubuntu下)
```
cd /srv  # 以下都是在这个目录下

sudo apt-get install python3-dev build-essential python3-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
```
如果无法安装，可能是系统版本过低，此时切换到root用户进行更新：
```
> su
> apt-get update
```
2. 把项目部署到服务器上需要指定该爬虫项目所用到的包：（以下命令在本机）
```
# 1.打开终端进入项目所在的目录(此处是处于scrapy虚拟环境下)
cd fang
# 2.冰冻生成项目包文件
pip freeze > requirements.txt
```
3. 把生成的包文件requirements.txt传输到服务器：（以下命令在ubuntu）
```
# 1. 选择包文件并读取
rz

# 2. 可以选择安装到虚拟环境下
#  1) 创建虚拟环境
pip install virtualenvwrapper
#   查看一下python3的路径
which python3   # /usr/bin/python3
mkvirtualenv -p /usr/bin/python3 crawler-env  # 最后crawler-env 是虚拟环境的名称

#  2) 进入crawler-env虚拟环境下
pip install -r requirements.txt  # 如果不在这个虚拟环境下，直接安装的是python2环境下

#  3) 如果有win下的包报错，对于ubuntu环境下不需要，直接进入包文件删除该包名,再重新安装：
ls
vim requirements.txt

```
4. 在本机（windows）打开redis服务：
```
cd Redis
redis-server redis.windows.conf

# 新建一个cmd窗口
redis-cli
```


5. 将项目文件压缩成fang.zip，打包到Linux爬虫服务器1：（以下命令在ubuntu下）
```
rz
unzip fang.zip
cd fang
cd fang
cd spider
# scrapy runspider sfw.py


```

6. 将项目拷贝到Windows爬虫服务器2中：（以下命令在cmd下）
```
cd Desktop
cd fang
workon crawler-env
cd fang
cd spiders
# scrapy runspider sfw.py
```
7. 运行爬虫：
- 在爬虫服务器上。进入爬虫文件所在的路径,然后输入命令：scrapy runspider [爬虫名]
```
scrapy runspider sfw.py
# 进入监听等待redis服务器命令
```

- 在 redis 服务器上，推入一个开始的url链接，开始爬取：   
redis-cli > lpush [redis_key] start_url 
```
# 返回第4步新创建的终端下，redis客户端已经连接服务器
lpush fang:start_urls https://www.fang.com/SoufunFamily.htm
```

