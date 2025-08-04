import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv

from src.notion import query_database, update_page


def update_anime(anime):
    # 提取bangumi_id和title
    bangumi_id = anime["properties"]["URL"]["url"].split("/")[-1]
    anime_title = anime["properties"]["名称"]["title"][0]["plain_text"]

    # 统一headers
    headers = {"accept": "application/json", "User-Agent": "nuthx/notion-assistant"}

    # 获取动画评分
    response = requests.get(f"https://api.bgm.tv/v0/subjects/{bangumi_id}", headers=headers).json()
    anime["bangumi"] = {}
    anime["bangumi"]["score"] = response["rating"]["score"]

    # 获取用户的收藏状态
    collection_mapping = {1: "想看", 2: "看过", 3: "在看", 4: "搁置", 5: "抛弃"}
    response = requests.get(f"https://api.bgm.tv/v0/users/{os.getenv('BANGUMI_USER_ID')}/collections/{bangumi_id}", headers=headers).json()
    anime["bangumi"]["collection"] = collection_mapping.get(response.get("type", 0), None)  # 如果没有收藏，则collection_mapping为0，然后自动设置为None

    # 更新评分和收藏状态到数据库
    if anime["bangumi"]["collection"]:
        update_page(
            anime["id"],
            {
                "评分": {"number": anime["bangumi"]["score"]},
                "收藏状态": {"status": {"name": anime["bangumi"]["collection"]}},
            },
        )
    else:
        update_page(anime["id"], {"评分": {"number": anime["bangumi"]["score"]}})

    return bangumi_id, anime_title


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()

    # 记录开始时间
    start_time = time.time()

    # 获取数据库内容
    print("——————————")
    print("获取动画列表")
    database = query_database(os.getenv("NOTION_DB_BANGUMI"))
    anime_list = [item for item in database if item["properties"]["URL"]["url"]]  # 排除没有url的动画
    print(f"当前共有{len(anime_list)}部动画，已排除{len(database) - len(anime_list)}条记录")

    # 从Bangumi获取最新内容，并更新到Notion
    print("——————————")
    with ThreadPoolExecutor(max_workers=20) as executor:
        index = 0
        futures = [executor.submit(update_anime, anime) for anime in anime_list]
        for future in as_completed(futures):
            try:
                result = future.result()
                index += 1
                print(f"完成[{index}/{len(anime_list)}]: {result[0]} - {result[1]}")
            except Exception as e:
                index += 1
                print(f"失败[{index}/{len(anime_list)}]: {e}")

    # 计算耗时
    end_time = time.time()
    used_time = round(end_time - start_time, 1)  # 四舍五入
    print("——————————")
    print(f"识别完成，耗时{used_time}秒")
