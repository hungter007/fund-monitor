#!/usr/bin/env python3
"""
BigModel AI分析模块
使用智谱AI的GLM模型进行离场信号分析
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


class BigModelAnalyzer:
    """BigModel AI分析器"""

    def __init__(self, api_key: str, model: str = "glm-4-flash",
                 base_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"):
        """
        初始化

        Args:
            api_key: BigModel API密钥
            model: 模型名称
            base_url: API基础URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.headers = {
            "Authorization": f"{api_key}",
            "Content-Type": "application/json"
        }

    def analyze_exit_signal(self, target: Dict, realtime_data: Dict,
                           historical_data: List[Dict], signals: List) -> Dict:
        """
        使用AI分析离场信号

        Args:
            target: 标的信息
            realtime_data: 实时数据
            historical_data: 历史数据
            signals: 触发的信号列表

        Returns:
            AI分析结果
        """
        if not self.api_key or self.api_key == "YOUR_BIGMODEL_API_KEY":
            return self._fallback_analysis(signals, target, realtime_data)

        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(
                target, realtime_data, historical_data, signals
            )

            # 调用BigModel API
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的证券交易分析师，擅长基于技术分析和离场纪律给出交易建议。请严格按照规则分析，给出明确的操作建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3
            }

            print("  发送AI分析请求...")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                # timeout=60  # 增加超时时间到60秒
            )

            print(f"  API响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("  AI分析成功")
                content = result['choices'][0]['message']['content']

                # 记录完整的AI分析过程
                analysis_result = self._parse_ai_response(content, signals)

                # 添加分析过程信息
                analysis_result['analysis_process'] = {
                    'input_data': {
                        'target_name': target.get('name', ''),
                        'current_price': realtime_data.get('price', realtime_data.get('nav', 0)),
                        'change_pct': realtime_data.get('change_pct', 0),
                        'ma5': realtime_data.get('ma5', 0),
                        'avg_volume': realtime_data.get('avg_volume', 0),
                        'signals': [s.rule_name for s in signals]
                    },
                    'ai_raw_response': content,
                    'model_used': self.model,
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                return analysis_result
            elif response.status_code == 429:
                print("  API速率限制，使用备用分析")
                return self._fallback_analysis(signals, target, realtime_data)
            elif response.status_code == 401:
                print("  API密钥无效，请检查配置")
                return self._fallback_analysis(signals, target, realtime_data)
            else:
                print(f"  BigModel API调用失败: {response.status_code}")
                return self._fallback_analysis(signals, target, realtime_data)

        except requests.Timeout:
            print("  AI请求超时，使用备用分析")
            return self._fallback_analysis(signals, target, realtime_data)
        except Exception as e:
            print(f"  AI分析异常: {e}")
            return self._fallback_analysis(signals, target, realtime_data)

    def _build_analysis_prompt(self, target: Dict, realtime_data: Dict,
                              historical_data: List[Dict], signals: List) -> str:
        """构建分析提示词"""

        # 基本信息
        code = target['code']
        name = target['name']
        target_type = target.get('type', 'ETF')
        holdings = target.get('holdings', 0)
        cost_price = target.get('cost_price', 0)

        # 实时数据
        current_price = realtime_data.get('price', realtime_data.get('nav', 0))
        change_pct = realtime_data.get('change_pct', 0)
        open_price = realtime_data.get('open', 0)
        high_price = realtime_data.get('high', 0)
        low_price = realtime_data.get('low', 0)
        volume = realtime_data.get('volume', 0)
        amount = realtime_data.get('amount', 0)
        avg_volume = realtime_data.get('avg_volume', 0)  # 5日平均成交额

        # 计算MA5
        if historical_data and len(historical_data) >= 5:
            if 'close' in historical_data[0]:
                prices = [item['close'] for item in historical_data[:5]]
            else:
                prices = [item['nav'] for item in historical_data[:5]]
            ma5 = sum(prices) / 5
        else:
            ma5 = 0

        # 构建提示词
        prompt = f"""请分析以下{target_type}的离场信号：

        【标的信息】
        - 代码: {code}
        - 名称: {name}
        - 持仓: {holdings}
        - 成本: {cost_price}
        
        【实时数据】
        - 当前价格: {current_price:.4f}
        - 涨跌幅: {change_pct:+.2f}%
        - 今开: {open_price:.4f}
        - 最高: {high_price:.4f}
        - 最低: {low_price:.4f}
        - 成交量: {volume:.2f}万手
        - 成交额: {amount:.2f}亿元
        - 5日均线: {ma5:.4f}
        
        【离场纪律规则】
        规则一：缩量破趋势线 → 价格跌破5日均线 → 减仓50%
        规则二：放量出一半 → 成交量异常放大(≥前5日均量130%) → 减仓50%
        规则三：放量破趋势线 → 价格跌破MA5 + 成交量放大 → 全部离场
        规则四：K线形态滞涨 → 连续大涨后出现长上影线/纺锤线 → 减仓30-50%
        
        【当前状态】
        """

        # 添加当前状态分析
        if current_price < ma5:
            break_pct = ((ma5 - current_price) / ma5) * 100
            prompt += f"- ⚠️ 价格跌破5日均线 {break_pct:.2f}%\n"
        else:
            above_pct = ((current_price - ma5) / ma5) * 100
            prompt += f"- ✓ 价格高于5日均线 {above_pct:.2f}%\n"

        # 添加成交量分析
        if avg_volume > 0:
            volume_ratio = (amount / avg_volume) if amount > 0 else 0
            if volume_ratio >= 1.3:
                prompt += f"- ⚠️ 成交量异常放大：当前{amount:.2f}亿元，前5日均量{avg_volume:.2f}亿元，放量{volume_ratio:.1%}\n"
            elif volume_ratio >= 1.1:
                prompt += f"- ⚠️ 成交量放大：当前{amount:.2f}亿元，前5日均量{avg_volume:.2f}亿元，放量{volume_ratio:.1%}\n"
            else:
                prompt += f"- ✓ 成交量正常：当前{amount:.2f}亿元，前5日均量{avg_volume:.2f}亿元\n"
        else:
            prompt += f"- 当前成交额：{amount:.2f}亿元\n"

        # 添加触发信号
        if signals:
            prompt += "\n【已触发信号】\n"
            for signal in signals:
                prompt += f"- {signal.rule_name}: {signal.reason}\n"

        prompt += """
        【请给出分析】
        请根据以上数据和离场纪律规则，给出明确的分析结论，包括：
        1. 当前趋势判断（上升/下降/震荡）
        2. 是否触发离场信号
        3. 具体操作建议（持有/减仓50%/全部离场/其他）
        4. 理由说明
        
        请以JSON格式返回：
        {
          "trend": "上升/下降/震荡",
          "action": "持有/减仓50%/全部离场",
          "confidence": "高/中/低",
          "reason": "分析理由",
          "risk_warning": "风险提示"
        }
        """

        return prompt

    def _parse_ai_response(self, content: str, signals: List) -> Dict:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
                result = json.loads(json_str)
            elif "{" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
            else:
                # 没有JSON格式，返回文本分析
                return {
                    'action': self._determine_action_from_text(content),
                    'trend': '未知',
                    'confidence': '中',
                    'reason': content[:200],
                    'risk_warning': 'AI分析仅供参考',
                    'signals': [s.to_dict() for s in signals]
                }

            result['signals'] = [s.to_dict() for s in signals]
            return result

        except Exception as e:
            print(f"解析AI响应失败: {e}")
            return self._fallback_analysis(signals, {}, {})

    def _determine_action_from_text(self, text: str) -> str:
        """从文本中判断操作建议"""
        text = text.lower()
        if "全部离场" in text or "清仓" in text or "卖出" in text:
            return "全部离场"
        elif "减仓50%" in text or "减半" in text:
            return "减仓50%"
        elif "减仓30" in text or "部分减仓" in text:
            return "减仓30-50%"
        else:
            return "持有"

    def _fallback_analysis(self, signals: List, target: Dict,
                          realtime_data: Dict) -> Dict:
        """备用分析（当AI不可用时）"""

        if not signals:
            return {
                'trend': '持有',
                'action': '持有',
                'confidence': '中',
                'reason': '未触发离场信号，建议继续持有',
                'risk_warning': '市场有风险，投资需谨慎',
                'signals': []
            }

        # 找优先级最高的操作
        action_priority = {
            '全部离场': 3,
            '减仓50%': 2,
            '减仓30-50%': 1
        }

        max_priority = 0
        reasons = []
        for signal in signals:
            priority = action_priority.get(signal.action.value, 0)
            if priority > max_priority:
                max_priority = priority
            reasons.append(f"{signal.rule_name}: {signal.reason}")

        # 确定操作
        if max_priority == 3:
            action = '全部离场'
        elif max_priority == 2:
            action = '减仓50%'
        elif max_priority == 1:
            action = '减仓30-50%'
        else:
            action = '持有'

        return {
            'trend': '下降' if '跌破' in str(reasons) else '震荡',
            'action': action,
            'confidence': '中',
            'reason': '; '.join(reasons),
            'risk_warning': '基于离场纪律规则分析，仅供参考',
            'signals': [s.to_dict() for s in signals]
        }


if __name__ == '__main__':
    # 测试代码
    analyzer = BigModelAnalyzer(api_key="8ece9829598a4facafabd8cb47748fc7.FdfZoGatoevxrSwp")

    # 模拟数据
    target = {
        'code': '159995',
        'name': '华夏国证半导体芯片ETF',
        'type': 'ETF'
    }

    realtime_data = {
        'price': 3.0,
        'change_pct': -1.5,
        'open': 3.05,
        'high': 3.1,
        'low': 2.95
    }

    historical_data = [
        {'close': 3.05},
        {'close': 3.08},
        {'close': 3.02},
        {'close': 3.10},
        {'close': 3.15}
    ]

    print("BigModel分析器已就绪")
    print("请在config.json中配置有效的API Key")
