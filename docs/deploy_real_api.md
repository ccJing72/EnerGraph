# 同步真实接口修改到服务器

## 修改的文件

1. `.env` - 添加了福加 API 配置（注意：不提交到git，需手动同步）
2. `config/site_mapping.yaml` - 新建站点映射配置
3. `src/tools/java_backend.py` - 修改接入真实 API
4. `src/graph/nodes.py` - 注入当前日期到 System Prompt

## 服务器同步步骤

### 1. 提交代码到 git（排除 .env）

```bash
git add config/site_mapping.yaml
git add src/tools/java_backend.py
git add src/graph/nodes.py
git commit -m "[tools] 接入福加真实 API：能耗查询接口"
git push origin main
```

### 2. 服务器拉取代码

```bash
ssh 服务器地址
cd /path/to/EnerGraph
git pull origin main
```

### 3. 手动添加 API 凭证到服务器 .env

在服务器上编辑 `.env` 文件，添加：

```bash
# 福加 API 配置
FUCA_API_BASE_URL=https://aiot-fuca.com
FUCA_API_TOKEN=hAXOi12p1cBBsHtS5DTwvOnB5W5gxqIbZu7qICqIBVmvrm9wqcUGzYC4al4dELUm_1071
FUCA_TENANT_ID=1071
```

### 4. 重启服务

```bash
# 如果使用 systemd
sudo systemctl restart energraph-agent

# 或者如果使用 PM2
pm2 restart energraph-agent

# 或者手动重启
pkill -f "uvicorn src.services.api:app"
python -m uvicorn src.services.api:app --host 0.0.0.0 --port 8000 &
```

### 5. 验证

```bash
curl http://localhost:8000/health
# 应返回: {"status":"ok"}
```

## 注意事项

- `.env` 包含敏感信息，不要提交到 git
- 确保服务器能访问 `https://aiot-fuca.com`
- Token 有效期未知，如失效需联系后端同事更新
