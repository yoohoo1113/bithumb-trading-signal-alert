# config_manager.py - 터미널에서 4가지 조건 수정

import os
import json
from config.settings import settings

class ConfigManager:
    """터미널에서 신호 조건을 동적으로 수정하는 관리자"""
    
    CONFIG_FILE = "signal_config.json"
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드 (없으면 기본값 생성)"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 기본 설정값
        return {
            "rsi_threshold": 45,
            "ma_periods": [9, 25, 99, 200],
            "require_ma_breakout": True,
            "require_price_above_ma25": True,
            "require_macd_golden_cross": True,
            "scan_interval": 600,
            "top_coins_count": 200
        }
    
    def save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("✅ 설정이 저장되었습니다.")
            return True
        except Exception as e:
            print(f"❌ 설정 저장 실패: {e}")
            return False
    
    def show_current_config(self):
        """현재 설정 표시"""
        print("\n📊 현재 신호 조건 설정:")
        print("="*50)
        print(f"1. RSI 임계값: {self.config['rsi_threshold']} 이상")
        print(f"2. 이동평균선 기간: {self.config['ma_periods']}")
        print(f"3. 9,25일선이 99,200일선 돌파: {'필수' if self.config['require_ma_breakout'] else '선택'}")
        print(f"4. MACD 골든크로스: {'필수' if self.config['require_macd_golden_cross'] else '선택'}")
        print(f"5. 가격이 25일선 위: {'필수' if self.config['require_price_above_ma25'] else '선택'}")
        print(f"6. 스캔 간격: {self.config['scan_interval']//60}분")
        print(f"7. 대상 코인 수: {self.config['top_coins_count']}개")
        print("="*50)
    
    def modify_rsi_threshold(self):
        """RSI 임계값 수정"""
        try:
            current = self.config['rsi_threshold']
            print(f"\n현재 RSI 임계값: {current}")
            new_value = input("새로운 RSI 임계값 (30-70): ").strip()
            
            if new_value:
                threshold = float(new_value)
                if 30 <= threshold <= 70:
                    self.config['rsi_threshold'] = threshold
                    print(f"✅ RSI 임계값을 {threshold}로 변경했습니다.")
                else:
                    print("❌ RSI 임계값은 30-70 사이여야 합니다.")
        except ValueError:
            print("❌ 올바른 숫자를 입력하세요.")
    
    def modify_ma_periods(self):
        """이동평균선 기간 수정"""
        try:
            current = self.config['ma_periods']
            print(f"\n현재 이동평균선 기간: {current}")
            print("예시: 5,20,60,120 (쉼표로 구분)")
            new_value = input("새로운 이동평균선 기간들: ").strip()
            
            if new_value:
                periods = [int(x.strip()) for x in new_value.split(',')]
                if len(periods) == 4 and all(p > 0 for p in periods):
                    self.config['ma_periods'] = sorted(periods)
                    print(f"✅ 이동평균선 기간을 {self.config['ma_periods']}로 변경했습니다.")
                else:
                    print("❌ 정확히 4개의 양수를 입력하세요.")
        except ValueError:
            print("❌ 올바른 숫자를 입력하세요.")
    
    def toggle_condition(self, condition_key, condition_name):
        """조건 필수/선택 토글"""
        current = self.config[condition_key]
        self.config[condition_key] = not current
        status = "필수" if self.config[condition_key] else "선택"
        print(f"✅ {condition_name}을(를) {status}으로 변경했습니다.")
    
    def modify_scan_interval(self):
        """스캔 간격 수정"""
        try:
            current_minutes = self.config['scan_interval'] // 60
            print(f"\n현재 스캔 간격: {current_minutes}분")
            new_value = input("새로운 스캔 간격 (분): ").strip()
            
            if new_value:
                minutes = int(new_value)
                if 1 <= minutes <= 60:
                    self.config['scan_interval'] = minutes * 60
                    print(f"✅ 스캔 간격을 {minutes}분으로 변경했습니다.")
                else:
                    print("❌ 스캔 간격은 1-60분 사이여야 합니다.")
        except ValueError:
            print("❌ 올바른 숫자를 입력하세요.")
    
    def modify_top_coins_count(self):
        """대상 코인 수 수정"""
        try:
            current = self.config['top_coins_count']
            print(f"\n현재 대상 코인 수: {current}개")
            new_value = input("새로운 대상 코인 수 (50-500): ").strip()
            
            if new_value:
                count = int(new_value)
                if 50 <= count <= 500:
                    self.config['top_coins_count'] = count
                    print(f"✅ 대상 코인 수를 {count}개로 변경했습니다.")
                else:
                    print("❌ 대상 코인 수는 50-500개 사이여야 합니다.")
        except ValueError:
            print("❌ 올바른 숫자를 입력하세요.")
    
    def interactive_menu(self):
        """대화형 설정 메뉴"""
        while True:
            self.show_current_config()
            print("\n🔧 설정 수정 메뉴:")
            print("1. RSI 임계값 수정")
            print("2. 이동평균선 기간 수정")
            print("3. 9,25일선 돌파 조건 토글")
            print("4. MACD 골든크로스 조건 토글")
            print("5. 가격 > 25일선 조건 토글")
            print("6. 스캔 간격 수정")
            print("7. 대상 코인 수 수정")
            print("8. 설정 저장")
            print("9. 종료")
            
            choice = input("\n선택 (1-9): ").strip()
            
            if choice == '1':
                self.modify_rsi_threshold()
            elif choice == '2':
                self.modify_ma_periods()
            elif choice == '3':
                self.toggle_condition('require_ma_breakout', '9,25일선 돌파 조건')
            elif choice == '4':
                self.toggle_condition('require_macd_golden_cross', 'MACD 골든크로스 조건')
            elif choice == '5':
                self.toggle_condition('require_price_above_ma25', '가격 > 25일선 조건')
            elif choice == '6':
                self.modify_scan_interval()
            elif choice == '7':
                self.modify_top_coins_count()
            elif choice == '8':
                self.save_config()
            elif choice == '9':
                break
            else:
                print("❌ 1-9 사이의 숫자를 입력하세요.")
            
            input("\nEnter를 눌러 계속...")

def main():
    """메인 실행 함수"""
    print("🔧 빗썸 상승신호 조건 설정 관리자")
    config_manager = ConfigManager()
    config_manager.interactive_menu()
    print("👋 설정 관리자를 종료합니다.")

if __name__ == "__main__":
    main()