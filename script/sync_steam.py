import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv

from src.notion import query_database, update_page, create_page


def update_game(game, wishlist):
    return 0, 1
    # print(game)
    # print(wishlist)
    # 提取steam_id
    # steam_id = game["properties"]["ID"]["number"]

    # 检测steam_id是不是在愿望单中
    # 在game中添加in_wishlist属性

    # 愿望单  发售日期  史低

    # 愿望单的创建回来


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()

    # 记录开始时间
    start_time = time.time()

    # 获取数据库内容
    print("——————————")
    print("获取游戏列表")
    database = query_database(os.getenv("NOTION_DB_GAME"))
    game_list = [item for item in database if item["properties"]["ID"]["number"]]  # 排除没有id的游戏
    print(f"当前共有{len(game_list)}个游戏，已忽略{len(database) - len(game_list)}条没有ID的记录")

    # 获取愿望单（第三方API）
    wishlist = requests.get(f"https://www.steamwishlistcalculator.com/api/wishlist?steamId={os.getenv('STEAM_UID')}&countryCode=CN").json()

    # 检查游戏是否只在愿望单中，如果是则创建相应的Notion条目
    wishlist_count = 0
    for item in wishlist:
        if not any(game["properties"]["ID"]["number"] == item["id"] for game in game_list):
            wishlist_count += 1
            create_page(os.getenv("NOTION_DB_GAME"), {"ID": {"number": item["id"]}})

    # 打印愿望单的添加结果
    print("——————————")
    if wishlist_count == 0:
        print("愿望单中没有新游戏")
    else:
        print(f"从愿望单添加了{wishlist_count}个游戏")


    # 从Bangumi获取最新内容，并更新到Notion
    print("——————————")
    with ThreadPoolExecutor(max_workers=20) as executor:
        index = 0
        futures = [executor.submit(update_game, game, wishlist) for game in game_list]
        for future in as_completed(futures):
            try:
                result = future.result()
                index += 1
                print(f"完成[{index}/{len(game_list)}]: {result[0]} - {result[1]}")
            except Exception as e:
                index += 1
                print(f"失败[{index}/{len(game_list)}]: {e}")

    # 计算耗时
    end_time = time.time()
    used_time = round(end_time - start_time, 1)  # 四舍五入
    print("——————————")
    print(f"识别完成，耗时{used_time}秒")
