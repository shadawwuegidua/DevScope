# 🔒 安全注意事项

## ⚠️ 重要安全提醒

### 1. GitHub Token 安全

**已修复的安全问题**：
- ✅ `.env` 文件已从 Git 追踪中移除
- ✅ `__pycache__` 缓存文件已清理
- ✅ `.gitignore` 已正确配置

**如果 Token 已泄露，请立即**：
1. 访问 https://github.com/settings/tokens
2. 撤销已泄露的 Token
3. 生成新的 Token
4. 更新本地 `.env` 文件

### 2. 环境变量配置

**首次设置**：
```bash
# 1. 复制模板文件
cp backend/.env.example backend/.env

# 2. 编辑 .env 文件，填入你的 Token
# GITHUB_TOKEN=ghp_your_new_token_here
```

**验证配置**：
```bash
cd backend
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token loaded:', 'Yes' if os.getenv('GITHUB_TOKEN') else 'No')"
```

### 3. 团队协作注意事项

**新成员加入流程**：
1. Clone 仓库后，自行创建 `.env` 文件
2. 从团队负责人处获取 Token（或自己生成）
3. **绝不**通过聊天工具、邮件发送 Token
4. **绝不**将 `.env` 文件提交到 Git

**已忽略的敏感文件**（见 `.gitignore`）：
- `.env` 及其变体
- `*.key`, `*.pem` 等密钥文件
- `secrets.json`, `config/secrets.yaml`
- 数据库文件 `*.db`, `*.sqlite`

### 4. Git 历史清理（如果需要）

如果 Token 已在历史提交中暴露，需要清理 Git 历史：

```bash
# 警告：这会重写 Git 历史，需要团队协调
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

**但更简单的做法是**：直接撤销泄露的 Token，生成新的。

### 5. 最佳实践清单

- [ ] `.env` 文件只存在本地，未被提交
- [ ] 使用 `.env.example` 作为配置模板
- [ ] 定期更换 Token（建议每 3 个月）
- [ ] Token 权限最小化（仅授予必要权限）
- [ ] 使用 GitHub Actions 时用 Secrets 存储 Token
- [ ] 监控 GitHub Token 使用情况（查看 API 速率限制）

### 6. 相关文档

- [GitHub Token 管理指南](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [.gitignore 最佳实践](https://git-scm.com/docs/gitignore)
- [环境变量安全指南](https://12factor.net/config)

---

**最后更新**: 2024-12-17  
**维护者**: DevScope 团队
