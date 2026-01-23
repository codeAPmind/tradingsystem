# daily_signal_alibaba.py
"""
阿里巴巴港股每日交易信号生成器
基于布林带+RSI策略

最优参数:
- 布林带周期: 15
- 布林带倍数: 2.0
- RSI周期: 10
- RSI超买: 75
- RSI超卖: 35
- 策略模式: 下轨反弹 (use_midband=False)

策略逻辑:
买入信号: 价格接近下轨 + RSI < 35 (超卖)
卖出信号: 价格接近上轨 + RSI > 75 (超买)
"""
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from futu import *


class AlibabaDailySignal:
    """阿里巴巴每日信号生成器"""
    
    def __init__(self):
        # 股票信息
        self.stock_code = 'HK.09988'
        self.stock_name = '阿里巴巴'
        
        # 策略参数（最优参数）
        self.bb_period = 15
        self.bb_devfactor = 2.0
        self.rsi_period = 10
        self.rsi_oversold = 35
        self.rsi_overbought = 75
        self.use_midband = False  # 使用下轨反弹策略
        self.bb_touch_pct = 0.01  # 接近布林带的阈值 1%
        
        # Futu连接
        self.quote_ctx = None
    
    def connect(self):
        """连接Futu OpenD"""
        try:
            self.quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
            
            # 订阅
            ret, data = self.quote_ctx.subscribe(
                [self.stock_code], 
                [SubType.QUOTE]
            )
            
            if ret != RET_OK:
                print(f"订阅失败: {data}")
                return False
            
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
    
    def get_historical_data(self, days=60):
        """
        获取历史数据
        需要至少 BB周期 + RSI周期 的数据来计算指标
        """
        try:
            end = datetime.now()
            start = end - timedelta(days=days)
            
            ret, df, _ = self.quote_ctx.request_history_kline(
                code=self.stock_code,
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                ktype=KLType.K_DAY,
                autype=AuType.NONE,
                max_count=1000
            )
            
            if ret != RET_OK:
                print(f"获取历史数据失败: {df}")
                return None
            
            return df
            
        except Exception as e:
            print(f"获取数据错误: {e}")
            return None
    
    def calculate_bollinger_bands(self, data):
        """
        计算布林带
        
        参数:
            data: DataFrame，包含 close 列
        
        返回:
            upper, middle, lower
        """
        close = data['close'].values
        
        # 计算中轨（移动平均）
        middle = pd.Series(close).rolling(window=self.bb_period).mean()
        
        # 计算标准差
        std = pd.Series(close).rolling(window=self.bb_period).std()
        
        # 计算上下轨
        upper = middle + (std * self.bb_devfactor)
        lower = middle - (std * self.bb_devfactor)
        
        return upper, middle, lower
    
    def calculate_rsi(self, data):
        """
        计算RSI
        
        参数:
            data: DataFrame，包含 close 列
        
        返回:
            RSI序列
        """
        close = data['close'].values
        
        # 计算价格变化
        delta = pd.Series(close).diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self):
        """
        生成今日交易信号
        
        返回:
            signal: 'BUY', 'SELL', 'HOLD', 'NO_DATA'
            reason: 信号原因
            details: 详细信息字典
        """
        # 获取历史数据
        data = self.get_historical_data(days=60)
        
        if data is None or len(data) < max(self.bb_period, self.rsi_period) + 5:
            return 'NO_DATA', '数据不足', {}
        
        # 计算指标
        bb_upper, bb_mid, bb_lower = self.calculate_bollinger_bands(data)
        rsi = self.calculate_rsi(data)
        
        # 获取最新数据
        latest_idx = len(data) - 1
        current_price = data['close'].iloc[latest_idx]
        current_bb_upper = bb_upper.iloc[latest_idx]
        current_bb_mid = bb_mid.iloc[latest_idx]
        current_bb_lower = bb_lower.iloc[latest_idx]
        current_rsi = rsi.iloc[latest_idx]
        
        # 检查数据有效性
        if pd.isna(current_bb_upper) or pd.isna(current_rsi):
            return 'NO_DATA', '指标计算失败', {}
        
        # 计算距离布林带的百分比
        band_width = current_bb_upper - current_bb_lower
        
        if band_width > 0:
            dist_to_upper = (current_bb_upper - current_price) / band_width
            dist_to_lower = (current_price - current_bb_lower) / band_width
        else:
            dist_to_upper = 1.0
            dist_to_lower = 1.0
        
        # 详细信息
        details = {
            'date': data['time_key'].iloc[latest_idx],
            'price': current_price,
            'bb_upper': current_bb_upper,
            'bb_mid': current_bb_mid,
            'bb_lower': current_bb_lower,
            'rsi': current_rsi,
            'dist_to_upper_pct': dist_to_upper * 100,
            'dist_to_lower_pct': dist_to_lower * 100,
            'band_width': band_width
        }
        
        # 生成信号（使用下轨反弹策略）
        signal = 'HOLD'
        reason = '观望，等待信号'
        
        # 买入信号：价格接近下轨 + RSI超卖
        if dist_to_lower < self.bb_touch_pct:
            if current_rsi < self.rsi_oversold:
                signal = 'BUY'
                reason = f'价格触及下轨 (距离{dist_to_lower*100:.1f}%) + RSI超卖 ({current_rsi:.1f})'
            else:
                signal = 'HOLD'
                reason = f'价格接近下轨但RSI未超卖 (RSI={current_rsi:.1f})'
        
        # 卖出信号：价格接近上轨 + RSI超买
        elif dist_to_upper < self.bb_touch_pct:
            if current_rsi > self.rsi_overbought:
                signal = 'SELL'
                reason = f'价格触及上轨 (距离{dist_to_upper*100:.1f}%) + RSI超买 ({current_rsi:.1f})'
            else:
                signal = 'HOLD'
                reason = f'价格接近上轨但RSI未超买 (RSI={current_rsi:.1f})'
        
        # 其他情况
        else:
            # 检查是否在极端RSI区域
            if current_rsi < self.rsi_oversold:
                signal = 'HOLD'
                reason = f'RSI超卖 ({current_rsi:.1f}) 但价格未到下轨，等待更好位置'
            elif current_rsi > self.rsi_overbought:
                signal = 'HOLD'
                reason = f'RSI超买 ({current_rsi:.1f}) 但价格未到上轨，等待更好位置'
            else:
                signal = 'HOLD'
                reason = f'价格在布林带中间，RSI中性 ({current_rsi:.1f})'
        
        return signal, reason, details
    
    def print_signal_report(self, signal, reason, details):
        """打印信号报告"""
        
        print("\n" + "="*70)
        print(f"{self.stock_name} ({self.stock_code}) - 每日交易信号")
        print("="*70)
        
        # 当前时间
        print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 策略参数
        print(f"\n策略参数:")
        print(f"  布林带周期: {self.bb_period}")
        print(f"  布林带倍数: {self.bb_devfactor}")
        print(f"  RSI周期: {self.rsi_period}")
        print(f"  RSI超卖线: {self.rsi_oversold}")
        print(f"  RSI超买线: {self.rsi_overbought}")
        print(f"  策略模式: {'中轨突破' if self.use_midband else '下轨反弹'}")
        
        # 当前市场数据
        print(f"\n当前市场数据:")
        print(f"  日期: {details.get('date', 'N/A')}")
        print(f"  收盘价: {details.get('price', 0):.2f} HKD")
        
        # 布林带
        print(f"\n布林带:")
        print(f"  上轨: {details.get('bb_upper', 0):.2f} HKD")
        print(f"  中轨: {details.get('bb_mid', 0):.2f} HKD")
        print(f"  下轨: {details.get('bb_lower', 0):.2f} HKD")
        print(f"  带宽: {details.get('band_width', 0):.2f} HKD")
        
        # 价格位置
        dist_upper = details.get('dist_to_upper_pct', 0)
        dist_lower = details.get('dist_to_lower_pct', 0)
        
        print(f"\n价格位置:")
        print(f"  距离上轨: {dist_upper:.1f}%")
        print(f"  距离下轨: {dist_lower:.1f}%")
        
        # 价格位置可视化
        bb_position = self._get_bb_position_visual(
            details.get('price', 0),
            details.get('bb_upper', 0),
            details.get('bb_mid', 0),
            details.get('bb_lower', 0)
        )
        print(f"  位置示意: {bb_position}")
        
        # RSI
        current_rsi = details.get('rsi', 0)
        print(f"\nRSI指标:")
        print(f"  当前RSI: {current_rsi:.1f}")
        print(f"  超买线: {self.rsi_overbought}")
        print(f"  超卖线: {self.rsi_oversold}")
        
        # RSI状态
        if current_rsi > self.rsi_overbought:
            rsi_status = "超买 ⚠️"
        elif current_rsi < self.rsi_oversold:
            rsi_status = "超卖 ⚠️"
        else:
            rsi_status = "中性"
        print(f"  状态: {rsi_status}")
        
        # RSI可视化
        rsi_visual = self._get_rsi_visual(current_rsi)
        print(f"  RSI示意: {rsi_visual}")
        
        # 交易信号
        print(f"\n" + "="*70)
        print(f"交易信号: {self._format_signal(signal)}")
        print(f"信号原因: {reason}")
        print("="*70)
        
        # 建议
        print(f"\n操作建议:")
        if signal == 'BUY':
            print("  ✅ 建议买入")
            print(f"  → 价格接近下轨，RSI超卖，可能反弹")
            print(f"  → 建议分批买入，控制仓位")
            print(f"  → 止损位: {details.get('bb_lower', 0) * 0.98:.2f} HKD (下轨下方2%)")
        elif signal == 'SELL':
            print("  ⚠️ 建议卖出")
            print(f"  → 价格接近上轨，RSI超买，可能回落")
            print(f"  → 建议分批卖出，保留部分仓位")
            print(f"  → 止盈位: 当前价格 {details.get('price', 0):.2f} HKD")
        else:
            print("  ⏸️ 建议观望")
            print(f"  → 等待更好的买卖时机")
            print(f"  → 密切关注价格和RSI变化")
        
        # 风险提示
        print(f"\n风险提示:")
        print("  ⚠️ 本信号仅供参考，不构成投资建议")
        print("  ⚠️ 请结合基本面和市场环境综合判断")
        print("  ⚠️ 注意控制仓位，设置止损")
        print("  ⚠️ 阿里巴巴受政策影响较大，注意政策风险")
        
        print("\n" + "="*70 + "\n")
    
    def _format_signal(self, signal):
        """格式化信号显示"""
        if signal == 'BUY':
            return "🟢 买入 (BUY)"
        elif signal == 'SELL':
            return "🔴 卖出 (SELL)"
        elif signal == 'HOLD':
            return "🟡 观望 (HOLD)"
        else:
            return "⚪ 无数据 (NO_DATA)"
    
    def _get_bb_position_visual(self, price, upper, mid, lower):
        """
        生成布林带位置可视化
        """
        if pd.isna(upper) or pd.isna(lower) or upper == lower:
            return "N/A"
        
        # 计算价格在布林带中的相对位置 (0-1)
        position = (price - lower) / (upper - lower)
        position = max(0, min(1, position))  # 限制在0-1之间
        
        # 生成可视化字符串
        bar_length = 30
        pos_index = int(position * bar_length)
        
        bar = "["
        for i in range(bar_length):
            if i == pos_index:
                bar += "●"
            elif i == 0:
                bar += "↓"  # 下轨
            elif i == bar_length - 1:
                bar += "↑"  # 上轨
            elif i == bar_length // 2:
                bar += "─"  # 中轨
            else:
                bar += "─"
        bar += "]"
        
        return bar
    
    def _get_rsi_visual(self, rsi):
        """
        生成RSI可视化
        """
        if pd.isna(rsi):
            return "N/A"
        
        rsi = max(0, min(100, rsi))  # 限制在0-100
        
        bar_length = 30
        rsi_index = int(rsi / 100 * bar_length)
        oversold_index = int(self.rsi_oversold / 100 * bar_length)
        overbought_index = int(self.rsi_overbought / 100 * bar_length)
        
        bar = "["
        for i in range(bar_length):
            if i == rsi_index:
                bar += "●"
            elif i == oversold_index:
                bar += "↓"  # 超卖线
            elif i == overbought_index:
                bar += "↑"  # 超买线
            else:
                bar += "─"
        bar += "]"
        
        return f"{bar} ({rsi:.1f})"
    
    def save_to_file(self, signal, reason, details):
        """保存信号到文件"""
        try:
            filename = f"alibaba_signal_{datetime.now().strftime('%Y%m%d')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write(f"{self.stock_name} ({self.stock_code}) - 每日交易信号\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("策略参数:\n")
                f.write(f"  布林带周期: {self.bb_period}\n")
                f.write(f"  布林带倍数: {self.bb_devfactor}\n")
                f.write(f"  RSI周期: {self.rsi_period}\n")
                f.write(f"  RSI超卖线: {self.rsi_oversold}\n")
                f.write(f"  RSI超买线: {self.rsi_overbought}\n\n")
                
                f.write("当前市场数据:\n")
                f.write(f"  日期: {details.get('date', 'N/A')}\n")
                f.write(f"  收盘价: {details.get('price', 0):.2f} HKD\n")
                f.write(f"  布林带上轨: {details.get('bb_upper', 0):.2f} HKD\n")
                f.write(f"  布林带中轨: {details.get('bb_mid', 0):.2f} HKD\n")
                f.write(f"  布林带下轨: {details.get('bb_lower', 0):.2f} HKD\n")
                f.write(f"  RSI: {details.get('rsi', 0):.1f}\n\n")
                
                f.write("="*70 + "\n")
                f.write(f"交易信号: {signal}\n")
                f.write(f"信号原因: {reason}\n")
                f.write("="*70 + "\n")
            
            print(f"信号已保存到: {filename}")
            
        except Exception as e:
            print(f"保存文件失败: {e}")


def main():
    """主函数"""
    print("\n阿里巴巴港股每日交易信号生成器")
    print("="*70)
    
    # 创建信号生成器
    signal_gen = AlibabaDailySignal()
    
    # 连接Futu
    print("\n正在连接 Futu OpenD...")
    if not signal_gen.connect():
        print("❌ 连接失败，请检查：")
        print("  1. Futu OpenD 是否已启动")
        print("  2. 是否有港股行情权限")
        print("  3. 网络连接是否正常")
        return
    
    print("✅ 连接成功")
    
    try:
        # 生成信号
        print("\n正在分析市场数据...")
        signal, reason, details = signal_gen.generate_signal()
        
        if signal == 'NO_DATA':
            print(f"\n❌ {reason}")
            print("请检查数据获取是否正常")
            return
        
        # 打印报告
        signal_gen.print_signal_report(signal, reason, details)
        
        # 保存到文件
        signal_gen.save_to_file(signal, reason, details)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 断开连接
        signal_gen.disconnect()
        print("连接已关闭")


if __name__ == '__main__':
    main()