# utils/data_processor.py - 데이터 전처리 (발열 방지)

import pandas as pd
from datetime import datetime

class DataProcessor:
    """발열 방지 최적화된 데이터 전처리"""
    
    @staticmethod
    def candles_to_dataframe(candles):
        """빗썸 캔들 데이터를 pandas DataFrame으로 변환"""
        try:
            if not candles:
                return None
            
            # 빗썸 캔들 데이터 구조에 맞게 변환
            df_data = []
            for candle in candles:
                df_data.append({
                    'timestamp': candle['candle_date_time_kst'],
                    'open': float(candle['opening_price']),
                    'high': float(candle['high_price']),
                    'low': float(candle['low_price']),
                    'close': float(candle['trade_price']),
                    'volume': float(candle['candle_acc_trade_volume'])
                })
            
            df = pd.DataFrame(df_data)
            
            # 시간순 정렬 (오래된 것부터)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"데이터 변환 완료: {len(df)}개 캔들")
            return df
            
        except Exception as e:
            print(f"데이터 변환 오류: {e}")
            return None
    
    @staticmethod
    def validate_data(df, min_length=200):
        """데이터 유효성 검사"""
        if df is None or len(df) < min_length:
            return False
        
        # 필수 컬럼 확인
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return False
        
        # 가격 데이터 유효성 확인
        if df[required_cols].isnull().any().any():
            return False
        
        return True