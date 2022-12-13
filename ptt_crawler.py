import requests as rq
from bs4 import BeautifulSoup as bsp
import json
import time
import os

url = "https://www.ptt.cc"
headers = {"cookie": "over18=1;", "User-Agent": "mozilla/5.0 (Linux; Android 6.0.1; ""Nexus 5x build/mtc19t applewebkit/537.36 (KHTML, like Gecko) ""Chrome/51.0.2702.81 Mobile Safari/537.36"}
def topic_crawler(board :str, frequency :int) ->list:
    result_box = []
    detailed_url = "/bbs/" + board + "/index.html"
    for i in range(0, int(frequency)):
    # request every demand page
        result = rq.post(url + detailed_url, headers = headers)
        result.encoding = "utf-8"
        result_soup = bsp(result.text.strip(), "html.parser")
        topic_anchor = result_soup.select_one(".r-list-sep")
        if topic_anchor != None:
            topics = topic_anchor.find_previous_siblings(class_ = "r-ent")
        else:
            topics = result_soup.select("r-cent")
        for element in topics:
            # request every topic
            title = element.select_one(".title")
            title_url = title.select_one("a")
            meta = element.select_one(".meta")
            if(title_url != None):
                topic_url = url + title_url["href"]
            else:
                continue
            topic_result = rq.post(topic_url, headers = headers)
            topic_result.encoding = "utf-8"
            # bs4 topic
            topic_result_soup = bsp(topic_result.text, "html.parser")
            topic = topic_result_soup.select_one(".bbs-screen.bbs-content")
            topic_meta = topic.select(".article-metaline")
            meta_box = {}
            topic_messages = topic.select(".push")
            message_box = {}
            # has meta information in topic page
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
                topic_box = {
                "meta_information": meta_box,
                "contents": contents,
                "messages": message_box
                }
            else:
                # meta information
                meta_box["作者"] = meta.select_one(".author").text.strip()
                meta_box["標題"] = title.text.strip()
                meta_box["時間"] = meta.select_one(".date").text.strip()
                # contents
                content = (topic.text.strip().split("--")[0]).split("\n")[1:]
                contents = "\n".join(content)
                # messages
                for message in topic_messages:
                    message_content = message.select_one(".push-content")
                    if message_content.select_one("a") != None:
                        continue
                    message_userid = message.select_one(".push-userid").text.strip()
                    message_box[message_userid] = message_box.get(message_userid, "")  + " " + message_content.text.strip().strip(":").strip()
                # intergrate
                topic_box = {
                "meta_information": meta_box,
                "contents": contents,
                "messages": message_box
                }
            result_box.append(topic_box)
        detailed_url = (result_soup.select(".btn-group.btn-group-paging > a")[1])["href"]
    return result_box

if __name__ == "__main__":
  storehouse = "ptt_crawler_json_results"

  board = input("Board: ")
  frequency = input("Frequency: ")
  result = topic_crawler(board = board, frequency = frequency)
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
