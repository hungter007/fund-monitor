#!/usr/bin/env python3
"""
离场规则分析模块
实现四大离场纪律规则的判断逻辑
"""

from typing import Dict, List, Optional
from enum import Enum


class ExitAction(Enum):
    """离场操作类型"""
    HOLD = "持有"
    REDUCE_50 = "减仓50%"
    SELL_ALL = "全部离场"
    REDUCE_30_50 = "减仓30-50%"


class ExitSignal:
    """离场信号"""

    def __init__(self, triggered: bool, rule_name: str, action: ExitAction,
                 reason: str, current_value: float, threshold: float):
        self.triggered = triggered
        self.rule_name = rule_name
        self.action = action
        self.reason = reason
        self.current_value = current_value
        self.threshold = threshold

    def to_dict(self) -> Dict:
        return {
            'triggered': self.triggered,
            'rule_name': self.rule_name,
            'action': self.action.value,
            'reason': self.reason,
            'current_value': self.current_value,
            'threshold': self.threshold
        }


class ExitRuleAnalyzer:
    """离场规则分析器"""

    def __init__(self):
        self.rules = {
            'ma5_break': self._check_ma5_break,
            'volume_break': self._check_volume_break,
            'doji_top': self._check_doji_top
        }

    def analyze(self, target: Dict, realtime_data: Dict,
                historical_data: List[Dict]) -> List[ExitSignal]:
        """
        分析离场信号

        Args:
            target: 标的信息
            realtime_data: 实时数据
            historical_data: 历史数据

        Returns:
            触发的离场信号列表
        """
        signals = []

        for rule_name, rule_func in self.rules.items():
            signal = rule_func(target, realtime_data, historical_data)
            if signal:
                signals.append(signal)

        return signals

    def _check_ma5_break(self, target: Dict, realtime_data: Dict,
                        historical_data: List[Dict]) -> Optional[ExitSignal]:
        """
        规则一：缩量破趋势线出一半

        判断条件：
        - 价格跌破5日均线
        - 成交量未异常放大
        """
        try:
            # 获取当前价格
            if target['type'] == 'ETF':
                current_price = realtime_data.get('price', 0)
            else:
                current_price = realtime_data.get('nav', 0)

            if not current_price:
                return None

            # 计算MA5
            if len(historical_data) < 5:
                return None

            if 'nav' in historical_data[0]:
                # 基金净值
                values = [item['nav'] for item in historical_data[:5]]
            else:
                # ETF收盘价
                values = [item['close'] for item in historical_data[:5]]

            ma5 = sum(values) / 5

            # 检查是否跌破
            if current_price < ma5:
                break_pct = ((ma5 - current_price) / ma5) * 100

                return ExitSignal(
                    triggered=True,
                    rule_name="缩量破趋势线",
                    action=ExitAction.REDUCE_50,
                    reason=f"价格 {current_price:.4f} 跌破5日均线 {ma5:.4f}，跌幅 {break_pct:.2f}%",
                    current_value=current_price,
                    threshold=ma5
                )

        except Exception as e:
            print(f"检查MA5破位失败: {e}")

        return None

    def _check_volume_break(self, target: Dict, realtime_data: Dict,
                          historical_data: List[Dict]) -> Optional[ExitSignal]:
        """
        规则三：放量破趋势线全部离场

        判断条件：
        - 价格跌破5日均线
        - 成交量异常放大（>=前5日均量的130%）
        """
        try:
            # 只对ETF有效
            if target['type'] != 'ETF':
                return None

            current_price = realtime_data.get('price', 0)
            current_amount = realtime_data.get('amount', 0)

            if not current_price or not current_amount:
                return None

            # 计算MA5
            if len(historical_data) < 5:
                return None

            values = [item['close'] for item in historical_data[:5]]
            ma5 = sum(values) / 5

            # 计算前5日平均成交额
            amounts = [item.get('amount', 0) for item in historical_data[:5]]
            avg_amount = sum(amounts) / len(amounts)

            # 检查是否同时满足两个条件
            if current_price < ma5 and current_amount >= avg_amount * 1.3:
                return ExitSignal(
                    triggered=True,
                    rule_name="放量破趋势线",
                    action=ExitAction.SELL_ALL,
                    reason=f"价格跌破MA5且放量，成交额 {current_amount:.2f}亿 >= 均量 {avg_amount:.2f}亿",
                    current_value=current_price,
                    threshold=ma5
                )

        except Exception as e:
            print(f"检查放量破位失败: {e}")

        return None

    def _check_doji_top(self, target: Dict, realtime_data: Dict,
                       historical_data: List[Dict]) -> Optional[ExitSignal]:
        """
        规则四：K线形态滞涨离场

        判断条件：
        - 连续大涨后出现长上影线、长下影线、纺锤线等形态
        """
        try:
            if target['type'] != 'ETF':
                return None

            current_price = realtime_data.get('price', 0)
            open_price = realtime_data.get('open', 0)
            high_price = realtime_data.get('high', 0)
            low_price = realtime_data.get('low', 0)

            if not all([current_price, open_price, high_price, low_price]):
                return None

            # 计算实体和影线
            body = abs(current_price - open_price)
            upper_shadow = high_price - max(current_price, open_price)
            lower_shadow = min(current_price, open_price) - low_price
            total_range = high_price - low_price

            if total_range == 0:
                return None

            # 检查最近是否连续大涨
            if len(historical_data) < 3:
                return None

            recent_changes = []
            for i in range(min(3, len(historical_data) - 1)):
                if 'close' in historical_data[i] and 'close' in historical_data[i + 1]:
                    change = (historical_data[i]['close'] - historical_data[i + 1]['close']) / historical_data[i + 1]['close']
                    recent_changes.append(change)

            # 连续3天涨幅都超过2%
            if len(recent_changes) < 3 or not all(c > 0.02 for c in recent_changes):
                return None

            # 检查K线形态
            # 纺锤线：实体很小，上下影线都很长
            is_doji = (body / total_range < 0.3 and
                      upper_shadow / total_range > 0.2 and
                      lower_shadow / total_range > 0.2)

            # 长上影线
            is_long_upper = upper_shadow / total_range > 0.4

            # 长下影线
            is_long_lower = lower_shadow / total_range > 0.4

            if is_doji or is_long_upper or is_long_lower:
                pattern_name = "纺锤线" if is_doji else ("长上影线" if is_long_upper else "长下影线")
                return ExitSignal(
                    triggered=True,
                    rule_name="K线形态滞涨",
                    action=ExitAction.REDUCE_30_50,
                    reason=f"连续大涨后出现{pattern_name}形态",
                    current_value=current_price,
                    threshold=0
                )

        except Exception as e:
            print(f"检查K线形态失败: {e}")

        return None


def analyze_with_ai(signals: List[ExitSignal], target: Dict,
                   realtime_data: Dict, api_key: Optional[str] = None) -> Dict:
    """
    使用AI模型分析离场信号（预留接口）

    Args:
        signals: 触发的信号列表
        target: 标的信息
        realtime_data: 实时数据
        api_key: AI API密钥（可选）

    Returns:
        AI分析结果
    """
    # 这里可以集成AI模型进行分析
    # 目前返回基础分析

    if not signals:
        return {
            'action': '持有',
            'confidence': '高',
            'reason': '未触发离场信号，继续持有'
        }

    # 找出优先级最高的操作
    action_priority = {
        ExitAction.SELL_ALL: 3,
        ExitAction.REDUCE_50: 2,
        ExitAction.REDUCE_30_50: 1
    }

    max_priority = 0
    recommended_action = ExitAction.HOLD
    reasons = []

    for signal in signals:
        priority = action_priority.get(signal.action, 0)
        if priority > max_priority:
            max_priority = priority
            recommended_action = signal.action
        reasons.append(signal.reason)

    return {
        'action': recommended_action.value,
        'confidence': '中',
        'reason': '; '.join(reasons),
        'signals': [s.to_dict() for s in signals]
    }


if __name__ == '__main__':
    # 测试代码
    analyzer = ExitRuleAnalyzer()

    # 模拟数据
    target = {
        'code': '159995',
        'type': 'ETF'
    }

    realtime_data = {
        'price': 2.9,
        'amount': 20.5
    }

    historical_data = [
        {'date': '2026-07-02', 'close': 3.0, 'amount': 15},
        {'date': '2026-07-01', 'close': 3.1, 'amount': 12},
        {'date': '2026-06-30', 'close': 3.0, 'amount': 10},
        {'date': '2026-06-29', 'close': 2.9, 'amount': 8},
        {'date': '2026-06-26', 'close': 2.8, 'amount': 9},
    ]

    signals = analyzer.analyze(target, realtime_data, historical_data)
    print(f"触发的信号: {[s.to_dict() for s in signals]}")
