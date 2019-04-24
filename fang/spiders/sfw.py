# -*- coding: utf-8 -*-
import scrapy
import re
from fang.items import NewHouseItem,EsfHouseItem
from scrapy_redis.spiders import RedisSpider


class SfwSpider(RedisSpider):
    name = 'sfw'
    allowed_domains = ['fang.com']
    # start_urls = ['https://www.fang.com/SoufunFamily.htm']
    redis_key = "fang:start_urls"
    
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
