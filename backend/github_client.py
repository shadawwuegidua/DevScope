import os
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

import requests

logger = logging.getLogger('github_client')


class GitHubClient:
    """GitHub REST API 客户端封装。

    环境变量：
    - GITHUB_TOKEN: 可选的个人访问令牌，用于提升速率限制与授权访问。

    速率限制处理逻辑：
    - 读取响应头 `X-RateLimit-Remaining` 与 `X-RateLimit-Reset`。
    - 当剩余额度过低时，休眠到重置时间后再继续请求。
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: str = "https://api.github.com",
        min_remaining: int = 2,
        timeout: int = 60,  # 增加到60秒
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        self.min_remaining = min_remaining
        _token = token or os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "DevScope-Client/1.0",
        }
        if _token:
            headers["Authorization"] = f"Bearer {_token}"
            logger.info("使用 GitHub Token 进行认证")
        else:
            logger.warning("未设置 GITHUB_TOKEN，将使用匿名访问（速率限制较低）")
        self.session.headers.update(headers)

    def _rate_limit_sleep(self, headers: Dict[str, Any]) -> None:
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        try:
            remaining_int = int(remaining) if remaining is not None else None
            reset_int = int(reset) if reset is not None else None
        except ValueError:
            remaining_int = None
            reset_int = None
        if remaining_int is not None and remaining_int <= self.min_remaining:
            if reset_int is not None:
                now = int(time.time())
                sleep_s = max(0, reset_int - now)
                if sleep_s > 0:
                    time.sleep(sleep_s)

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.info(f"发送 GitHub API 请求: {method} {url}")
        try:
            resp = self.session.request(method, url, params=params, timeout=self.timeout)
            logger.info(f"GitHub API 响应: {resp.status_code} {url}")
        except requests.Timeout as exc:
            logger.error(f"GitHub API 请求超时: {url} (timeout={self.timeout}s)")
            raise RuntimeError(f"GitHub API 请求超时: {exc}")
        except requests.ConnectionError as exc:
            logger.error(f"GitHub API 连接错误: {url} - {exc}")
            raise RuntimeError(f"GitHub API 连接失败: {exc}")
        except requests.RequestException as exc:
            logger.error(f"GitHub API 请求异常: {url} - {exc}")
            raise RuntimeError(f"GitHub API 请求失败: {exc}")
        
        self._rate_limit_sleep(resp.headers)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            logger.warning(f"检测到速率限制，等待重置: {url}")
            self._rate_limit_sleep(resp.headers)
        return resp

    def get_user(self, username: str) -> Dict[str, Any]:
        logger.info(f"获取用户信息: {username}")
        resp = self._request("GET", f"/users/{username}")
        if resp.status_code >= 400:
            error_msg = f"获取用户信息失败: {resp.status_code} {resp.text[:200]}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        user_data = resp.json()
        logger.info(f"用户信息获取成功: {user_data.get('login', 'unknown')}")
        return user_data

    def get_repos(self, username: str, per_page: int = 100, max_pages: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"获取仓库列表: {username} (per_page={per_page}, max_pages={max_pages})")
        repos: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params = {"per_page": per_page, "page": page, "type": "owner"}
            logger.info(f"获取仓库列表第 {page} 页")
            resp = self._request("GET", f"/users/{username}/repos", params=params)
            if resp.status_code >= 400:
                error_msg = f"获取仓库列表失败: {resp.status_code} {resp.text[:200]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                logger.info(f"第 {page} 页无数据，停止分页")
                break
            repos.extend(batch)
            logger.info(f"第 {page} 页获取到 {len(batch)} 个仓库，总计 {len(repos)} 个")
            if len(batch) < per_page:
                logger.info(f"第 {page} 页数据不足 {per_page}，已获取全部仓库")
                break
            page += 1
        logger.info(f"仓库列表获取完成: 共 {len(repos)} 个仓库")
        return repos

    def get_commits(
        self,
        owner: str,
        repo: str,
        author: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> List[Dict[str, Any]]:
        commits: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params: Dict[str, Any] = {"per_page": per_page, "page": page}
            if author:
                params["author"] = author
            if since:
                params["since"] = since
            if until:
                params["until"] = until
            resp = self._request("GET", f"/repos/{owner}/{repo}/commits", params=params)
            if resp.status_code >= 400:
                raise RuntimeError(f"获取提交历史失败: {resp.status_code} {resp.text}")
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            commits.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return commits

    def get_user_commit_activity(
        self, username: str, limit_repos: int = 20, per_repo_commits: int = 500
    ) -> Dict[str, Any]:
        """获取用户最近一年的提交活动时间戳。

        策略变更:
        - 采用 "Rolling 12 Months" 观测窗口。
        - limit_repos 和 per_repo_commits 仅作为兜底限制。

        返回:
        {
            "commit_times": [...],
            "window_start": "...",
            "window_end": "..."
        }
        """
        logger.info(f"获取提交活动: {username} (limit_repos={limit_repos})")
        # 1. 计算时间窗口
        now = datetime.now(timezone.utc)
        since_date = now - timedelta(days=365)
        since_str = since_date.isoformat()

        # 2. 获取仓库列表
        repos = self.get_repos(username, per_page=100, max_pages=5)
        logger.info(f"开始处理 {min(len(repos), limit_repos)} 个仓库的提交记录")
        
        timestamps: List[str] = []
        recent_commits: List[Dict[str, Any]] = []
        
        # 3. 遍历仓库 (limit_repos 作为兜底)
        for idx, repo in enumerate(repos[:limit_repos], 1):
            owner = repo.get("owner", {}).get("login", username)
            name = repo.get("name")
            if not name:
                continue
            
            logger.info(f"处理仓库 {idx}/{min(len(repos), limit_repos)}: {owner}/{name}")
            
            # 4. 获取 Commit (使用 since 参数)
            try:
                commits = self.get_commits(
                    owner, 
                    name, 
                    author=username,
                    since=since_str, 
                    per_page=100, 
                    max_pages=max(1, int(per_repo_commits / 100))
                )
                logger.info(f"仓库 {owner}/{name} 获取到 {len(commits)} 条提交")
                for c in commits:
                    try:
                        ts = c["commit"]["author"]["date"]
                        if isinstance(ts, str):
                            timestamps.append(ts)
                            # 收集提交详情
                            recent_commits.append({
                                "message": c["commit"]["message"],
                                "repo_name": f"{owner}/{name}",
                                "date": ts,
                                "url": c["html_url"]
                            })
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"获取仓库 {owner}/{name} 的提交失败: {e}")
                continue
        
        # 按时间倒序排序并取前 20 条
        recent_commits.sort(key=lambda x: x["date"], reverse=True)
        recent_commits = recent_commits[:20]

        logger.info(f"提交活动获取完成: 共 {len(timestamps)} 条提交记录")
        return {
            "commit_times": timestamps,
            "recent_commits": recent_commits,
            "window_start": since_str,
            "window_end": now.isoformat()
        }
