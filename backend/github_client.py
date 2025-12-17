import os
import time
from typing import List, Optional, Dict, Any

import requests


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
        timeout: int = 30,
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
        try:
            resp = self.session.request(method, url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"GitHub API 请求失败: {exc}")
        self._rate_limit_sleep(resp.headers)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            self._rate_limit_sleep(resp.headers)
        return resp

    def get_user(self, username: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/users/{username}")
        if resp.status_code >= 400:
            raise RuntimeError(f"获取用户信息失败: {resp.status_code} {resp.text}")
        return resp.json()

    def get_repos(self, username: str, per_page: int = 100, max_pages: int = 10) -> List[Dict[str, Any]]:
        repos: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params = {"per_page": per_page, "page": page, "type": "owner"}
            resp = self._request("GET", f"/users/{username}/repos", params=params)
            if resp.status_code >= 400:
                raise RuntimeError(f"获取仓库列表失败: {resp.status_code} {resp.text}")
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            repos.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return repos

    def get_commits(
        self,
        owner: str,
        repo: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> List[Dict[str, Any]]:
        commits: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params: Dict[str, Any] = {"per_page": per_page, "page": page}
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
        self, username: str, limit_repos: int = 5, per_repo_commits: int = 100
    ) -> List[str]:
        repos = self.get_repos(username, per_page=limit_repos, max_pages=1)
        timestamps: List[str] = []
        for repo in repos[:limit_repos]:
            owner = repo.get("owner", {}).get("login", username)
            name = repo.get("name")
            if not name:
                continue
            commits = self.get_commits(owner, name, per_page=per_repo_commits, max_pages=1)
            for c in commits:
                try:
                    ts = c["commit"]["author"]["date"]
                    if isinstance(ts, str):
                        timestamps.append(ts)
                except Exception:
                    continue
        return timestamps
