#!/usr/bin/env python3
"""
推送通知模块
集成PushPlus推送服务
"""

import requests
from typing import Dict, Optional
from datetime import datetime


class PushPlusNotifier:
    """PushPlus推送通知器"""

    def __init__(self, token: str, topic: str = ""):
        """
        初始化

        Args:
            token: PushPlus Token
            topic: 推送群组ID（可选）
        """
        self.token = token
        self.topic = topic
        self.api_url = "http://www.pushplus.plus/send"

    def send(self, title: str, content: str, template: str = "html") -> bool:
        """
        发送推送通知

        Args:
            title: 标题
            content: 内容（支持HTML）
            template: 模板类型（html/text）

        Returns:
            是否发送成功
        """
        try:
            data = {
                'token': self.token,
                'title': title,
                'content': content,
                'template': template
            }

            if self.topic:
                data['topic'] = self.topic

            response = requests.post(self.api_url, json=data, timeout=10)
            result = response.json()

            if result.get('code') == 200:
                print(f"推送成功: {title}")
                return True
            else:
                print(f"推送失败: {result.get('msg', '未知错误')}")
                return False

        except Exception as e:
            print(f"推送异常: {e}")
            return False

    def send_exit_signal(self, target: Dict, analysis: Dict, realtime_data: Dict) -> bool:
        """
        发送离场信号通知

        Args:
            target: 标的信息
            analysis: 分析结果
            realtime_data: 实时数据

        Returns:
            是否发送成功
        """
        # 只在触发离场信号时推送
        if not analysis or analysis.get('action') == '持有':
            return True

        # 构建HTML消息
        target_type = 'ETF' if target['type'] == 'ETF' else '基金'
        price = realtime_data.get('price', realtime_data.get('nav', 0))
        change_pct = realtime_data.get('change_pct', 0)

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: #f44336; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .signal {{ background: #fff; padding: 15px; margin: 10px 0; border-left: 4px solid #f44336; }}
                .data-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .label {{ color: #666; }}
                .value {{ font-weight: bold; }}
                .action {{ background: #f44336; color: white; padding: 10px; text-align: center; margin-top: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>⚠️ 离场信号提醒</h2>
                </div>
                <div class="content">
                    <div class="signal">
                        <h3>{target['name']} ({target['code']})</h3>
                        <div class="data-row">
                            <span class="label">类型:</span>
                            <span class="value">{target_type}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">最新价格:</span>
                            <span class="value">{price:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">涨跌幅:</span>
                            <span class="value" style="color: {'red' if change_pct < 0 else 'green'}">
                                {change_pct:+.2f}%
                            </span>
                        </div>
                        <div class="data-row">
                            <span class="label">持仓数量:</span>
                            <span class="value">{target.get('holdings', 0):,}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">成本价格:</span>
                            <span class="value">{target.get('cost_price', 0):.4f}</span>
                        </div>
                    </div>

                    <div class="action">
                        <h3>建议操作: {analysis['action']}</h3>
                    </div>

                    <div style="background: #f0f0f0; padding: 15px; margin: 15px 0; border-radius: 5px;">
                        <p style="margin: 0 0 10px 0;"><strong>🤖 AI分析:</strong></p>
                        <div style="font-size: 14px; line-height: 1.6;">
                            <p style="margin: 5px 0;">• 趋势判断: {analysis.get('trend', '未知')}</p>
                            <p style="margin: 5px 0;">• 置信度: {analysis.get('confidence', '中')}</p>
                            <p style="margin: 5px 0;">• 分析理由: {analysis.get('reason', '')}</p>
                        </div>
                    </div>

                    {self._build_risk_warning(analysis.get('risk_warning'))}

                    <p style="color: #999; font-size: 12px; margin-top: 20px;">
                        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        此为系统自动分析，仅供参考，投资需谨慎
                    </p>

                    <p style="color: #999; font-size: 12px; margin-top: 20px;">
                        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        此为系统自动分析，仅供参考，投资需谨慎
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        title = f"⚠️ 离场信号: {target['name']}"
        return self.send(title, html_content, template='html')

    def send_summary(self, results: list) -> bool:
        """
        发送监控汇总

        Args:
            results: 所有标的的监控结果列表

        Returns:
            是否发送成功
        """
        # 计算统计信息
        total = len(results)
        triggered = sum(1 for r in results if r.get('analysis', {}).get('action') != '持有')

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: #2196F3; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .summary-item {{ text-align: center; }}
                .summary-number {{ font-size: 32px; font-weight: bold; }}
                .target {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .target-signal {{ color: #f44336; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 监控汇总报告</h2>
                </div>
                <div class="content">
                    <div class="summary">
                        <div class="summary-item">
                            <div class="summary-number">{total}</div>
                            <div>监控标的</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number" style="color: #f44336;">{triggered}</div>
                            <div>触发信号</div>
                        </div>
                    </div>

                    <h3>监控详情</h3>
        """

        for result in results:
            target = result.get('target', {})
            analysis = result.get('analysis', {})
            realtime = result.get('realtime_data', {})

            price = realtime.get('price', realtime.get('nav', 0))
            change_pct = realtime.get('change_pct', 0)
            action = analysis.get('action', '持有')

            signal_class = 'target-signal' if action != '持有' else ''

            html_content += f"""
                    <div class="target">
                        <strong>{target.get('name', '')} ({target.get('code', '')})</strong><br>
                        价格: {price:.4f} |
                        涨跌: {change_pct:+.2f}% |
                        <span class="{signal_class}">{action}</span>
                    </div>
            """

        html_content += f"""
                    <p style="color: #999; font-size: 12px; margin-top: 20px;">
                        时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        title = f"📊 监控汇总 ({triggered}/{total} 触发信号)"
        return self.send(title, html_content, template='html')

    def send_test(self) -> bool:
        """发送测试通知"""
        html = """
        <h2>✅ 推送测试成功</h2>
        <p>您的监控系统已正常工作！</p>
        <p>时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "</p>"
        return self.send("监控测试", html)

    def _build_risk_warning(self, warning: str = None) -> str:
        """构建风险警告HTML"""
        if not warning:
            warning = "市场有风险，投资需谨慎。本分析仅供参考，不构成投资建议。"

        return f"""
                    <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 15px 0;">
                        <p style="margin: 0; color: #856404; font-size: 13px;">
                            ⚠️ {warning}
                        </p>
                    </div>
                    """


if __name__ == '__main__':
    # 测试代码
    # 注意：需要配置真实的PushPlus Token才能测试
    notifier = PushPlusNotifier(token="YOUR_TOKEN")

    # 测试简单消息
    # notifier.send("测试", "<h2>测试消息</h2>")

    print("PushPlus通知器已就绪")
    print("请配置config.json中的pushplus.token后使用")
