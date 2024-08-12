import os
import csv
import json
import nodriver as uc
from lxml import html
URL_ONLINE = "https://alternativeto.net/platform/online/?p={}" 
URL_ONLINE_DETAIL = "https://alternativeto.net/software/{}/about/"
URL_SASS = "https://alternativeto.net/platform/software-as-a-service/?p={}" 
PAGES_ONLINE = 2800
PAGES_SASS = 620

class Scraper:
    main_tab: uc.Tab
    def __init__(self):
        self.data = []
        self.dataMap = dict()

        if os.path.exists('result.csv'):
            with open('result.csv', 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    if row.get("id", None) is not None:
                        self.dataMap[row["id"]] = True
                        
        uc.loop().run_until_complete(self.main())

    async def create_browser(self):
        self.browser = await uc.start(headless=False )
        self.main_tab = await self.browser.get("draft:,")

    def save_csv(self, row):
        with open('result.csv', 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(row)

    async def main(self):
        print("---Starting")

        await self.create_browser()
        
        print("---Created Browser Successfully")
        
        for i in range(PAGES_ONLINE, 1, -1):
            print(f'###Scraping {i}/{PAGES_ONLINE} -----ONLINE')
            flag = True
            while flag:
                try:
                    await self.parse_lists_page(URL_ONLINE, URL_ONLINE_DETAIL, i, 'ONLINE')
                    flag = False
                except:
                    print("Try again")
                    flag=True
                    continue

        for i in range(1, PAGES_SASS + 1):
            print(f'###Scraping {i}/{PAGES_SASS} -----SASS')
            flag = True
            while flag:
                try:
                    await self.parse_lists_page(URL_SASS, URL_ONLINE_DETAIL, i, 'SASS')
                    flag = False
                except:
                    print("Try again")
                    flag=True
                    continue

    async def parse_lists_page(self,f_main_url, f_detail_url, i, group_name):
        temp = dict()

        self.page = await self.browser.get(f_main_url.format(i))
        
        await self.page.wait_for("script[type='application/json']", timeout=99999)

        content = await self.page.get_content()

        page_data_json = self.parse_page2json(content)

        items = page_data_json['props']['pageProps']['items']

        for item in items:
            temp['id'] = item['id']
            temp['name'] = item['name']
            temp['url'] = f_detail_url.format(item['urlName'])
            temp['appTypes'] = []
            temp['appTypes'] = [app_type['appType'] for app_type in item['appTypes']]
            temp['licenseModel'] = item.get('licenseModel', None)
            temp['licenseCost'] = item.get('licenseCost', None)
            temp['platforms'] = []
            temp['platforms'] = [{'name': platform['name'], 'type':platform['platformType']} for platform in item['platforms']]

            await self.page.get(temp['url'])
            
            await self.page.wait_for("script[type='application/json']", timeout=99999)

            detail_content = await self.page.get_content()
            
            detail_json = self.parse_page2json(detail_content)
            
            temp['description'] = detail_json['props']['pageProps']['mainItem']['description']

            temp['categories'] = []
            
            temp['categories'] = [category['name'] for category in detail_json['props']['pageProps']['mainItem']['categories']]

            temp['socialLinks'] = []
            
            temp['socialLinks'] = [link for link in detail_json['props']['pageProps']['mainItem']['externalLinks'] if link.get('type') == 'Social']
            
            temp['group'] = group_name

            if self.dataMap.get(temp['id'], None) is None:
                self.save_csv(temp)
                print("++++ Saved ", item['name'])
            else:
                print('----Skipped ', item['name'])
                pass
    def parse_page2json(self, content):

        tree = html.fromstring(content)
        
        page_data_json = json.loads(tree.cssselect("script[type='application/json']")[0].text_content().strip())

        return page_data_json

if __name__ == '__main__':
   Scraper()
