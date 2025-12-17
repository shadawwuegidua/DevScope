import json
from typing import Any, Dict, Optional

import requests


def load_opendigger_json(path_or_url: str, timeout: int = 30) -> Any:
    """加载 OpenDigger 静态 JSON 数据。

    参数支持：
    - 远程 URL（以 http/https 开头）
    - 本地文件路径

    返回值：已解析的 JSON Python 对象（dict 或 list）。
    异常：当网络或解析失败时抛出 RuntimeError。
    """
    if path_or_url.lower().startswith(("http://", "https://")):
        try:
            resp = requests.get(path_or_url, timeout=timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"下载 OpenDigger 数据失败: {exc}")
        if resp.status_code >= 400:
            raise RuntimeError(f"下载 OpenDigger 数据失败: {resp.status_code} {resp.text}")
        try:
            return resp.json()
        except ValueError as exc:
            raise RuntimeError(f"解析 OpenDigger JSON 失败: {exc}")
    else:
        try:
            with open(path_or_url, "r", encoding="utf-8") as f:
                return json.load(f)
        except OSError as exc:
            raise RuntimeError(f"读取本地 OpenDigger 文件失败: {exc}")
        except ValueError as exc:
            raise RuntimeError(f"解析本地 OpenDigger JSON 失败: {exc}")


def get_developer_metrics(username: str, data: Any) -> Optional[Dict[str, Any]]:
    """从 OpenDigger 数据中抽取指定开发者的活跃度指标。

    兼容多种结构：
    - 若 data 为 dict 且包含用户名键，则直接返回。
    - 若 data 为 list，则尝试寻找带有 'username' 或 'login' 字段匹配的项。

    返回值：匹配到的开发者指标字典，或 None。
    """
    if isinstance(data, dict):
        if username in data:
            item = data.get(username)
            if isinstance(item, dict):
                return item
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("username") == username or item.get("login") == username:
                return item
    return None
