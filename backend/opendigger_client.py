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


def get_user_openrank(username: str, timeout: int = 10) -> Optional[float]:
    """从 OpenDigger 在线 API 获取指定用户的最新 OpenRank 值。

    API 地址格式：
    https://oss.x-lab.info/open_digger/github/{username}/openrank.json

    返回数据格式示例：
    {
        "2023": 123.45,
        "2024": 150.67,
        "2024-01": 12.3,
        "2024-02": 13.5,
        ...
    }

    参数：
        username: GitHub 用户名
        timeout: 请求超时时间（秒）

    返回值：
        最新的年度 OpenRank 值（浮点数），如果获取失败或用户不存在则返回 None
    """
    url = f"https://oss.x-lab.info/open_digger/github/{username}/openrank.json"
    
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 404:
            # 用户在 OpenDigger 数据库中不存在
            return None
        if resp.status_code >= 400:
            return None
        
        data = resp.json()
        if not isinstance(data, dict):
            return None
        
        # 筛选出年度数据（格式为 "2023", "2024" 等）
        year_values = {}
        for key, value in data.items():
            if isinstance(key, str) and key.isdigit() and len(key) == 4:
                try:
                    year_values[int(key)] = float(value)
                except (ValueError, TypeError):
                    continue
        
        if not year_values:
            return None
        
        # 返回最新年份的 OpenRank 值
        latest_year = max(year_values.keys())
        return round(year_values[latest_year], 2)
        
    except requests.RequestException:
        return None
    except (ValueError, KeyError, TypeError):
        return None


def get_repo_openrank(owner: str, repo: str, timeout: int = 10) -> Optional[float]:
    """从 OpenDigger 在线 API 获取指定仓库的最新 OpenRank 值。

    API 地址格式：
    https://oss.x-lab.info/open_digger/github/{owner}/{repo}/openrank.json

    返回值：最新年度的 OpenRank（float）；若仓库未被收录或获取失败返回 None。
    """
    url = f"https://oss.x-lab.info/open_digger/github/{owner}/{repo}/openrank.json"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 404 or resp.status_code >= 400:
            return None
        data = resp.json()
        if not isinstance(data, dict):
            return None
        year_values: Dict[int, float] = {}
        for key, value in data.items():
            if isinstance(key, str) and key.isdigit() and len(key) == 4:
                try:
                    year_values[int(key)] = float(value)
                except (ValueError, TypeError):
                    continue
        if not year_values:
            return None
        latest_year = max(year_values.keys())
        return round(year_values[latest_year], 2)
    except requests.RequestException:
        return None
    except (ValueError, KeyError, TypeError):
        return None
