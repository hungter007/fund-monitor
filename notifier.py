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

    def send_exit_signal(self, target: Dict, analysis: Dict, realtime_data: Dict, execution_time = None) -> bool:
        """
        发送离场信号通知（包含完整技术指标和AI分析）

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

        # 构建HTML消息（添加None值保护）
        target_type = 'ETF' if target['type'] == 'ETF' else '股票'

        # 安全获取数据，设置默认值
        price = realtime_data.get('price') or realtime_data.get('nav') or 0.0
        change_pct = realtime_data.get('change_pct') or 0.0
        prev_close = realtime_data.get('prev_close') or 0.0
        ma5 = realtime_data.get('ma5') or 0.0
        avg_volume = realtime_data.get('avg_volume') or 0.0
        volume = realtime_data.get('volume') or 0
        amount = realtime_data.get('amount') or 0.0  # 添加成交额
        high = realtime_data.get('high') or price
        low = realtime_data.get('low') or price

        # 确保数值类型正确
        try:
            price = float(price) if price else 0.0
            change_pct = float(change_pct) if change_pct else 0.0
            prev_close = float(prev_close) if prev_close else 0.0
            ma5 = float(ma5) if ma5 else 0.0
            avg_volume = float(avg_volume) if avg_volume else 0.0
            volume = float(volume) if volume else 0.0  # 改为float以支持小数
            amount = float(amount) if amount else 0.0
            high = float(high) if high else price
            low = float(low) if low else price
        except (ValueError, TypeError):
            price = change_pct = prev_close = ma5 = avg_volume = volume = amount = 0.0
            high = low = price

        # 计算安全的显示值，避免除零错误
        ma5_diff_pct = 0.0
        if ma5 > 0:
            ma5_diff_pct = (price - ma5) / ma5 * 100
        else:
            ma5_diff_pct = 0.0

        # 计算盈亏情况
        holdings = target.get('holdings', 0) or 0
        cost_price = target.get('cost_price', 0) or 0.0
        current_value = holdings * price
        cost_value = holdings * cost_price
        profit_loss = current_value - cost_value
        profit_pct = 0.0
        if cost_value > 0:
            profit_pct = profit_loss / cost_value * 100

        # 计算盈亏情况
        holdings = target.get('holdings', 0)
        cost_price = target.get('cost_price', 0)
        current_value = holdings * price
        cost_value = holdings * cost_price
        profit_loss = current_value - cost_value
        profit_pct = (profit_loss / cost_value * 100) if cost_value > 0 else 0

        # 信号详情
        signals = realtime_data.get('signals', [])
        signals_html = ""
        if signals:
            signals_html = "<div style='background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px;'>"
            signals_html += "<p style='margin: 0 0 10px 0; color: #856404;'><strong>🚨 触发的离场信号:</strong></p>"
            for signal in signals:
                signals_html += f"<p style='margin: 5px 0; color: #856404;'>• {signal.get('rule_name', '未知')}: {signal.get('action', '')}</p>"
                signals_html += f"<p style='margin: 2px 0 10px 10px; font-size: 12px; color: #856404;'>理由: {signal.get('reason', '')}</p>"
            signals_html += "</div>"

        # 完整的AI分析内容（增强版）
        ai_analysis_html = ""
        if analysis:
            ai_analysis_html = """
            <div style="background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #2196F3;">
                <p style="margin: 0 0 10px 0; color: #1976D2;"><strong>🤖 AI深度分析报告:</strong></p>
                <div style="font-size: 14px; line-height: 1.8; color: #333;">
            """

            # 基础分析信息
            ai_analysis_html += f"<div style='background: #fff; padding: 10px; margin: 10px 0; border-radius: 3px;'>"
            ai_analysis_html += f"<p style='margin: 0 0 8px 0;'><strong>📊 分析结论:</strong></p>"
            ai_analysis_html += f"<p style='margin: 3px 0;'>• <strong>建议操作:</strong> {analysis.get('action', '未知')}</p>"
            ai_analysis_html += f"<p style='margin: 3px 0;'>• <strong>趋势判断:</strong> {analysis.get('trend', '未知')}</p>"
            ai_analysis_html += f"<p style='margin: 3px 0;'>• <strong>置信度:</strong> {analysis.get('confidence', '中')}</p>"
            ai_analysis_html += "</div>"

            # 分析输入数据
            analysis_process = analysis.get('analysis_process', {})
            if analysis_process:
                input_data = analysis_process.get('input_data', {})
                ai_analysis_html += f"<div style='background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px;'>"
                ai_analysis_html += f"<p style='margin: 0 0 8px 0;'><strong>📥 分析输入数据:</strong></p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 标的: {input_data.get('target_name', '未知')}</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 当前价格: {input_data.get('current_price', 0):.4f}</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 涨跌幅: {input_data.get('change_pct', 0):+.2f}%</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 5日均线: {input_data.get('ma5', 0):.4f}</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 5日均量: {input_data.get('avg_volume', 0):.2f}亿</p>"

                signals = input_data.get('signals', [])
                if signals:
                    ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 触发信号: {', '.join(signals)}</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 模型: {analysis_process.get('model_used', '未知')}</p>"
                ai_analysis_html += f"<p style='margin: 2px 0; font-size: 12px;'>• 分析时间: {analysis_process.get('analysis_time', '未知')}</p>"
                ai_analysis_html += "</div>"

            # 详细分析理由
            reason = analysis.get('reason', '')
            if reason:
                ai_analysis_html += f"<div style='background: #fff; padding: 10px; margin: 10px 0; border-radius: 3px;'>"
                ai_analysis_html += f"<p style='margin: 0 0 8px 0;'><strong>📝 详细分析理由:</strong></p>"
                ai_analysis_html += f"<p style='margin: 0; font-size: 13px; line-height: 1.6; color: #333;'>{reason}</p>"
                ai_analysis_html += "</div>"

            # AI原始响应
            ai_raw_response = analysis_process.get('ai_raw_response', '')
            if ai_raw_response:
                ai_analysis_html += f"<div style='background: #fff3e0; padding: 10px; margin: 10px 0; border-radius: 3px;'>"
                ai_analysis_html += f"<p style='margin: 0 0 8px 0;'><strong>🤖 AI完整响应:</strong></p>"
                ai_analysis_html += f"<p style='margin: 0; font-size: 12px; line-height: 1.5; color: #555; font-family: monospace; white-space: pre-wrap;'>{ai_raw_response[:800]}</p>"
                if len(ai_raw_response) > 800:
                    ai_analysis_html += f"<p style='margin: 5px 0 0 0; font-size: 11px; color: #999;'>... (内容过长，已截断)</p>"
                ai_analysis_html += "</div>"

            # 风险提示
            risk_warning = analysis.get('risk_warning')
            if risk_warning:
                ai_analysis_html += f"<div style='margin: 10px 0; padding: 8px; background: #ffebee; border-radius: 3px;'>"
                ai_analysis_html += f"<p style='margin: 0; font-size: 12px; color: #c62828;'>⚠️ 风险提示: {risk_warning}</p>"
                ai_analysis_html += "</div>"

            ai_analysis_html += "</div></div>"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #fff; }}
                .header {{ background: linear-gradient(135deg, #f44336 0%, #e53935 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .section {{ background: #fff; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .section-title {{ font-size: 16px; font-weight: bold; margin: 0 0 12px 0; color: #333; border-bottom: 2px solid #f44336; padding-bottom: 8px; }}
                .data-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .data-row:last-child {{ border-bottom: none; }}
                .label {{ color: #666; font-size: 14px; }}
                .value {{ font-weight: bold; font-size: 14px; }}
                .value.red {{ color: #f44336; }}
                .value.green {{ color: #4CAF50; }}
                .action {{ background: linear-gradient(135deg, #f44336 0%, #e53935 100%); color: white; padding: 15px; text-align: center; margin: 15px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .action h3 {{ margin: 0; font-size: 18px; }}
                .footer {{ text-align: center; padding: 15px; color: #999; font-size: 12px; background: #f5f5f5; border-radius: 0 0 10px 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">⚠️ 离场信号提醒</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">{target['name']} ({target['code']})</p>
                </div>

                <div class="content">
                    <!-- 基本信息 -->
                    <div class="section">
                        <div class="section-title">📊 基本信息</div>
                        <div class="data-row">
                            <span class="label">类型:</span>
                            <span class="value">{target_type}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">最新价格:</span>
                            <span class="value {('red' if change_pct < 0 else 'green')}">{price:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">涨跌幅:</span>
                            <span class="value {('red' if change_pct < 0 else 'green')}">{change_pct:+.2f}%</span>
                        </div>
                        <div class="data-row">
                            <span class="label">昨收:</span>
                            <span class="value">{prev_close:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">最高:</span>
                            <span class="value">{high:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">最低:</span>
                            <span class="value">{low:.4f}</span>
                        </div>
                    </div>

                    <!-- 技术指标 -->
                    <div class="section">
                        <div class="section-title">📈 技术指标</div>
                        <div class="data-row">
                            <span class="label">5日均线:</span>
                            <span class="value">{ma5:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">与MA5差距:</span>
                            <span class="value {('red' if price < ma5 else 'green')}">{ma5_diff_pct:+.2f}%</span>
                        </div>
                        <div class="data-row">
                            <span class="label">成交量:</span>
                            <span class="value">{volume:,.2f}万手</span>
                        </div>
                        <div class="data-row">
                            <span class="label">成交额:</span>
                            <span class="value">{amount:.2f}亿元</span>
                        </div>
                        <div class="data-row">
                            <span class="label">5日均量:</span>
                            <span class="value">{avg_volume:.2f}亿元</span>
                        </div>
                    </div>

                    <!-- 持仓盈亏 -->
                    <div class="section">
                        <div class="section-title">💼 持仓盈亏</div>
                        <div class="data-row">
                            <span class="label">持仓数量:</span>
                            <span class="value">{holdings:,}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">成本价格:</span>
                            <span class="value">{cost_price:.4f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">当前市值:</span>
                            <span class="value">{current_value:,.2f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">成本市值:</span>
                            <span class="value">{cost_value:,.2f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">盈亏金额:</span>
                            <span class="value {('red' if profit_loss < 0 else 'green')}">{profit_loss:+,.2f}</span>
                        </div>
                        <div class="data-row">
                            <span class="label">盈亏比例:</span>
                            <span class="value {('red' if profit_pct < 0 else 'green')}">{profit_pct:+.2f}%</span>
                        </div>
                    </div>

                    <!-- 触发信号 -->
                    {signals_html}

                    <!-- 建议操作 -->
                    <div class="action">
                        <h3>建议操作: {analysis.get('action', '持有')}</h3>
                    </div>

                    <!-- AI分析 -->
                    {ai_analysis_html}

                    <!-- 风险警告 -->
                    {self._build_risk_warning(analysis.get('risk_warning'))}
                </div>

                <div class="footer">
                    <p style="margin: 0;">🕒 {'执行时间: ' + execution_time.strftime('%Y-%m-%d %H:%M:%S') if execution_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0 0 0;">⏰ 监控系统自动执行 | 时区: 北京时间 (UTC+8)</p>
                    <p style="margin: 5px 0 0 0; font-size: 11px; color: #999;">此为系统自动分析，仅供参考，投资需谨慎</p>
                </div>
            </div>
        </body>
        </html>
        """

        title = f"⚠️ 离场信号: {target['name']} - {analysis.get('action', '持有')}"
        return self.send(title, html_content, template='html')

    def send_summary(self, results: list, execution_time = None) -> bool:
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
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 10px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #fff; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; background: #f8f9fa; padding: 15px; border-radius: 8px; }}
                .summary-item {{ text-align: center; flex: 1; }}
                .summary-number {{ font-size: 28px; font-weight: bold; margin-bottom: 5px; }}
                .summary-label {{ font-size: 14px; color: #666; }}
                .target {{ background: #fff; padding: 15px; margin: 10px 0; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
                .target:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                .section-title {{ font-size: 16px; font-weight: bold; margin: 0 0 15px 0; color: #333; }}
                .footer {{ text-align: center; padding: 15px; background: #f8f9fa; color: #666; font-size: 12px; border-top: 1px solid #e0e0e0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">📊 监控汇总报告</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">自动监控系统 - 实时数据</p>
                </div>

                <div class="content">
                    <div class="summary">
                        <div class="summary-item">
                            <div class="summary-number" style="color: #2196F3;">{total}</div>
                            <div class="summary-label">监控标的</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number" style="color: #f44336;">{triggered}</div>
                            <div class="summary-label">触发信号</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number" style="color: #4CAF50;">{total - triggered}</div>
                            <div class="summary-label">正常持有</div>
                        </div>
                    </div>

                    <div class="section-title">📋 监控详情</div>
        """

        for result in results:
            target = result.get('target', {})
            analysis = result.get('analysis', {})
            realtime = result.get('realtime_data', {})

            # 安全获取数据，设置默认值
            price = realtime.get('price') or realtime.get('nav') or 0.0
            change_pct = realtime.get('change_pct') or 0.0
            action = analysis.get('action', '持有')
            ma5 = realtime.get('ma5') or 0.0
            volume = realtime.get('volume') or 0
            avg_volume = realtime.get('avg_volume') or 0.0

            # 确保数值类型正确
            try:
                price = float(price) if price else 0.0
                change_pct = float(change_pct) if change_pct else 0.0
                ma5 = float(ma5) if ma5 else 0.0
                volume = float(volume) if volume else 0.0  # 改为float以支持小数
                avg_volume = float(avg_volume) if avg_volume else 0.0
            except (ValueError, TypeError):
                price = change_pct = ma5 = avg_volume = volume = 0.0

            signal_class = 'target-signal' if action != '持有' else ''
            status_color = '#f44336' if action != '持有' else '#4CAF50'

            # 计算盈亏
            holdings = target.get('holdings', 0) or 0
            cost_price = target.get('cost_price', 0) or 0.0
            profit_pct = ((price - cost_price) / cost_price * 100) if cost_price > 0 else 0

            html_content += f"""
                    <div class="target" style="border-left: 3px solid {status_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <strong style="font-size: 15px;">{target.get('name', '')} ({target.get('code', '')})</strong>
                            <span style="color: {status_color}; font-weight: bold; padding: 3px 8px; background: rgba({'244, 67, 54' if action != '持有' else '76, 175, 80'}, 0.1); border-radius: 3px;">{action}</span>
                        </div>
                        <div style="font-size: 13px; color: #666; line-height: 1.8;">
                            <span style="margin-right: 15px;">💰 价格: {price:.4f}</span>
                            <span style="margin-right: 15px; color: {'red' if change_pct < 0 else 'green'};">📈 涨跌: {change_pct:+.2f}%</span>
                            <span style="margin-right: 15px;">📊 MA5: {ma5:.4f}</span>
                        </div>
                        <div style="font-size: 12px; color: #999; margin-top: 4px;">
                            <span style="margin-right: 15px;">🏦 持仓: {holdings:,}</span>
                            <span style="margin-right: 15px; color: {'red' if profit_pct < 0 else 'green'};">💵 盈亏: {profit_pct:+.2f}%</span>
                            <span style="margin-right: 15px;">📦 成交量: {volume:,.2f}万手</span>
                        </div>
                    </div>
            """

        html_content += f"""
                </div>

                <div class="footer">
                    <p style="margin: 0;">🕒 {'执行时间: ' + execution_time.strftime('%Y-%m-%d %H:%M:%S') if execution_time else datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0 0 0;">⏰ 监控系统自动执行 | 时区: 北京时间 (UTC+8)</p>
                    <p style="margin: 5px 0 0 0; font-size: 11px; color: #999;">此为系统自动分析，仅供参考，投资需谨慎</p>
                </div>
            </div>
        </body>
        </html>
        """

        time_str = execution_time.strftime('%H:%M') if execution_time else datetime.now().strftime('%H:%M')
        title = f"📊 监控汇总 ({triggered}/{total} 触发信号) - {time_str}"
        return self.send(title, html_content, template='html')

    def send_test(self) -> bool:
        """发送测试通知（增强版）"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; text-align: center; }}
                .icon {{ font-size: 48px; margin-bottom: 20px; }}
                .success {{ color: #4CAF50; font-size: 24px; font-weight: bold; margin-bottom: 15px; }}
                .info {{ color: #666; font-size: 16px; line-height: 1.6; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">✅ 测试成功</h2>
                </div>
                <div class="content">
                    <div class="icon">🎉</div>
                    <div class="success">推送服务正常工作</div>
                    <p class="info">
                        恭喜！您的基金/ETF监控系统已成功配置。<br>
                        系统将在交易时间内自动监控并发送通知。
                    </p>
                    <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                        <p style="margin: 0; color: #666; font-size: 14px;">
                            <strong>监控功能：</strong><br>
                            ✅ 实时价格监控<br>
                            ✅ 技术指标分析<br>
                            ✅ AI智能分析<br>
                            ✅ 离场信号推送<br>
                            ✅ 定时汇总报告
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p style="margin: 0;">🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p style="margin: 5px 0 0 0;">基金/ETF智能监控系统</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send("🎉 监控测试成功", html, template='html')

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
