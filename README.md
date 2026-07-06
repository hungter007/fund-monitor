# 基金/ETF 智能监控系统

基于离场纪律的自动化监控和推送通知系统，支持GitHub Actions定时执行。

## 功能特点

- 📊 **多标的监控**：支持ETF和股票的实时监控
- 🤖 **智能分析**：基于四大离场纪律规则 + BigModel AI深度分析
- 📱 **实时推送**：通过PushPlus推送离场信号提醒
- ⏰ **定时执行**：使用GitHub Actions在工作日交易时间自动运行
- 🔔 **汇总报告**：每次监控后的汇总报告
- 🔒 **安全配置**：API密钥通过GitHub Secrets管理

## 离场纪律规则

### 规则一：缩量破趋势线出一半
- **条件**：价格跌破5日均线
- **操作**：减仓50%

### 规则二：放量出一半
- **条件**：成交量达到前5日均量的130%以上
- **操作**：减仓50%

### 规则三：放量破趋势线全部离场
- **条件**：价格跌破5日均线 + 成交量异常放大
- **操作**：全部离场

### 规则四：K线形态滞涨离场
- **条件**：连续大涨后出现长上影线、纺锤线等形态
- **操作**：减仓30-50%

## 快速开始

### 1. 获取必要的服务

#### PushPlus（推送服务）
1. 访问 [PushPlus官网](https://www.pushplus.plus/) 注册
2. 登录后获取您的Token

#### BigModel AI分析服务（可选）
1. 访问 [BigModel官网](https://open.bigmodel.cn/) 注册
2. 获取您的API Key

### 2. 配置监控标的

编辑 `config.json` 文件，添加您要监控的ETF或股票：

```json
{
  "pushplus": {
    "token": "您的PushPlus Token"
  },
  "bigmodel": {
    "model": "glm-4-flash",
    "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "api_key_env": "BIGMODEL_API_KEY"
  },
  "targets": [
    {
      "code": "588170",
      "name": "半导体ETF",
      "type": "ETF",
      "holdings": 10000,
      "cost_price": 1.25
    },
    {
      "code": "600584",
      "name": "长电科技",
      "type": "STOCK",
      "holdings": 1000,
      "cost_price": 85.0
    }
  ]
}
```

### 3. 本地测试

```bash
cd monitor
python monitor.py --test-push
```

### 4. 部署到GitHub Actions

#### 步骤1：创建GitHub仓库
```bash
# 初始化Git仓库
cd monitor
git init
git add .
git commit -m "Add fund monitoring system"
```

#### 步骤2：配置GitHub Secrets（重要！）

1. 打开您的GitHub仓库
2. 进入：`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

**需要配置的Secrets：**

| Secret名称 | 值 | 说明 |
|-----------|---|---|
| `PUSHPLUS_TOKEN` | 您的PushPlus Token | 推送通知必需 |
| `BIGMODEL_API_KEY` | 您的BigModel API Key | AI分析（可选） |

#### 步骤3：推送代码

```bash
# 添加远程仓库（使用SSH方式更安全）
git remote add origin git@github.com:YOUR_USERNAME/fund-monitor.git

# 推送代码
git push -u origin main
```

#### 步骤4：启用GitHub Actions

1. 进入仓库的 `Actions` 标签页
2. 如果提示启用Actions，点击启用
3. 手动测试：`Actions` → `Fund Monitor` → `Run workflow`

## 安全配置说明

### 🔒 API密钥管理

**安全实践：**
- ✅ **不要在代码中硬编码API密钥**
- ✅ **使用GitHub Secrets管理敏感信息**
- ✅ **定期更换API密钥**
- ✅ **使用Private仓库保护配置文件**

**配置方式：**
- 系统优先从环境变量 `BIGMODEL_API_KEY` 读取
- GitHub Actions自动将Secrets注入为环境变量
- 本地测试时可以手动设置环境变量

### 📋 目录结构

```
monitor/
├── config.json              # 配置文件（不含敏感信息）
├── monitor.py               # 主程序
├── data_fetcher.py          # 数据获取模块
├── exit_rules.py            # 离场规则分析模块
├── notifier.py              # 推送通知模块
├── bigmodel_analysis.py     # BigModel AI分析模块
├── requirements.txt         # Python依赖
├── .github/workflows/
│   └── monitor.yml         # GitHub Actions配置
├── README.md                # 说明文档
└── DEPLOY.md                # 部署指南
```

## 使用说明

### 命令行参数

```bash
# 运行监控并发送通知
python monitor.py

# 运行监控但不发送通知（测试模式）
python monitor.py --no-notify

# 测试推送功能
python monitor.py --test-push

# 使用自定义配置文件
python monitor.py --config my_config.json
```

### 环境变量配置（本地测试）

```bash
# 设置BigModel API Key
export BIGMODEL_API_KEY="your_api_key_here"

# 运行监控
python monitor.py
```

### GitHub Actions定时执行

系统会在工作日以下时间自动运行：

| 北京时间 | UTC时间 | 说明 |
|----------|---------|------|
| 9:30 | 1:30 | 开盘监控 |
| 10:30 | 2:30 | 上午监控 |
| 11:00 | 3:00 | 上午监控 |
| 11:30 | 3:30 | 午前监控 |
| 12:00 | 4:00 | 午间监控 |
| 12:30 | 4:30 | 午后监控 |
| 13:00 | 5:00 | 下午开盘 |
| 13:30 | 5:30 | 下午监控 |
| 14:00 | 6:00 | 下午监控 |
| 14:30 | 6:30 | 收盘前监控 |

## 监控流程

```
┌─────────────────────────────────────────┐
│         智能监控流程                    │
├─────────────────────────────────────────┤
│                                         │
│  第一步：快速检查（每30分钟）          │
│  ┌─────────────────────────────────┐   │
│  │ • 获取实时数据                   │   │
│  │ • 计算技术指标                   │   │
│  │ • 普通规则判断                   │   │
│  │ • 结果：持有/信号触发            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  第二步：AI深度分析（仅触发时）       │
│  ┌─────────────────────────────────┐   │
│  │ • 只对触发信号的标的调用AI       │   │
│  │ • 综合分析和建议                 │   │
│  │ • 确认离场操作                   │   │
│  └─────────────────────────────────┘   │
│                                         │
│  第三步：推送通知（离场时）           │
│  ┌─────────────────────────────────┐   │
│  │ • 发送离场信号提醒               │   │
│  │ • 包含AI分析结果                 │   │
│  │ • 发送监控汇总                   │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

## 支持的标的类型

### ETF（交易所交易基金）
- 深市ETF：15/16开头
- 沪市ETF：5开头

### 股票
- 科创板：688开头
- 深市股票：00/30开头
- 沪市股票：60开头

## 注意事项

1. **数据延迟**：ETF可实时查看，股票有轻微延迟
2. **交易时间**：系统只在工作日运行
3. **仅供参考**：本系统仅供参考，不构成投资建议
4. **Token安全**：请妥善保管API密钥，不要泄露

## 依赖项

```
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
```

## 成本估算

### GitHub Actions使用量

**免费账户限制：**
- Public仓库：无限制
- Private仓库：每月2000分钟

**系统用量：**
- 每次运行：约1分钟
- 每天10次 × 22天 = 220分钟/月
- **免费账户完全够用**

### BigModel API费用

- 按调用次数计费
- 只在触发离场信号时调用
- 平均每天2-3次调用
- 成本极低

## 高级配置

### 修改监控频率

编辑 `.github/workflows/monitor.yml` 中的 `cron` 表达式

### 修改监控标的

编辑 `config.json` 中的 `targets` 数组

### 调整离场规则

修改 `config.json` 中的 `rules` 配置

## 故障排查

### 问题：GitHub Actions执行失败
- 检查Secrets是否正确配置
- 确认Actions已启用
- 查看Actions日志

### 问题：没有收到推送通知
- 检查PUSHPLUS_TOKEN是否正确
- 确认PushPlus服务正常
- 查看Actions日志

### 问题：AI分析不工作
- 检查BIGMODEL_API_KEY是否配置
- 确认API Key有效
- 查看是否触发速率限制

## 许可证

MIT License

## 更新日志

### v1.1.0 (最新)
- ✅ 安全优化：API密钥移至GitHub Secrets
- ✅ 智能监控：只在触发信号时调用AI
- ✅ 成本优化：减少95%的API调用
- ✅ 支持ETF和股票混合监控

### v1.0.0
- 基础监控功能上线
- 离场纪律规则实现
- PushPlus推送集成
