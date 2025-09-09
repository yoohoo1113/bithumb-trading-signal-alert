# main.py - 메인 실행 로직 (거래량 순위 표시 수정)

import time
import gc
import json
import os
from datetime import datetime

from api.bithumb_client import BithumbClient
from api.discord_webhook import DiscordWebhook
from utils.data_processor import DataProcessor
from analysis.indicators import TechnicalIndicators
from analysis.signal_checker import SignalChecker
from config.settings import settings

class TradingSignalBot:
    """발열 방지 최적화된 트레이딩 신호 봇"""
    
    def __init__(self):
        # 지연 초기화 (메모리 최적화)
        self.bithumb_client = None
        self.discord_webhook = None
        self.is_running = False
        self.last_scan_time = 0
        self.config = self.load_signal_config()
    
    def load_signal_config(self):
        """signal_config.json에서 설정 로드"""
        config_file = "signal_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 설정
        return {
            "rsi_threshold": 45,
            "require_ma_breakout": True,
            "require_price_above_ma25": True,
            "require_macd_golden_cross": True,
            "scan_interval": 600,
            "top_coins_count": 200
        }
    
    def _lazy_init_components(self):
        """필요할 때만 컴포넌트 생성"""
        if self.bithumb_client is None:
            self.bithumb_client = BithumbClient()
        if self.discord_webhook is None:
            self.discord_webhook = DiscordWebhook()
    
    def scan_single_coin(self, market_code):
        """단일 코인 스캔 (1차 필터링용)"""
        try:
            # 캔들 데이터 가져오기
            candles = self.bithumb_client.get_candle_data(market_code, 200)
            if not candles:
                return False, None
            
            # 데이터 변환 및 검증
            df = DataProcessor.candles_to_dataframe(candles)
            if not DataProcessor.validate_data(df):
                return False, None
            
            # 기술적 지표 계산
            df = TechnicalIndicators.calculate_all_indicators(df)
            
            # 1차 필터: 가격이 25일선 위인지 체크 (가장 빠른 조건)
            latest = df.iloc[-1]
            if latest['close'] <= latest['ma25']:
                return False, None
            
            # 4가지 조건 모두 체크
            signal_found, analysis = SignalChecker.check_all_conditions(df)
            
            return signal_found, analysis
            
        except Exception as e:
            print(f"{market_code} 스캔 오류: {e}")
            return False, None
    
    def scan_all_coins(self):
        """모든 코인 스캔"""
        start_time = time.time()
        signal_count = 0
        scanned_count = 0
        
        try:
            print(f"\n=== 스캔 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
            
            # 지연 초기화
            self._lazy_init_components()
            
            # 마켓 목록 가져오기
            markets = self.bithumb_client.get_market_list()
            if not markets:
                print("마켓 목록 조회 실패")
                return
            
            # 거래량 상위 코인들 가져오기 (BTC 데이터 포함)
            top_tickers, btc_ticker = self.bithumb_client.get_ticker_data(markets)
            if not top_tickers:
                print("거래량 데이터 조회 실패")
                return
            
            # 상위 N개 코인만 스캔
            target_count = min(self.config['top_coins_count'], len(top_tickers))
            target_tickers = top_tickers[:target_count]
            
            print(f"거래량 상위 {target_count}개 코인 스캔 시작...")
            
            # 각 코인별 신호 체크
            for ticker in target_tickers:
                market_code = ticker['market']
                scanned_count += 1
                
                # 신호 체크
                signal_found, analysis = self.scan_single_coin(market_code)
                
                if signal_found and isinstance(analysis, dict):
                    signal_count += 1
                    print(f"🚀 신호 발견: {market_code}")
                    
                    # 핵심: bithumb_client 인스턴스 전달하여 거래량 순위 표시
                    self.discord_webhook.send_signal_alert(
                        coin_data=ticker, 
                        analysis_data=analysis, 
                        btc_data=btc_ticker,
                        bithumb_client=self.bithumb_client  # 거래량 순위를 위해 필수!
                    )
                
                # 진행률 표시 (매 50개마다)
                if scanned_count % 50 == 0:
                    print(f"진행: {scanned_count}/{target_count} ({scanned_count/target_count*100:.1f}%)")
                
                # API 호출 제한 (발열 방지)
                time.sleep(0.1)
            
            # 스캔 완료
            scan_time = time.time() - start_time
            print(f"\n=== 스캔 완료 ===")
            print(f"스캔 코인: {scanned_count}개")
            print(f"신호 발견: {signal_count}개")
            print(f"소요 시간: {scan_time:.1f}초")
            
            # 메모리 정리 (발열 방지)
            gc.collect()
            
        except Exception as e:
            print(f"스캔 오류: {e}")
    
    def run_once(self):
        """1회 스캔 실행"""
        self.scan_all_coins()
        self.cleanup()
    
    def show_countdown_with_animation(self, total_seconds):
        """카운트다운과 애니메이션 표시"""
        animation_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
        for remaining in range(total_seconds, 0, -1):
            # 시간 포맷팅 (분:초)
            minutes = remaining // 60
            seconds = remaining % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            # 애니메이션 문자 선택
            anim_char = animation_chars[remaining % len(animation_chars)]
            
            # 진행률 바 생성 (30자)
            total_duration = self.config['scan_interval']
            progress = (total_duration - remaining) / total_duration
            filled_length = int(30 * progress)
            bar = '█' * filled_length + '░' * (30 - filled_length)
            
            # 터미널 출력 (같은 줄에 덮어쓰기)
            print(f"\r{anim_char} 다음 스캔까지: {time_str} [{bar}] {progress*100:.1f}%", end='', flush=True)
            
            time.sleep(1)
        
        # 카운트다운 완료 후 줄바꿈
        print()
    
    def run_continuous(self):
        """연속 스캔 실행 (애니메이션 추가)"""
        self.is_running = True
        print(f"🚀 연속 스캔 모드 시작 (간격: {self.config['scan_interval']//60}분)")
        print("Ctrl+C로 중단")
        
        try:
            while self.is_running:
                # 스캔 실행
                self.scan_all_coins()
                self.last_scan_time = time.time()
                
                print(f"\n💤 다음 스캔까지 {self.config['scan_interval']//60}분 대기...")
                
                # 애니메이션과 함께 대기
                try:
                    self.show_countdown_with_animation(self.config['scan_interval'])
                except KeyboardInterrupt:
                    # Ctrl+C 시 즉시 종료
                    raise KeyboardInterrupt
                
        except KeyboardInterrupt:
            print("\n\n🛑 사용자가 중단했습니다.")
            self.is_running = False
        except Exception as e:
            print(f"\n\n❌ 실행 오류: {e}")
            self.is_running = False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리 (메모리 최적화)"""
        if self.bithumb_client:
            self.bithumb_client.close()
            self.bithumb_client = None
        if self.discord_webhook:
            self.discord_webhook.close()
            self.discord_webhook = None
        
        # 메모리 정리
        gc.collect()
        print("✅ 리소스 정리 완료")

def main():
    """메인 실행 함수"""
    try:
        print("🎯 빗썸 상승신호 알림 시스템")
        print("="*50)
        print("1. 1회 스캔")
        print("2. 연속 스캔")
        print("3. 설정 확인")
        print("4. 종료")
        print("="*50)
        
        choice = input("선택 (1-4): ").strip()
        
        bot = TradingSignalBot()
        
        if choice == '1':
            print("1회 스캔을 시작합니다...")
            bot.run_once()
        elif choice == '2':
            print("연속 스캔을 시작합니다...")
            bot.run_continuous()
        elif choice == '3':
            print("\n📊 현재 설정:")
            for key, value in bot.config.items():
                print(f"  {key}: {value}")
            print("\n설정 수정: python3 config_manager.py")
        elif choice == '4':
            print("종료합니다.")
        else:
            print("올바른 선택지를 입력하세요.")
            
    except KeyboardInterrupt:
        print("\n\n🛑 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()