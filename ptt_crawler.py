"""This is a crawler for PTT.

It will crawl the data from PTT and generate crawl result.
"""

import asyncio
import datetime

from bs4 import BeautifulSoup as bsp
import requests as rq


class PTTCrawler:
    """Set basic information for crawling data from PTT."""

    def __init__(self):
        self._base_url = "https://www.ptt.cc"
        self._headers = {
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

    def _POST(self, url) -> str:
        """Return the HTML we crawl from website.

        Args:
            url: the website we want to crawl.
        Returns:
            HTML which type is string.
            For example:
            '<div>Hello!</div>'
        """
        res = rq.post(url, headers=self._headers)
        res.encoding = "utf-8"
        return res

class PTTTopicUrlCrawler(PTTCrawler):
    """Crawl topic url last day from PTT.

    Attributes:
        board: The board we want to crawl.
    """
    def __init__(self, board: str):
        super().__init__()
        self.__board = board
    
    @property
    def result(self) -> list:
        """Collect topic urls.

        Inherit from PTTCrawler.
        Request the index page. Collect topic urls.
        Returns:
            A list that is filled with topic urls(type is string).
            For example:
            ["/bbs/XXX/XXX.html"]
        """
        topic_urls = []
        url = "{}/bbs/{}/index.html".format(self._base_url, self.__board)
        today = formalization_date(datetime.date.today())
        load_more = True
        while load_more:
            # Get html docs.
            index_topic_list = self._POST(url)
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
            for i in range(len(topics)):
                sub_url = topics[i].select_one(".title > a")
                if (sub_url is not None):
                    topic_urls.append(sub_url["href"])
                # topic date
                date = topics[i].select_one(".date").text.strip()
                if date != today:
                    load_more = False
                    break
            # Current url is changed to next page.
            url = "{}{}".format(
                self._base_url,
                (index_topic_list_soup.select(".btn.wide"))[1]["href"]
            )
        return topic_urls

class PTTTopicCrawler(PTTCrawler):
    """Crawl data from PTT using topic_urls.

    Inherit from PTTCrawler.
    Attributes:
        topic_urls: 
            The urls we want to crawl.
            For example:
                '/bbs/Doctor-Info/M.1681350010.A.BDB.html'
        loop: Event Loop.
    """

    def __init__(self, topic_urls, loop):
        super().__init__()
        self.__topic_urls = topic_urls
        self.__loop = loop
        self.__result_box = []

    async def __data_crawler(self, url: str):
        """Gather datas we want from PTT topic.

        Args:
            url: the topic url we want to crawl.
        """
        topic_box = {}
        # Get html docs.
        topic_result = await self.__loop.run_in_executor(None, self._POST, url)
        # bs4 html docs.
        topic_result_soup = bsp(topic_result.text, "html.parser")
        topic = topic_result_soup.select_one(".bbs-screen.bbs-content")
        # Select meta informations.
        topic_meta = topic.select(".article-metaline")
        # Select messages.
        topic_messages = topic.select(".push")
        message_box = {}
        # If has meta information in topic page.
        if (topic_meta != []):
            # Url
            topic_box["Url"] = url
            # Select meta information.
            meta_info = []
            for t in topic_meta:
                meta_info.append(t.select_one(".article-meta-value").text.strip())
            # Author
            topic_box["Author"] = meta_info[0]
            # Title
            topic_box["Title"] = meta_info[1]
            # Time
            topic_box["Time"] = formalization_time(meta_info[2])
            # Contents
            content = (topic.text.strip().split("--")[0]).split("\n")[1:]
            contents = " ".join(content)
            topic_box["Contents"] = contents
            # Messages
            for message in topic_messages:
                message_content = message.select_one(".push-content")
                if (message_content.select_one("a") is not None):
                    continue
                message_userid = message.select_one(
                    ".push-userid").text.strip()
                message_box[message_userid] = "".join(
                    (
                        message_box.get(message_userid, ""),
                        " ",
                        message_content.text.strip().strip(":").strip()
                    )
                )
            messages = []
            for key, value in message_box.items():
                messages.append({"Author": key, "Contents": value})
            topic_box["Messages"] = messages
            # Save result.
            self.__result_box.append(topic_box)

    async def __main(self):
        """Manage crawl tasks.

        Use asyncio way to manage crawlers.
        While a crawler is I/Oing(ex: request the website),
        execute other crawler.
        So, we can save the time.
        """
        tasks = [asyncio.create_task(self.__data_crawler(
            self._base_url + url)) for url in self.__topic_urls]
        await asyncio.gather(*tasks)

    @property
    def result(self) -> list:
        """Return the result.

        Returns:
            A list is formed with
            some dicts keys that are category and values are information.
            For example:
                [
                    {
                        'Url': 'https://www.ptt.cc/bbs/Doctor/XXXX.html',
                        'Author': 'bca321 (bcderf)',
                        'Title': '[閒聊] HELLO WORLD!',
                        'Time': '2023-03-21 02:57:29'
                        'Contents': 'Hello World :P'
                        'Messages': 
                        {
                            'Author': 'abc123',
                            'Contents': 'HAHA.'
                        }
                    }
                ]
        """
        self.__loop.run_until_complete(self.__main())
        return self.__result_box

def formalization_time(time:str) -> str:
    """Set time format to '%Y-%m-%d %H:%M:%S'.
    
    Args:
        time: The time wnat to formatted.
    Returns:
        A time which type is string.
        For example:
            '2023-03-21 02:57:29'
    """
    month = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }
    y = time[20:]
    m = month[time[4:7]]
    d = time[8:10]
    H = time[11:13]
    M = time[14:16]
    S = time[17:19]
    formatted_time = "{}-{}-{} {}:{}:{}".format(y, m, d, H, M, S)
    return formatted_time

def formalization_date(today: datetime.date) -> str:
    month = today.month
    day = today.day
    if day <= 9:
        return "{}/0{}".format(month, day)
    return "{}/{}".format(month, day)

# How to use:
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    t = PTTTopicUrlCrawler("doctor-info")
    urls = t.result
    print(urls)
    print("========")
    c = PTTTopicCrawler(urls, loop)
    for r in c.result:
        print(r)