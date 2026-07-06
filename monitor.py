#!/usr/bin/env python3
"""
主监控脚本
整合数据获取、规则分析和推送通知功能
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List

# 导入自定义模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_fetcher import DataFetcher
from exit_rules import ExitRuleAnalyzer
from notifier import PushPlusNotifier
from bigmodel_analysis import BigModelAnalyzer


class FundMonitor:
    """基金/ETF监控系统"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化监控系统

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.fetcher = DataFetcher()
        self.analyzer = ExitRuleAnalyzer()
        self.notifier = None
        self.ai_analyzer = None

        # 初始化推送器
        if self.config.get('pushplus', {}).get('token'):
            token = self.config['pushplus']['token']
            topic = self.config['pushplus'].get('topic', '')
            self.notifier = PushPlusNotifier(token, topic)

        # 初始化AI分析器（优先从环境变量读取API Key）
        bigmodel_config = self.config.get('bigmodel', {})
        api_key = None

        # 优先从环境变量读取
        env_key = os.environ.get('BIGMODEL_API_KEY')
        if env_key:
            api_key = env_key
            print("✓ 从环境变量读取BigModel API Key")
        # 其次从配置文件读取
        elif bigmodel_config.get('api_key') and bigmodel_config['api_key'] != 'YOUR_BIGMODEL_API_KEY':
            api_key = bigmodel_config['api_key']
            print("⚠️ 从配置文件读取BigModel API Key（建议使用环境变量）")

        if api_key:
            self.ai_analyzer = BigModelAnalyzer(
                api_key=api_key,
                model=bigmodel_config.get('model', 'glm-4-flash'),
                base_url=bigmodel_config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
            )
            print("✓ AI分析器已启用")
        else:
            print("ℹ️ BigModel API Key未配置，将使用备用分析")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ 配置文件加载成功: {config_path}")
            return config
        except FileNotFoundError:
            print(f"✗ 配置文件不存在: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"✗ 配置文件格式错误: {e}")
            return {}

    def monitor_target(self, target: Dict) -> Dict:
        """
        监控单个标的

        Args:
            target: 标的信息

        Returns:
            监控结果
        """
        code = target['code']
        target_type = target['type']

        print(f"\n{'='*60}")
        print(f"监控: {target['name']} ({code})")
        print(f"{'='*60}")

        result = {
            'target': target,
            'realtime_data': {},
            'historical_data': [],
            'signals': [],
            'analysis': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # 获取实时数据（ETF和股票都用同一个接口）
            realtime_data = self.fetcher.get_etf_realtime(code)

            if not realtime_data:
                print(f"✗ 获取实时数据失败")
                return result

            result['realtime_data'] = realtime_data
            print(f"✓ 实时数据: 价格={realtime_data.get('price', realtime_data.get('nav', 0)):.4f}")

            # 获取历史数据（ETF和股票都获取）
            historical_data = self.fetcher.get_historical_data(
                code, days=10, is_etf=True
            )

            if not historical_data:
                print(f"✗ 获取历史数据失败")
                return result

            result['historical_data'] = historical_data

            # 计算MA5
            ma5 = self.fetcher.calculate_ma5(historical_data)
            if ma5:
                print(f"✓ MA5: {ma5:.4f}")

            # 计算平均成交量
            avg_volume = self.fetcher.calculate_avg_volume(historical_data)
            if avg_volume:
                print(f"✓ 5日均量: {avg_volume:.2f}亿元")
                realtime_data['avg_volume'] = avg_volume

            # 分析离场信号（普通规则）
            signals = self.analyzer.analyze(target, realtime_data, historical_data)
            result['signals'] = [s.to_dict() for s in signals]

            if signals:
                print(f"⚠️ 触发 {len(signals)} 个离场信号:")
                for signal in signals:
                    print(f"   - {signal.rule_name}: {signal.action.value}")
                    print(f"     理由: {signal.reason}")

            # 只有触发离场信号时才调用AI分析
            if signals and self.ai_analyzer:
                print("🤖 触发离场信号，启动AI深度分析...")
                analysis = self.ai_analyzer.analyze_exit_signal(
                    target, realtime_data, historical_data, signals
                )
                print(f"✓ AI分析完成: {analysis.get('action')}")
                print(f"✓ 趋势判断: {analysis.get('trend')}")
                print(f"✓ 分析理由: {analysis.get('reason', '')[:100]}...")
            else:
                # 未触发信号，使用简单分析
                if signals:
                    # 有信号但无AI，使用备用分析
                    analysis = self._fallback_analyze(signals, target, realtime_data)
                else:
                    # 无信号，直接持有
                    analysis = {
                        'action': '持有',
                        'trend': '持有' if realtime_data.get('price', 0) > realtime_data.get('prev_close', 0) else '震荡',
                        'confidence': '高',
                        'reason': '未触发离场信号，继续持有',
                        'signals': []
                    }

            result['analysis'] = analysis

            print(f"✓ 建议操作: {analysis.get('action', '持有')}")

        except Exception as e:
            print(f"✗ 监控异常: {e}")
            result['error'] = str(e)

        return result

    def run(self, send_notification: bool = True) -> List[Dict]:
        """
        运行监控

        Args:
            send_notification: 是否发送推送通知

        Returns:
            所有标的的监控结果
        """
        print(f"\n{'='*60}")
        print(f"开始监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        targets = self.config.get('targets', [])

        if not targets:
            print("✗ 未配置监控标的")
            return []

        results = []

        for target in targets:
            result = self.monitor_target(target)
            results.append(result)

            # 如果触发离场信号，立即推送
            if send_notification and self.notifier:
                analysis = result.get('analysis', {})
                if analysis.get('action') != '持有':
                    print("📱 准备发送离场信号通知...")
                    self.notifier.send_exit_signal(
                        target,
                        analysis,
                        result.get('realtime_data', {})
                    )

        # 每次都发送汇总报告
        if send_notification and self.notifier:
            self.notifier.send_summary(results)

        print(f"\n{'='*60}")
        print(f"监控完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        return results

    def test_pushplus(self) -> bool:
        """测试PushPlus推送"""
        if not self.notifier:
            print("✗ 未配置PushPlus Token")
            return False

        print("发送测试推送...")
        return self.notifier.send_test()

    def _fallback_analyze(self, signals: List, target: Dict,
                         realtime_data: Dict) -> Dict:
        """备用分析方法（不使用AI）"""
        if not signals:
            return {
                'action': '持有',
                'trend': '持有',
                'confidence': '中',
                'reason': '未触发离场信号，继续持有'
            }

        # 找优先级最高的操作
        action_priority = {
            '全部离场': 3,
            '减仓50%': 2,
            '减仓30-50%': 1
        }

        max_priority = 0
        recommended_action = '持有'
        reasons = []

        for signal in signals:
            priority = action_priority.get(signal.action.value, 0)
            if priority > max_priority:
                max_priority = priority
                recommended_action = signal.action.value
            reasons.append(signal.reason)

        return {
            'action': recommended_action,
            'trend': '下降' if any('跌破' in r for r in reasons) else '震荡',
            'confidence': '中',
            'reason': '; '.join(reasons),
            'signals': [s.to_dict() for s in signals]
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='基金/ETF监控系统')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--no-notify', action='store_true', help='不发送推送通知')
    parser.add_argument('--test-push', action='store_true', help='测试推送功能')

    args = parser.parse_args()

    # 检查配置文件
    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        print("\n请先创建配置文件，参考 config.json")
        return

    # 创建监控系统
    monitor = FundMonitor(args.config)

    # 测试推送
    if args.test_push:
        monitor.test_pushplus()
        return

    # 运行监控
    monitor.run(send_notification=not args.no_notify)


if __name__ == '__main__':
    main()
