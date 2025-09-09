# api/bithumb_client.py - 거래량 순위 완전 수정 (빗썸 ALL_KRW API 사용)

import requests
import time
import json
import os
from config.settings import settings

class BithumbClient:
    """빗썸 ALL_KRW API를 사용한 클라이언트"""
    
    def __init__(self):
        self.base_url = settings.BITHUMB_BASE_URL
        self.session = None
        self.ranking_file = "data/previous_ranking.json"
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """data 디렉토리 생성"""
        os.makedirs("data", exist_ok=True)
    
    def _get_session(self):
        """지연 초기화: 필요할 때만 세션 생성"""
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update({"accept": "application/json"})
        return self.session
    
    def get_market_list(self):
        """빗썸 ALL_KRW API에서 마켓 목록 추출"""
        try:
            # 빗썸 ALL_KRW API로 전체 코인 목록 조회
            url = "https://api.bithumb.com/public/ticker/ALL_KRW"
            response = self._get_session().get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "0000":
                    ticker_data = data.get("data", {})
                    
                    # KRW 마켓 목록 생성
                    krw_markets = []
                    for symbol in ticker_data.keys():
                        if symbol != "date":  # 날짜 정보 제외
                            krw_markets.append({"market": f"KRW-{symbol}"})
                    
                    print(f"KRW 마켓 {len(krw_markets)}개 조회 완료 (빗썸 ALL_KRW API)")
                    return krw_markets
                else:
                    print(f"빗썸 API 상태 오류: {data.get('status')}")
                    return []
            else:
                print(f"마켓 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"마켓 조회 오류: {e}")
            return []
    
    def get_ticker_data(self, markets=None):
        """빗썸 ALL_KRW API로 전체 현재가 정보 조회"""
        try:
            # 빗썸의 전체 KRW 마켓 티커 조회 API
            url = "https://api.bithumb.com/public/ticker/ALL_KRW"
            print(f"📡 빗썸 ALL_KRW API 호출: {url}")
            
            response = self._get_session().get(url)
            
            if response.status_code != 200:
                print(f"❌ API 호출 실패: {response.status_code}")
                return [], None
            
            data = response.json()
            
            if data.get("status") != "0000":
                print(f"❌ API 응답 오류: {data.get('status')}")
                return [], None
            
            ticker_data = data.get("data", {})
            if not ticker_data:
                print("❌ 티커 데이터가 비어있음")
                return [], None
            
            print(f"✅ 빗썸 API 응답 성공: {len(ticker_data)}개 코인 데이터")
            
            # 빗썸 형식을 업비트 호환 형식으로 변환
            all_tickers = []
            btc_ticker = None
            
            for symbol, info in ticker_data.items():
                if symbol == "date":  # 날짜 정보 제외
                    continue
                
                if not isinstance(info, dict):
                    continue
                
                try:
                    # 빗썸 형식을 업비트 호환 형식으로 변환
                    converted_ticker = {
                        "market": f"KRW-{symbol}",
                        "trade_price": float(info.get("closing_price", 0)),
                        "signed_change_rate": float(info.get("fluctate_rate_24H", 0)) / 100,
                        "acc_trade_price_24h": float(info.get("acc_trade_value_24H", 0)),
                        "acc_trade_volume_24h": float(info.get("acc_trade_volume_24H", 0))
                    }
                    
                    all_tickers.append(converted_ticker)
                    
                    # BTC 데이터 별도 저장
                    if symbol == "BTC":
                        btc_ticker = converted_ticker
                        
                except (ValueError, KeyError) as e:
                    print(f"⚠️ {symbol} 데이터 변환 오류: {e}")
                    continue
            
            print(f"📊 변환 완료: {len(all_tickers)}개 코인")
            
            # 거래량 기준 내림차순 정렬
            sorted_tickers = sorted(all_tickers, 
                                  key=lambda x: float(x.get('acc_trade_price_24h', 0)), 
                                  reverse=True)
            
            print(f"📊 거래량 정렬 완료: 1위 {sorted_tickers[0]['market']}")
            
            # 거래량 순위 계산 및 저장
            current_ranking = self._calculate_volume_ranking(sorted_tickers)
            self._save_current_ranking(current_ranking)
            
            # 상위 200개만 반환
            top_count = getattr(settings, 'TOP_COINS_COUNT', 200)
            top_tickers = sorted_tickers[:top_count]
            print(f"🎯 거래량 상위 {len(top_tickers)}개 코인 선택 완료")
            
            return top_tickers, btc_ticker
            
        except Exception as e:
            print(f"❌ 빗썸 API 호출 오류: {e}")
            return [], None
    
    def _calculate_volume_ranking(self, sorted_tickers):
        """거래량 순위 계산"""
        ranking = {}
        for idx, ticker in enumerate(sorted_tickers, 1):
            market = ticker.get('market')
            ranking[market] = idx
        return ranking
    
    def _save_current_ranking(self, current_ranking):
        """현재 순위를 이전 순위로 저장 (디버깅 강화)"""
        try:
            print(f"💾 순위 저장 시작 - 총 {len(current_ranking)}개 코인")
            
            # 기존 순위 백업
            if os.path.exists(self.ranking_file):
                with open(self.ranking_file, 'r') as f:
                    previous_ranking = json.load(f)
                
                # 백업 파일 생성
                backup_file = self.ranking_file.replace('.json', '_backup.json')
                with open(backup_file, 'w') as f:
                    json.dump(previous_ranking, f)
                print(f"✅ 이전 순위 백업 완료: {len(previous_ranking)}개")
            else:
                print("📝 첫 실행 - 이전 순위 파일 없음")
            
            # 현재 순위 저장
            with open(self.ranking_file, 'w') as f:
                json.dump(current_ranking, f)
            
            print(f"✅ 현재 순위 저장 완료: {self.ranking_file}")
            
            # 상위 5개 순위 확인
            top_5 = dict(list(current_ranking.items())[:5])
            print(f"📊 상위 5개 순위: {top_5}")
                
        except Exception as e:
            print(f"❌ 순위 저장 오류: {e}")
            print(f"🗂️ 데이터 폴더 존재: {os.path.exists('data')}")
            print(f"🗂️ 순위 파일 경로: {self.ranking_file}")
            
            # 디렉토리 다시 생성 시도
            try:
                os.makedirs("data", exist_ok=True)
                print("📁 데이터 폴더 재생성 완료")
            except Exception as dir_error:
                print(f"❌ 데이터 폴더 생성 실패: {dir_error}")
    
    def get_rank_change(self, market):
        """거래량 순위 변동 계산 (디버깅 강화)"""
        try:
            print(f"🔍 순위 조회 시작: {market}")
            
            # 현재 순위 로드
            if not os.path.exists(self.ranking_file):
                print(f"❌ 순위 파일이 없음: {self.ranking_file}")
                return None, None
            
            with open(self.ranking_file, 'r') as f:
                current_ranking = json.load(f)
            
            current_rank = current_ranking.get(market)
            print(f"📊 현재 순위: {market} = {current_rank}")
            
            if not current_rank:
                print(f"❌ {market}의 현재 순위 정보 없음")
                available_markets = list(current_ranking.keys())[:5]
                print(f"📝 사용 가능한 마켓 예시: {available_markets}")
                return None, None
            
            # 이전 순위 로드
            backup_file = self.ranking_file.replace('.json', '_backup.json')
            if not os.path.exists(backup_file):
                print(f"⚠️ 백업 파일이 없음: {backup_file} (첫 실행)")
                return current_rank, None
            
            with open(backup_file, 'r') as f:
                previous_ranking = json.load(f)
            
            previous_rank = previous_ranking.get(market)
            print(f"📊 이전 순위: {market} = {previous_rank}")
            
            if not previous_rank:
                print(f"⚠️ {market}의 이전 순위 정보 없음 (신규 상장?)")
                return current_rank, None
            
            # 순위 변동 계산 (이전 순위 - 현재 순위 = 상승한 계단 수)
            rank_change = previous_rank - current_rank
            print(f"📈 순위 변동: {market} = {rank_change} (이전 {previous_rank} → 현재 {current_rank})")
            
            return current_rank, rank_change
            
        except Exception as e:
            print(f"❌ 순위 변동 계산 오류: {e}")
            print(f"🗂️ 파일 상태 - 현재: {os.path.exists(self.ranking_file)}, 백업: {os.path.exists(self.ranking_file.replace('.json', '_backup.json'))}")
            return None, None
    
    def get_candle_data(self, market, count=200):
        """1시간 캔들 데이터 조회 (공식 문서 기준)"""
        try:
            url = f"{self.base_url}/v1/candles/minutes/60?market={market}&count={count}"
            response = self._get_session().get(url)
            
            if response.status_code == 200:
                candles = response.json()
                print(f"{market} 1시간봉 {len(candles)}개 조회 완료")
                return candles
            else:
                print(f"{market} 캔들 데이터 조회 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"{market} 캔들 데이터 오류: {e}")
            return []
    
    def close(self):
        """세션 정리 (메모리 최적화)"""
        if self.session:
            self.session.close()
            self.session = None