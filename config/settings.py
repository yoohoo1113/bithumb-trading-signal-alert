# config/settings.py - 동적 설정 로드 기능 추가

import os
import json
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class Settings:
    """🔥 맥북 발열 방지 + 동적 설정 로드"""
    
    def __init__(self):
        # 디스코드 웹훅 설정
        self.DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
        
        # 빗썸 공식 API 설정
        self.BITHUMB_BASE_URL = "https://api.bithumb.com"
        
        # 동적 설정 로드
        self._load_dynamic_config()
    
    def _load_dynamic_config(self):
        """signal_config.json에서 동적 설정 로드"""
        config_file = "signal_config.json"
        
        # 기본값 설정
        default_config = {
            "rsi_threshold": 45,
            "ma_periods": [9, 25, 99, 200],
            "require_ma_breakout": True,
            "require_price_above_ma25": True,
            "require_macd_golden_cross": True,
            "scan_interval": 600,  # 10분
            "top_coins_count": 200
        }
        
        # 설정 파일에서 로드
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 기본값에 사용자 설정 덮어쓰기
                    default_config.update(user_config)
                    print(f"✅ 사용자 설정 로드 완료: 스캔 간격 {default_config['scan_interval']//60}분")
            except Exception as e:
                print(f"⚠️ 설정 파일 로드 실패, 기본값 사용: {e}")
        else:
            print("📝 설정 파일이 없어 기본값을 사용합니다.")
        
        # 설정값 적용
        self.RSI_THRESHOLD = default_config["rsi_threshold"]
        self.TOP_COINS_COUNT = default_config["top_coins_count"]
        self.SCAN_INTERVAL = default_config["scan_interval"]  # 핵심: 동적 스캔 간격
        self.MA_PERIODS = default_config["ma_periods"]
        self.REQUIRE_MA_BREAKOUT = default_config["require_ma_breakout"]
        self.REQUIRE_PRICE_ABOVE_MA25 = default_config["require_price_above_ma25"]
        self.REQUIRE_MACD_GOLDEN_CROSS = default_config["require_macd_golden_cross"]
        
        # 🔥 발열 방지 최적화 설정
        self.CANDLE_COUNT = 200   # 200개 1시간봉 데이터
        
        # 기술적 지표 설정
        self.RSI_PERIOD = 14
        self.MACD_FAST = 12
        self.MACD_SLOW = 26
        self.MACD_SIGNAL = 9
    
    def reload_config(self):
        """설정 다시 로드 (런타임 중 설정 변경 시 사용)"""
        print("🔄 설정을 다시 로드합니다...")
        self._load_dynamic_config()
        return True
    
    def get_current_config(self):
        """현재 설정값 반환"""
        return {
            "rsi_threshold": self.RSI_THRESHOLD,
            "scan_interval_minutes": self.SCAN_INTERVAL // 60,
            "top_coins_count": self.TOP_COINS_COUNT,
            "ma_periods": self.MA_PERIODS,
            "require_ma_breakout": self.REQUIRE_MA_BREAKOUT,
            "require_price_above_ma25": self.REQUIRE_PRICE_ABOVE_MA25,
            "require_macd_golden_cross": self.REQUIRE_MACD_GOLDEN_CROSS
        }

# 전역 설정 인스턴스
settings = Settings()