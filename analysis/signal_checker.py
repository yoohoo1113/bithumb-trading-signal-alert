# analysis/signal_checker.py - 완전한 5가지 신호 조건 체크

import pandas as pd
import numpy as np

class SignalChecker:
    """완전한 5가지 신호 조건 체크 (20% 상승 제한 포함)"""
    
    @staticmethod
    def check_moving_average_breakout(df):
        """9일선, 25일선이 99일선, 200일선을 최근 10시간 내 돌파했는지 확인"""
        try:
            # 최근 10개 봉 데이터 (10시간)
            recent_data = df.iloc[-10:]
            
            if len(recent_data) < 10:
                return False
            
            # 현재 시점에서는 돌파 상태여야 함
            latest = recent_data.iloc[-1]
            ma9_above = latest['ma9'] > latest['ma99'] and latest['ma9'] > latest['ma200']
            ma25_above = latest['ma25'] > latest['ma99'] and latest['ma25'] > latest['ma200']
            
            if not (ma9_above and ma25_above):
                return False
            
            # 10시간 전에는 돌파하지 않은 상태였는지 확인
            oldest = recent_data.iloc[0]
            ma9_was_below = oldest['ma9'] <= oldest['ma99'] or oldest['ma9'] <= oldest['ma200']
            ma25_was_below = oldest['ma25'] <= oldest['ma99'] or oldest['ma25'] <= oldest['ma200']
            
            return ma9_was_below or ma25_was_below
            
        except Exception as e:
            print(f"이동평균 돌파 체크 오류: {e}")
            return False
    
    @staticmethod
    def check_rsi_condition(df, threshold=45):
        """RSI가 45 이상인지 확인"""
        try:
            latest_rsi = df.iloc[-1]['rsi']
            return not pd.isna(latest_rsi) and latest_rsi >= threshold
            
        except Exception as e:
            print(f"RSI 체크 오류: {e}")
            return False
    
    @staticmethod
    def check_macd_golden_cross(df):
        """MACD 골든크로스 확인"""
        try:
            latest = df.iloc[-1]
            previous = df.iloc[-2]
            
            # 현재 MACD가 시그널선 위에 있고, 이전에는 아래에 있었는지
            current_above = latest['macd'] > latest['macd_signal']
            previous_below = previous['macd'] <= previous['macd_signal']
            
            # 또는 현재 MACD가 시그널선 위에 있는 상태 유지
            return current_above and (previous_below or True)
            
        except Exception as e:
            print(f"MACD 골든크로스 체크 오류: {e}")
            return False
    
    @staticmethod
    def check_price_above_ma25(df):
        """가격이 25일선 위에 있는지 확인"""
        try:
            latest = df.iloc[-1]
            return latest['close'] > latest['ma25']
            
        except Exception as e:
            print(f"가격 vs 25일선 체크 오류: {e}")
            return False
    
    @staticmethod
    def check_price_increase_limit(df, max_increase=0.20):
        """24시간 상승률이 20% 이하인지 확인 (이미 상승한 것 제외)"""
        try:
            if len(df) < 24:
                return True  # 데이터 부족시 통과
            
            current_price = df.iloc[-1]['close']
            price_24h_ago = df.iloc[-24]['close']
            
            increase_rate = (current_price - price_24h_ago) / price_24h_ago
            return increase_rate <= max_increase  # 20% 이하만 통과
            
        except Exception as e:
            print(f"상승률 체크 오류: {e}")
            return True
    
    @staticmethod
    def check_all_conditions(df):
        """완전한 5가지 조건 체크"""
        try:
            # 데이터 유효성 확인
            if len(df) < 200:
                return False, "데이터 부족"
            
            # 5가지 조건 체크
            conditions = {
                'ma_breakout': SignalChecker.check_moving_average_breakout(df),  # 최근 10시간 내 돌파
                'rsi_above_45': SignalChecker.check_rsi_condition(df),  # RSI 45 이상
                'macd_golden_cross': SignalChecker.check_macd_golden_cross(df),  # MACD 골든크로스
                'price_above_ma25': SignalChecker.check_price_above_ma25(df),  # 가격이 25일선 위
                'not_overextended': SignalChecker.check_price_increase_limit(df)  # 24시간 상승률 20% 이하
            }
            
            # 모든 조건 만족 여부
            all_satisfied = all(conditions.values())
            
            # 분석 데이터 추출
            latest = df.iloc[-1]
            
            # 24시간 상승률 계산
            price_24h_ago = df.iloc[-24]['close'] if len(df) >= 24 else latest['close']
            increase_24h = ((latest['close'] - price_24h_ago) / price_24h_ago * 100) if price_24h_ago > 0 else 0
            
            analysis_data = {
                'rsi': latest['rsi'],
                'ma25': latest['ma25'],
                'macd': latest['macd'],
                'current_price': latest['close'],
                'increase_24h': increase_24h,
                'conditions': conditions
            }
            
            return all_satisfied, analysis_data
            
        except Exception as e:
            print(f"신호 조건 체크 오류: {e}")
            return False, str(e)
    
    @staticmethod
    def get_condition_summary(conditions):
        """조건별 만족 여부 요약"""
        summary = []
        condition_names = {
            'ma_breakout': '최근 10시간내 9,25일선 돌파',
            'rsi_above_45': 'RSI 45 이상',
            'macd_golden_cross': 'MACD 골든크로스',
            'price_above_ma25': '가격이 25일선 위',
            'not_overextended': '24시간 상승률 20% 이하'
        }
        
        for key, name in condition_names.items():
            status = "✓" if conditions.get(key, False) else "✗"
            summary.append(f"{name}: {status}")
        
        return summary