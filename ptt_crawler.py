'''
$pip install requests
$pip install beautifulsoup4

'''
import requests as rq
from bs4 import BeautifulSoup as bsp
import asyncio
import json
import time
import os


class PTTCrawler:

    def __init__(self, board:str, frequency:int):
        self.base_url = "https://www.ptt.cc"
        self.headers = {"cookie": "over18=1;", "User-Agent": "mozilla/5.0 (Linux; Android 6.0.1; ""Nexus 5x build/mtc19t applewebkit/537.36 (KHTML, like Gecko) ""Chrome/51.0.2702.81 Mobile Safari/537.36"}
        self.board = board
        self.frequency = frequency
        self.topic_urls = []
        self.result_box = []

    def get_result(self):
        return self.result_box

    def POST(self, url)->str:
        res = rq.post(url, headers=self.headers)
        res.encoding = "utf-8"
        return res

    async def main(self):
        self.topic_urls_crawler()
        tasks = []
        tasks = [asyncio.create_task(self.data_crawler(self.base_url + url)) for url in self.topic_urls]
        await asyncio.gather(*tasks)

    def topic_urls_crawler(self):
        page_url = self.base_url + "/bbs/" + self.board + "/index.html"
        for i in range(frequency):
            index_topic_list = self.POST(page_url)
            index_topic_list_soup = bsp(index_topic_list.text.strip(), "html.parser")
            index_topic_anchor = index_topic_list_soup.select_one(".r-list-sep")
            if index_topic_anchor != None:
                topics = index_topic_anchor.find_previous_siblings(class_ = "r-ent")
            else:
                topics = index_topic_list_soup.select(".r-ent")
            for topic in topics:
                sub_url = topic.select_one(".title > a")
                if sub_url != None: 
                    self.topic_urls.append(sub_url["href"])
            print(f"Page {i + 1} urls is collected. ")
            page_url = self.base_url + (index_topic_list_soup.select(".btn.wide"))[1]["href"]

    async def data_crawler(self, url:str):
        topic_box = {}
        topic_result = await loop.run_in_executor(None, self.POST, url)
        # bs4 topic
        topic_result_soup = bsp(topic_result.text, "html.parser")
        topic = topic_result_soup.select_one(".bbs-screen.bbs-content")
        topic_meta = topic.select(".article-metaline")
        meta_box = {}
        topic_messages = topic.select(".push")
        message_box = {}
        # if has meta information in topic page
        if(topic_meta != []):
            # meta infomation
            for topic_meta_info in topic_meta:
                meta_box[topic_meta_info.select_one(".article-meta-tag").text.strip()] = topic_meta_info.select_one(".article-meta-value").text.strip()
            # contents
            content = (topic.text.strip().split("--")[0]).split("\n")[1:]
            contents = " ".join(content)
            # messages
            for message in topic_messages:
                message_content = message.select_one(".push-content")
                if message_content.select_one("a") != None:
                    continue
                message_userid = message.select_one(".push-userid").text.strip()
                message_box[message_userid] = message_box.get(message_userid, "")  + " " + message_content.text.strip().strip(":").strip()
            # intergrate
            topic_box["meta_information"] = meta_box
            topic_box["contents"] = contents
            topic_box["messages"] = message_box
        self.result_box.append(topic_box)

if __name__ == "__main__":
    storehouse = "ptt_crawler_json_results"
    board = input("Board: ")
    frequency = int(input("Page: "))
    crawler = PTTCrawler(board, frequency)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(crawler.main())
    result = crawler.get_result()
    today = time.strftime("%Y-%m-%d")
    data = {
        "crawl_date": today,
        "community": "PPT",
        "crawl_results": result
    }
    Root = os.path.join(os.getcwd(), storehouse)
    if not os.path.exists(Root):
        os.mkdir(Root)
    with open(os.path.join(Root, today + "-PPT-" + board + ".json"), "w+", encoding = "utf-8") as f:
        json.dump(data, f, indent = 2, ensure_ascii = False)
    print("Finish!")