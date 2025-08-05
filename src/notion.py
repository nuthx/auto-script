import os

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 获取数据库内容
def query_database(database_id):
    notion_list = []
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    payload = {"page_size": 100}
    headers = {
        "Authorization": "Bearer " + os.getenv("NOTION_TOKEN"),
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    # 由于API每次最多返回100条目，因此分轮次查询
    while True:
        response = requests.post(url, json=payload, headers=headers).json()
        notion_list.extend(response["results"])

        # 判断是否存在下一轮次，如果存在则重复执行
        if response.get("next_cursor"):
            payload["start_cursor"] = response["next_cursor"]
        else:
            break

    return notion_list


# 更新数据库条目
def update_page(page_id, content):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": "Bearer " + os.getenv("NOTION_TOKEN"),
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = {
        "parent": {"database_id": os.getenv("NOTION_DB_BANGUMI")},
        "properties": content,
    }

    response = requests.patch(url, json=data, headers=headers)
    return response


# 创建数据库条目
def create_page(database_id, content):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": "Bearer " + os.getenv("NOTION_TOKEN"),
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    data = {"parent": {"database_id": database_id}, "properties": content}

    response = requests.post(url, json=data, headers=headers)
    return response
