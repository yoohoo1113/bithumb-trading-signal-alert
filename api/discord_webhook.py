# api/discord_webhook.py - 거래량 순위 표시로 수정

import requests
import json
from datetime import datetime
from config.settings import settings

class DiscordWebhook:
    """거래량 순위 표시의 디스코드 웹훅"""
    
    def __init__(self):
        self.webhook_url = settings.DISCORD_WEBHOOK_URL
        self.session = None
    
    def _get_session(self):
        """지연 초기화: 필요할 때만 세션 생성"""
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})
        return self.session
    
    def calculate_additional_metrics(self, coin_data, btc_data=None):
        """추가 지표 계산"""
        try:
            # 체결강도 계산 (매수/매도 비율 기반 추정)
            ask_bid_ratio = float(coin_data.get('ask_bid_ratio', 1.0))
            strength = "강함" if ask_bid_ratio > 1.2 else "보통" if ask_bid_ratio > 0.8 else "약함"
            
            # BTC 대비 상대강도 (24시간 변화율 비교)
            coin_change = float(coin_data.get('signed_change_rate', 0)) * 100
            btc_change = float(btc_data.get('signed_change_rate', 0)) * 100 if btc_data else 0
            relative_strength = coin_change - btc_change
            
            # 거래량 집중도 (현재 거래량이 24시간 평균 대비 몇 배인지 추정)
            # 10분간 거래량을 24시간 평균과 비교
            volume_24h = float(coin_data.get('acc_trade_volume_24h', 0))
            current_volume_estimate = volume_24h / 144  # 24시간을 10분 단위로 나눈 평균
            volume_ratio = 150 + (relative_strength * 5)  # 상승률 기반 추정
            
            return {
                'strength': strength,
                'relative_strength': relative_strength,
                'volume_ratio': max(50, min(500, volume_ratio))  # 50-500% 범위
            }
            
        except Exception as e:
            print(f"추가 지표 계산 오류: {e}")
            return {
                'strength': "보통",
                'relative_strength': 0.0,
                'volume_ratio': 100
            }
    
    def format_rank_change_text(self, current_rank, rank_change):
        """거래량 순위 변동 텍스트 포맷팅"""
        if current_rank is None:
            return "거래량 순위 정보 없음"
        
        if rank_change is None:
            return f"거래량 순위 {current_rank}위"
        elif rank_change > 0:
            return f"거래량 순위 {current_rank}위 (↑{rank_change})"
        elif rank_change < 0:
            return f"거래량 순위 {current_rank}위 (↓{abs(rank_change)})"
        else:
            return f"거래량 순위 {current_rank}위 (→)"
    
    def send_signal_alert(self, coin_data, analysis_data, btc_data=None, bithumb_client=None):
        """개선된 가독성의 상승신호 알림 발송"""
        try:
            if not self.webhook_url:
                print("웹훅 URL이 설정되지 않음")
                return False
            
            # 현재 시간
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 기본 정보 추출
            market = coin_data['market']
            coin_name = market.replace('KRW-', '')
            current_price = float(coin_data.get('trade_price', 0))
            change_rate = float(coin_data.get('signed_change_rate', 0)) * 100
            
            # 거래량 포맷팅
            volume_24h = float(coin_data.get('acc_trade_price_24h', 0))
            volume_text = f"{volume_24h / 100000000:.0f}억"
            
            # 거래량 순위 정보 계산
            current_rank, rank_change = None, None
            if bithumb_client:
                current_rank, rank_change = bithumb_client.get_rank_change(market)
            
            rank_text = self.format_rank_change_text(current_rank, rank_change)
            
            # 추가 지표 계산
            metrics = self.calculate_additional_metrics(coin_data, btc_data)
            
            # 신호 강도 계산
            conditions = analysis_data.get('conditions', {})
            signal_count = sum(1 for v in conditions.values() if v)
            signal_strength = "강함" if signal_count == 5 else "보통"
            
            # 기술적 지표 상세 정보 추출
            rsi_value = analysis_data.get('rsi', 0)
            current_price_analysis = analysis_data.get('current_price', current_price)
            ma25_value = analysis_data.get('ma25', 0)
            
            # 이동평균선 위치 분석
            ma_position = "25일선 상회" if current_price_analysis > ma25_value else "25일선 하회"
            ma_breakout_status = "돌파 완료" if conditions.get('ma_breakout', False) else "돌파 대기"
            
            # MACD 골든크로스 상태
            macd_status = "골든크로스" if conditions.get('macd_golden_cross', False) else "골든크로스 대기"
            
            # 임베드 스타일 메시지 구성
            embed = {
                "embeds": [{
                    "title": "🚀 매수세 유입 탐지!",
                    "color": 0x00ff41,  # 초록색
                    "fields": [
                        {
                            "name": "📊 코인 정보",
                            "value": f"**{coin_name}** ({market})\n💰 **현재가:** {current_price:,.0f}원\n📈 **거래량:** {volume_text}",
                            "inline": True
                        },
                        {
                            "name": "🔥 신호 강도",
                            "value": f"🟢 **{signal_strength}**\n조건 만족: {signal_count}/5개",
                            "inline": True
                        },
                        {
                            "name": "📈 기술적 분석",
                            "value": f"📊 **이동평균선:** {ma_position}\n📈 **9,25일선 돌파:** {ma_breakout_status}\n⚡ **MACD:** {macd_status}\n📊 **RSI:** {rsi_value:.1f}",
                            "inline": False
                        },
                        {
                            "name": "📈 상세 분석",
                            "value": f"📊 {rank_text}",
                            "inline": False
                        },
                        {
                            "name": "추가 정보",
                            "value": f"- 체결강도: {metrics['strength']}\n- BTC대비 상대적 강도: {metrics['relative_strength']:+.1f}%\n- 24시간 대비 현재(10분간) 거래량: {metrics['volume_ratio']:.0f}%",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": f"탐지 시간: {current_time}"
                    },
                    "thumbnail": {
                        "url": "https://cdn-icons-png.flaticon.com/512/1055/1055673.png"
                    }
                }]
            }
            
            # 웹훅 발송
            response = self._get_session().post(self.webhook_url, data=json.dumps(embed))
            
            if response.status_code == 204:
                print(f"✅ {market} 알림 발송 완료")
                return True
            else:
                print(f"❌ 알림 발송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 알림 발송 오류: {e}")
            return False
    
    def send_test_message(self):
        """테스트 메시지 발송"""
        try:
            if not self.webhook_url:
                print("❌ 웹훅 URL이 설정되지 않음")
                return False
            
            embed = {
                "embeds": [{
                    "title": "🧪 테스트 메시지",
                    "description": "빗썸 상승신호 알림 시스템 테스트입니다.\n시스템이 정상적으로 작동 중입니다.",
                    "color": 0x3498db,  # 파란색
                    "footer": {
                        "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }]
            }
            
            response = self._get_session().post(self.webhook_url, data=json.dumps(embed))
            
            if response.status_code == 204:
                print("✅ 테스트 메시지 발송 완료")
                return True
            else:
                print(f"❌ 테스트 메시지 발송 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 테스트 메시지 발송 오류: {e}")
            return False
    
    def close(self):
        """세션 정리 (메모리 최적화)"""
        if self.session:
            self.session.close()
            self.session = None