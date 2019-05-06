import requests
from urllib.parse import urlencode
from lxml import etree
from requests import codes
import os
from hashlib import md5
from multiprocessing.pool import Pool
import re
import json
import csv
#声明一个全局变量存储字典
data_list = []
#请求头
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36',
    'Referer':'https://www.zhihu.com/',
    'Accept':'*/*',
    'X-Requested-With':'fetch',
    'Cookie':'_xsrf=TjVRV2dlEIZic9TSlBje7Re0pIXi65oC; _zap=e856749a-92e0-435b-b57f-d7b6ac3777d2; d_c0="ACBlMihGUw-PTmvO9XC6KMi3vq_iPI5dscE=|1556066464"; __gads=ID=4d26e74f8b83fd6c:T=1556066563:S=ALNI_MZVaab_2ltChYVZ935hEMT7ymElGQ; q_c1=174f137e89d644368bf04ae921c021b6|1556066604000|1556066604000; tst=r; __utma=51854390.433761935.1556950532.1556950532.1556950532.1; __utmz=51854390.1556950532.1.1.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __utmv=51854390.100--|2=registration_date=20171023=1^3=entry_date=20171023=1; r_cap_id="MTVhMTE1MmNkNjczNDcyMDkyZmE2YzAxMWU0NGYwMTI=|1556957697|60c39f88f2c6d79acac585b5453bfa4852638efd"; cap_id="NjBkMDc3NWNlZTJmNDAyNmI5OTI1ZTQ2ZjNkOWNjODE=|1556957697|38c1cf48b7c9017425845dec689deeca04c467e5"; l_cap_id="N2QyZmU4ZTUwNDNmNDQxM2E2ODFhZGRiZGU4NDY0ODI=|1556957697|62beeb6dba5cfee7e7e2733cb038eb5e06a239cf"; capsion_ticket="2|1:0|10:1557064717|14:capsion_ticket|44:ZTJmZjJkNDkxOWE2NDgzY2FhMzVjZDQ3OTY0OWU0MDg=|3d486c3c76e53f9d66d9b3034990f70367f65558f92573439e237d96d523c97d"; z_c0="2|1:0|10:1557064724|4:z_c0|92:Mi4xeFRCSkJnQUFBQUFBSUdVeUtFWlREeVlBQUFCZ0FsVk5GRHE4WFFBeWp2OEdpVzJTQ3ZJYU9lblUxTGt4aE93YjBB|3b673c142e59dc9b9079ea86da1dfa72c59e6cea1c0be0526d64754613f16c2e"; tgw_l7_route=a37704a413efa26cf3f23813004f1a3b'
}
#获取知乎网址
def get_page(page_number):
    params = {
        'session_token':'aae66b8711d72373d8dfb7faa8744d0f',
        'desktop':'true',
        'page_number':page_number,#地址中有2个变量page_number和after_id,但这2个数据有关联
        'limit':'6',
        'action':'down',
        'after_id':int(page_number)*6-7
    }
    base_url = 'https://www.zhihu.com/api/v3/feed/topstory/recommend?'
    url = base_url + urlencode(params)
    try:
        resp = requests.get(url,headers = headers)
        print(url)
        if 200  == resp.status_code:
            # print(resp.json())
            return resp.json()
    except requests.ConnectionError:
        return None


#抽取信息
def get_data(json):
    if json.get('data'):
        items = json.get('data')
        for item in items:
            item = item.get('target').get('question')
            if item:
                try:
                    if(item.get('created')):#知乎问题创建时间
                        time = item.get('created')
                        if time>1546272000:#判断是否是在2019年的
                            titles = item.get('title')#知乎问题标题
                            question_id = item.get('id')
                            url = "https://www.zhihu.com/question/" + str(question_id)
                            response = requests.get(url, headers=headers)
                            html = etree.HTML(response.text)
                            excerpts = html.xpath('//span[@class="RichText ztext"]/text()')#知乎问题描述
                            excerpts = ''.join(excerpts)#将list转化为字符串
                            # print(excerpts)
                            # print(type(excerpts))
                            excerpts = re.sub(r'[图片]','',excerpts)#将图片清洗掉
                            # excerpts = item.get('excerpt')#知乎问题描述
                            # excerpts = re.sub(r'本题.*?</a>|<b>|</b>|<a.*?>|</a>|<span.*?>.*?</span>', '', excerpts)#数据清洗,刷掉“本题已加入知乎圆桌，
                            #                                                 # 更多「复联」讨论欢迎关注 »”和各种的地址还有b标签
                            data_dict = {}#写入字典
                            data_dict['titles']=titles
                            data_dict['excerpts']=excerpts

                            if(data_dict not in data_list):#查重，如果没重复就加入
                                data_list.append(data_dict)

                            # yield {
                            #      'title':titles,
                            #      'excerpt':excerpts
                            # }
                        else:
                            continue
                except requests.ConnectionError:
                    return None
        return True
    else:
        return None

# json = get_page(2)
# for item in get_images(json):
#     print(item)


def save_data():
    #写入json文件
    content = json.dumps(data_list,ensure_ascii=False,indent=2)#字典转化为json
                                                        #有中文要加ensure_ascii=False
    with open("zhihu.json", "a+", encoding="utf-8") as f:
        f.write(content)
        print("正在保存："+content)

    # 将数据写入csv文件
    with open('data_csv.csv', 'w', encoding='utf-8', newline='') as f:
         # 表头
        title = data_list[0].keys()
        # 声明writer
        writer = csv.DictWriter(f, title)
        # 写入表头
        writer.writeheader()
        # 批量写入数据
        writer.writerows(data_list)



def main():
    offset = 0
    while True:
        json = get_page(offset)
        flag = get_data(json)
        offset += 1
        if(offset>=10):#自增，当大于等于20时中止
            break
    save_data()



# GROUP_START = 0
# GROUP_END = 7

if __name__ == '__main__':
    # groups = ([x for x in range(GROUP_START, GROUP_END + 1)])
    # map(main, groups)
    main()
