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
        timeout: Optional[int] = None,  # 允许通过环境变量覆盖
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # 允许通过环境变量 GITHUB_TIMEOUT（秒）配置请求超时，默认 60 秒
        if timeout is None:
            try:
                timeout_env = os.environ.get("GITHUB_TIMEOUT")
                timeout = int(timeout_env) if timeout_env else 60
            except Exception:
                timeout = 60
        self.timeout = timeout
        self.min_remaining = min_remaining
        _token = token or os.environ.get("GITHUB_TOKEN")
        headers = {
            # 启用 topics 预览字段（mercy-preview），避免列表接口缺失 topics 数据
            "Accept": "application/vnd.github+json, application/vnd.github.mercy-preview+json",
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

    def get_user_events_public(self, username: str, per_page: int = 100, max_pages: int = 5) -> List[Dict[str, Any]]:
        """获取用户的公开事件，用于发现其参与贡献的仓库。

        仅用于收集仓库标识，不做深入事件分析。
        """
        events: List[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            params = {"per_page": per_page, "page": page}
            resp = self._request("GET", f"/users/{username}/events/public", params=params)
            if resp.status_code >= 400:
                logger.warning(f"获取用户事件失败: {resp.status_code} {resp.text[:200]}")
                break
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            events.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        logger.info(f"用户事件获取完成: 共 {len(events)} 条")
        return events

    def get_user_contributed_repos(self, username: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """根据公开事件收集用户参与过的仓库，并拉取仓库详情（含 topics）。"""
        events = self.get_user_events_public(username, per_page=100, max_pages=max_pages)
        repo_full_names: set[str] = set()
        for ev in events:
            repo = ev.get("repo") or {}
            full = repo.get("name")  # 格式: owner/name
            if isinstance(full, str) and "/" in full:
                repo_full_names.add(full)

        repos: List[Dict[str, Any]] = []
        for full in list(repo_full_names)[:200]:  # 限制最多200个，避免过多请求
            try:
                owner, name = full.split("/", 1)
                resp = self._request("GET", f"/repos/{owner}/{name}")
                if resp.status_code >= 400:
                    logger.warning(f"获取仓库详情失败: {full} {resp.status_code}")
                    continue
                repos.append(resp.json())
            except Exception as e:
                logger.warning(f"解析仓库 {full} 失败: {e}")
                continue
        logger.info(f"贡献仓库详情获取完成: 共 {len(repos)} 个")
        return repos

    def get_user_repos_union(self, username: str, include_contrib: bool = True) -> List[Dict[str, Any]]:
        """返回用户拥有的仓库与参与贡献的仓库的并集（去重），按活跃时间倒序排列。"""
        owned = self.get_repos(username)
        if include_contrib:
            contrib = self.get_user_contributed_repos(username)
        else:
            contrib = []
        # 去重依据 full_name；没有则用 name
        seen: set[str] = set()
        union: List[Dict[str, Any]] = []
        for r in owned + contrib:
            key = r.get("full_name") or r.get("name")
            if not key or key in seen:
                continue
            seen.add(key)
            union.append(r)
            
        # 按 pushed_at 倒序排序 (优先检查最近活跃仓库)
        # 这确保了 get_user_commit_activity 中的切片能命中真正活跃的仓库
        def get_sort_key(repo: Dict[str, Any]) -> str:
            val = repo.get("pushed_at") or repo.get("updated_at") or ""
            return str(val)
            
        union.sort(key=get_sort_key, reverse=True)
            
        logger.info(f"仓库并集完成: owned={len(owned)}, contrib={len(contrib)}, union={len(union)}")
        return union

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
        self, 
        username: str, 
        limit_repos: int = 20, 
        per_repo_commits: int = 500,
        repos: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """获取用户最近一年的提交活动时间戳。

        参数:
        - repos:如果不传，内部会调用 get_user_repos_union 获取。
          如果建议传入已获取并排序好的 repos 列表，减少 API 调用并保证一致性。

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
        # 如果未传入 repos，则自行获取并排序
        if repos is None:
            repos = self.get_user_repos_union(username)
        
        # 获取用户 Profile 用于辅助匹配 (避免反复调用，应该在上层获取，这里简单再获取一次或假设 username)
        # 为节约 API，这里只使用 username 和 repo owner name 进行匹配
        
        logger.info(f"开始处理 {min(len(repos), limit_repos)} 个仓库的提交记录")
        
        timestamps: List[str] = []
        recent_commits: List[Dict[str, Any]] = []
        commit_counts_by_repo: Dict[str, int] = {}
        
        # 3. 遍历仓库 (limit_repos 作为兜底)
        for idx, repo in enumerate(repos[:limit_repos], 1):
            owner = repo.get("owner", {}).get("login", username)
            name = repo.get("name")
            if not name:
                continue
            
            logger.info(f"处理仓库 {idx}/{min(len(repos), limit_repos)}: {owner}/{name}")
            
            repo_commits: List[Dict[str, Any]] = []
            
            # 4.1 尝试标准获取 (author=username)
            try:
                standard_commits = self.get_commits(
                    owner, 
                    name, 
                    author=username,
                    since=since_str, 
                    per_page=100, 
                    max_pages=max(1, int(per_repo_commits / 100))
                )
                repo_commits.extend(standard_commits)
            except Exception as e:
                logger.warning(f"获取仓库 {owner}/{name} 的提交失败: {e}")
            
            # 4.2 补救策略：如果标准获取为空，尝试无 filter 获取并客户端匹配
            # 场景：用户 Git 邮箱未绑定 GitHub 账户，导致 API author 筛选失效
            # 修改：不仅针对 owner，对所有活跃仓库都尝试补救，特别是 contrib 仓库
            if not repo_commits:
                logger.info(f"仓库 {owner}/{name} 标准获取为空，尝试名称匹配补救...")
                try:
                    fallback_commits = self.get_commits(
                        owner,
                        name,
                        author=None, # 不按 author 筛选
                        since=since_str,
                        per_page=100, # 检查最近 100 条，增加命中概率
                        max_pages=1
                    )
                    
                    # 客户端过滤：匹配 Git Author Name
                    username_lower = username.lower()
                    for c in fallback_commits:
                        commit_author = c.get("commit", {}).get("author", {})
                        author_name = commit_author.get("name", "").lower()
                        
                        # 简单的模糊匹配规则：如果 Git Name 等于用户名，或包含用户名
                        if username_lower == author_name or username_lower in author_name:
                            repo_commits.append(c)
                            
                    if repo_commits:
                        logger.info(f"补救成功！在 {owner}/{name} 中找到 {len(repo_commits)} 条潜在提交")
                        
                except Exception as e:
                    logger.warning(f"补救策略执行失败 {owner}/{name}: {e}")

            logger.info(f"仓库 {owner}/{name} 最终有效提交: {len(repo_commits)}")
            
            # 5. 统计与聚合
            if repo_commits:
                repo_full = f"{owner}/{name}"
                commit_counts_by_repo[repo_full] = len(repo_commits)
                for c in repo_commits:
                    try:
                        # 优先使用 commit.author.date，其次 committer.date
                        c_info = c.get("commit", {})
                        ts = c_info.get("author", {}).get("date") or c_info.get("committer", {}).get("date")
                        
                        if isinstance(ts, str):
                            timestamps.append(ts)
                            # 收集提交详情
                            recent_commits.append({
                                "message": c_info.get("message", ""),
                                "repo_name": repo_full,
                                "date": ts,
                                "url": c.get("html_url", "")
                            })
                    except Exception:
                        continue
        
        # 按时间倒序排序并取前 20 条
        recent_commits.sort(key=lambda x: x["date"], reverse=True)
        recent_commits = recent_commits[:20]

        logger.info(f"提交活动获取完成: 共 {len(timestamps)} 条提交记录")
        return {
            "commit_times": timestamps,
            "recent_commits": recent_commits,
            "commit_counts_by_repo": commit_counts_by_repo,
            "window_start": since_str,
            "window_end": now.isoformat()
        }
