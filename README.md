# 基金/ETF 智能监控系统

基于离场纪律的自动化监控和推送通知系统。

## 功能特点

- 📊 **多标的监控**：支持ETF和基金的实时监控
- 🤖 **智能分析**：基于四大离场纪律规则自动分析
- 📱 **实时推送**：触发离场信号时通过PushPlus推送通知
- ⏰ **定时执行**：使用GitHub Actions在工作日交易时间定时运行
- 🔔 **汇总报告**：每日监控汇总推送

## 离场纪律规则

### 规则一：缩量破趋势线出一半
- 条件：价格跌破5日均线
- 操作：减仓50%

### 规则二：放量出一半
- 条件：成交量达到前5日均量的130%以上
- 操作：减仓50%

### 规则三：放量破趋势线全部离场
- 条件：价格跌破5日均线 + 成交量异常放大
- 操作：全部离场

### 规则四：K线形态滞涨离场
- 条件：连续大涨后出现长上影线、纺锤线等形态
- 操作：减仓30-50%

## 快速开始

### 1. 获取PushPlus Token

访问 [PushPlus官网](https://www.pushplus.plus/) 注册并获取Token。

### 2. 配置监控标的

编辑 `config.json` 文件：

```json
{
  "pushplus": {
    "token": "YOUR_PUSHPLUS_TOKEN"
  },
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

### 3. 本地测试

```bash
cd monitor
python monitor.py --test-push
```

### 4. 部署到GitHub

1. 创建GitHub仓库
2. 上传代码
3. 配置Secret：`Settings > Secrets > New` 添加 `PUSHPLUS_TOKEN`
4. 启用Actions：`Actions > Enable GitHub Actions`

## 目录结构

```
monitor/
├── config.json          # 配置文件
├── monitor.py           # 主程序
├── data_fetcher.py      # 数据获取模块
├── exit_rules.py        # 离场规则分析模块
├── notifier.py          # 推送通知模块
└── README.md            # 说明文档
```

## 使用说明

### 命令行参数

```bash
# 运行监控并发送通知
python monitor.py

# 运行监控但不发送通知
python monitor.py --no-notify

# 测试推送功能
python monitor.py --test-push

# 使用自定义配置文件
python monitor.py --config my_config.json
```

### GitHub Actions 定时任务

系统会在以下时间自动运行（工作日）：
- 9:30, 10:30
- 11:00, 11:30, 12:00, 12:30
- 13:00, 13:30, 14:00, 14:30

## 注意事项

1. **数据延迟**：基金净值T+1公布，ETF可实时查看
2. **交易时间**：系统只在工作日运行
3. **仅供参考**：本系统仅供参考，不构成投资建议
4. **Token安全**：请妥善保管PushPlus Token

## 依赖项

```
requests>=2.28.0
beautifulsoup4>=4.11.0
```

## 许可证

MIT License
