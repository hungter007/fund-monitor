# GitHub Actions 部署指南

## 📋 部署步骤

### 1️⃣ 创建GitHub仓库

```bash
# 在GitHub上创建新仓库
# 仓库名称：fund-monitor 或其他名称
# 初始化为Public（免费用户Actions有分钟限制）
```

### 2️⃣ 上传代码到GitHub

```bash
cd /Users/zhihenghuang/Documents/CC/finance

# 初始化Git仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Fund monitoring system"

# 关联远程仓库（替换YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/fund-monitor.git

# 推送到GitHub
git push -u origin main
```

### 3️⃣ 配置GitHub Secrets

**步骤：**
1. 打开您的GitHub仓库
2. 进入 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`

**需要配置的Secrets：**

| Secret名称 | 值 | 说明 |
|-----------|---|---|
| `PUSHPLUS_TOKEN` | `b7ccb2a3915949bd97c2822e95a5f4a2` | PushPlus推送Token |
| `BIGMODEL_API_KEY` | `8ece9829598a4facafabd8cb47748fc7.FdfZoGatoevxrSwp` | BigModel API密钥 |

### 4️⃣ 启用GitHub Actions

**步骤：**
1. 进入仓库的 `Actions` 标签页
2. 如果提示启用Actions，点击 `I understand my workflows, go ahead and enable them`
3. 确认工作流文件可见：`Actions` → `Fund Monitor`

### 5️⃣ 验证部署

**手动测试：**
1. 进入 `Actions` 标签页
2. 选择 `Fund Monitor` 工作流
3. 点击 `Run workflow` → `Run workflow` 手动触发
4. 查看运行日志，确认成功

**查看定时任务：**
1. 工作流会自动按以下时间运行：
   - 工作日：9:30, 10:30, 11:00, 11:30
   - 工作日：12:00, 12:30, 13:00, 13:30
   - 工作日：14:00, 14:30

### 6️⃣ 查看监控结果

**方式一：GitHub Actions日志**
- 进入 `Actions` → `Fund Monitor` → 查看每次运行的日志

**方式二：PushPlus通知**
- 检查您的手机/邮件，接收监控汇总和离场信号提醒

**方式三：推送记录**
- 登录PushPlus官网：https://www.pushplus.plus/
- 查看推送历史记录

## 🔧 高级配置

### 修改监控频率

编辑 `.github/workflows/monitor.yml` 中的 `cron` 表达式：

```yaml
schedule:
  # 北京时间对应UTC时间需要减8小时
  # 例如：北京时间9:30 = UTC 1:30
  - cron: '30 1 * * 1-5'   # 每天9:30
  - cron: '0 2 * * 1-5'     # 每天10:00

# Cron格式：分 时 日 月 周
# 周一到周五：1-5
# 周一到周日：*
```

### 修改监控标的

编辑 `monitor/config.json` 文件，添加或删除标的：

```json
{
  "targets": [
    {
      "code": "159995",
      "name": "华夏国证半导体芯片ETF",
      "type": "ETF",
      "holdings": 10000,
      "cost_price": 2.5
    }
  ]
}
```

### 添加更多监控时间

```yaml
schedule:
  - cron: '30 1 * * 1-5'   # 9:30
  - cron: '0 2 * * 1-5'     # 10:00
  - cron: '30 2 * * 1-5'   # 10:30
  - cron: '0 3 * * 1-5'     # 11:00
  # ... 添加更多时间点
```

## ⚠️ 注意事项

### GitHub Actions使用限制

**免费账户限制：**
- Public仓库：无限制
- Private仓库：每月2000分钟

**估算用量：**
- 每次运行约1分钟
- 每天10次 × 22天 = 220分钟/月
- **免费账户足够使用**

### 时区设置

GitHub Actions使用UTC时区，计算北京时间：
- 北京时间 = UTC时间 + 8小时
- 例如：北京时间9:30 = UTC 1:30

### 安全建议

1. ✅ 使用Private仓库保护配置文件
2. ✅ 不要在代码中硬编码API密钥
3. ✅ 定期更换API密钥
4. ✅ 监控GitHub Actions使用情况

## 🚀 快速部署命令

```bash
# 一键部署脚本
cd /Users/zhihenghuang/Documents/CC/finance/monitor

# 如果还没有Git仓库
git init
git add .
git commit -m "Add fund monitoring system"
git remote add origin https://github.com/YOUR_USERNAME/fund-monitor.git
git push -u origin main
```

## 📞 获取帮助

如遇问题，检查：
1. Secrets是否正确配置
2. Actions是否已启用
3. 工作流文件路径是否正确
4. 依赖包是否安装成功
