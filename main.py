"""Call PTTCrawler to crawl and save the result in a directory."""

import asyncio
import json
import os
import time

from ptt_crawler import PTTCrawler


def main():
    """Call PTTCrawler and save the result in a directory.

    Call PTTCrawler and pass needed parameters.
    We will get a result which type is dictionary.
    Then, we will create a directory, if it does not exist.
    Finally, we save result in the directory.
    """
    # Create a Event Loop.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Call PTTCrawler and pass parameters.
    board = input("Board: ")
    frequency = input("Page: ")
    crawler = PTTCrawler(board, frequency, loop)
    loop.run_until_complete(crawler.main())
    result = crawler.get_result()
    # Get date.
    today = time.strftime("%Y-%m-%d")
    data = {
        "crawl_date": today,
        "community": "PPT",
        "crawl_results": result
    }
    # Indicate the directory name that we want to save result.
    directory_name = "PTTCrawlerJSONResults"
    Root = os.path.join(os.getcwd(), directory_name)
    # If directory does not exist, create it.
    if not os.path.exists(Root):
        os.mkdir(Root)
    # Open the directory and save the result.
    with open(os.path.join(Root, today + "-PPT-" + board + ".json"), "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Finish!")


if __name__ == "__main__":
    main()
