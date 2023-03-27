"""This is a crawler for PTT.

It will crawl the data from PTT and generate crawl result.
"""

import asyncio

from bs4 import BeautifulSoup as bsp
import requests as rq


class PTTCrawler:
    """Crawl data from PTT.

    Attributes:
        board: The board we want to crawl.
        frequency: The number of pages we want to get.
        loop: Event Loop.
    """

    def __init__(self, board: str, frequency: str, loop):
        self.__base_url = "https://www.ptt.cc"
        self.__headers = {
            "cookie":
                "over18=1;",
            "User-Agent":
                "".join(
                    (
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) ",
                        "Gecko/20100101 Firefox/111.0"
                    )
                )
        }
        self.__board = board
        self.__frequency = frequency
        self.__loop = loop
        self.__result_box = []

    def get_result(self) -> dict:
        """Return the result.

        Returns:
            A list is formed with
            some dicts keys that are category and values are information.
        For example:
        [
            {
                'MetaInformation': 
                {
                    "作者": "bca321 (bcderf)",
                    "標題": "[閒聊] HELLO WORLD!",
                    "時間": "Thu Mar 23 17:43:05 2023"
                }
                'Contents': 'Hello World :P'
                'Messages': {'abc123': 'HAHA.'}
            }
        ]
        """
        return self.__result_box

    def __POST(self, url) -> str:
        """Return the HTML we crawl from website.

        Args:
            url: the website we want to crawl.
        Returns:
            HTML docs which type is sting.
            For example:
            "<div>Hello!</div>"
        """
        res = rq.post(url, headers=self.__headers)
        res.encoding = "utf-8"
        return res

    async def main(self):
        """Manage crawl tasks.

        Use asyncio way to manage crawlers.
        While a crawler is I/Oing(ex: request the website),
        execute other crawler.
        So, we can save the time.
        """
        topic_urls = self.__topic_urls_crawler()
        tasks = [asyncio.create_task(self.__data_crawler(
            self.__base_url + url)) for url in topic_urls]
        await asyncio.gather(*tasks)

    def __topic_urls_crawler(self) -> list:
        """Collect topic urls.

        Request the index page. Collect topic urls.
        Returns:
            A list that is filled with topic urls(type is string).
            For example:
            ["https://www.ptt.cc/bbs/XXX/XXX.html"]
        """
        topic_urls = []
        url = "{}/bbs/{}/index.html".format(self.__base_url, self.__board)
        for i in range(int(self.__frequency)):
            # Get html docs.
            index_topic_list = self.__POST(url)
            # bs4 html docs.
            index_topic_list_soup = bsp(
                index_topic_list.text.strip(), "html.parser")
            # Determine if exist annocement.
            index_topic_anchor = index_topic_list_soup.select_one(
                ".r-list-sep")
            if (index_topic_anchor is not None):
                topics = index_topic_anchor.find_previous_siblings(
                    class_="r-ent")
            else:
                topics = index_topic_list_soup.select(".r-ent")
            # Select topic urls.
            for topic in topics:
                sub_url = topic.select_one(".title > a")
                if (sub_url is not None):
                    topic_urls.append(sub_url["href"])
            print(f"Page {i + 1} urls is collected. ")
            # url is changed to next page.
            url = "{}{}".format(
                self.__base_url,
                (index_topic_list_soup.select(".btn.wide"))[1]["href"]
            )
        return topic_urls

    async def __data_crawler(self, url: str):
        """Gather informations we want from PTT topics.

        Args:
            url: the website we want to crawl.
        """
        topic_box = {}
        # Get html docs.
        topic_result = await self.__loop.run_in_executor(None, self.__POST, url)
        # bs4 html docs.
        topic_result_soup = bsp(topic_result.text, "html.parser")
        topic = topic_result_soup.select_one(".bbs-screen.bbs-content")
        # Select meta informations.
        topic_meta = topic.select(".article-metaline")
        meta_box = {}
        # Select messages.
        topic_messages = topic.select(".push")
        message_box = {}
        # If has meta information in topic page.
        if (topic_meta != []):
            # Select meta information and arrange it.
            for topic_meta_info in topic_meta:
                meta_box[topic_meta_info.select_one(".article-meta-tag").text.strip(
                )] = topic_meta_info.select_one(".article-meta-value").text.strip()
            # Select contents.
            content = (topic.text.strip().split("--")[0]).split("\n")[1:]
            contents = " ".join(content)
            # Select message and arrange it.
            for message in topic_messages:
                message_content = message.select_one(".push-content")
                if (message_content.select_one("a") is not None):
                    continue
                message_userid = message.select_one(
                    ".push-userid").text.strip()
                message_box[message_userid] = message_box.get(
                    message_userid, "") + " " + message_content.text.strip().strip(":").strip()
            # Integrate neta informtaions, contents and messages.
            topic_box["MetaInformation"] = meta_box
            topic_box["Contents"] = contents
            topic_box["Messages"] = message_box
            # Save Integrated result.
            self.__result_box.append(topic_box)
