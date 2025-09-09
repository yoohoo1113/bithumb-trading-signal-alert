# analysis/indicators.py - 기술적 지표 계산 (발열 방지)

import pandas as pd
import numpy as np

class TechnicalIndicators:
    """발열 방지 최적화된 기술적 지표 계산"""
    
    @staticmethod
    def moving_average(data, period):
        """단순 이동평균선 계산"""
        return data.rolling(window=period, min_periods=period).mean()
    
    @staticmethod
    def calculate_rsi(data, period=14):
        """RSI 계산"""
        try:
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([np.nan] * len(data))
    
    @staticmethod
    def calculate_macd(data, fast=12, slow=26, signal=9):
        """MACD 계산"""
        try:
            ema_fast = data.ewm(span=fast).mean()
            ema_slow = data.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        except:
            return {
                'macd': pd.Series([np.nan] * len(data)),
                'signal': pd.Series([np.nan] * len(data)),
                'histogram': pd.Series([np.nan] * len(data))
            }
    
    @staticmethod
    def calculate_all_indicators(df):
        """모든 지표를 한번에 계산 (메모리 효율적)"""
        try:
            close_prices = df['close']
            
            # 이동평균선 계산
            df['ma9'] = TechnicalIndicators.moving_average(close_prices, 9)
            df['ma25'] = TechnicalIndicators.moving_average(close_prices, 25)
            df['ma99'] = TechnicalIndicators.moving_average(close_prices, 99)
            df['ma200'] = TechnicalIndicators.moving_average(close_prices, 200)
            
            # RSI 계산
            df['rsi'] = TechnicalIndicators.calculate_rsi(close_prices, 14)
            
            # MACD 계산
            macd_data = TechnicalIndicators.calculate_macd(close_prices)
            df['macd'] = macd_data['macd']
            df['macd_signal'] = macd_data['signal']
            df['macd_histogram'] = macd_data['histogram']
            
            print(f"기술적 지표 계산 완료: {len(df)}개 데이터")
            return df
            
        except Exception as e:
            print(f"지표 계산 오류: {e}")
            return df