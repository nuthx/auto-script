import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv

from src.notion import query_database, update_page


def update_anime(anime):
    # 统一headers
    headers = {"accept": "application/json", "User-Agent": "nuthx/notion-assistant"}

    # 搜索bangumi_id
    response = requests.get(f"https://api.bgm.tv/search/subject/{anime['properties']['名称']['title'][0]['plain_text']}?type=2&responseGroup=small", headers=headers).json()
    if response["list"]:
        anime["bangumi"] = {}
        anime["bangumi"]["id"] = response["list"][0]["id"]
        anime["bangumi"]["title"] = response["list"][0]["name"]
    else:
        return

    # 更新标题和链接到数据库
    update_page(
        anime["id"],
        {
            "原名": {"rich_text": [{"text": {"content": anime["bangumi"]["title"]}}]},
            "URL": {"url": f"bgm.tv/subject/{anime['bangumi']['id']}"},
        },
    )

    return anime["bangumi"]["id"], anime["bangumi"]["title"]


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()

    # 记录开始时间
    start_time = time.time()

    # 获取数据库内容
    print("——————————")
    print("获取动画列表")
    database = query_database(os.getenv("NOTION_DB_BANGUMI"))
    anime_list = [item for item in database if not item["properties"]["URL"]["url"]]  # 排除有url的动画
    print(f"当前共有{len(anime_list)}部动画待搜索")

    # 从Bangumi获取最新内容，并更新到Notion
    print("——————————")
    with ThreadPoolExecutor(max_workers=20) as executor:
        index = 0
        futures = [executor.submit(update_anime, anime) for anime in anime_list]
        for future in as_completed(futures):
            try:
                result = future.result()
                index += 1
                if result:
                    print(f"完成[{index}/{len(anime_list)}]: {result[0]} - {result[1]}")
                else:
                    print(f"完成[{index}/{len(anime_list)}]: 该动画无搜索结果")
            except Exception as e:
                index += 1
                print(f"失败[{index}/{len(anime_list)}]: {e}")

    # 计算耗时
    end_time = time.time()
    used_time = round(end_time - start_time, 1)  # 四舍五入
    print("——————————")
    print(f"识别完成，耗时{used_time}秒")
