# debug_ranking_test.py - 거래량 순위 시스템 테스트

import requests
import json
import os

def test_bithumb_api():
    """빗썸 API 테스트"""
    print("=== 빗썸 API 테스트 ===")
    
    try:
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        response = requests.get(url)
        
        print(f"응답 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"응답 상태: {data.get('status')}")
            
            if data.get("status") == "0000":
                ticker_data = data.get("data", {})
                print(f"코인 개수: {len(ticker_data)}")
                
                # 상위 5개 코인 확인
                coin_list = []
                for symbol, info in ticker_data.items():
                    if symbol != "date" and isinstance(info, dict):
                        try:
                            volume_24h = float(info.get("acc_trade_value_24H", 0))
                            coin_list.append({
                                "symbol": symbol,
                                "market": f"KRW-{symbol}",
                                "volume": volume_24h
                            })
                        except:
                            continue
                
                # 거래량 순위 정렬
                coin_list.sort(key=lambda x: x["volume"], reverse=True)
                
                print("\n상위 10개 코인 거래량:")
                for i, coin in enumerate(coin_list[:10], 1):
                    print(f"{i}위: {coin['market']} - {coin['volume']:,.0f} KRW")
                
                return coin_list
            else:
                print(f"API 오류: {data.get('status')}")
                return []
        else:
            print(f"HTTP 오류: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"API 테스트 오류: {e}")
        return []

def test_ranking_system(coin_list):
    """순위 시스템 테스트"""
    print("\n=== 순위 시스템 테스트 ===")
    
    if not coin_list:
        print("코인 리스트가 비어있음")
        return
    
    # data 폴더 생성
    os.makedirs("data", exist_ok=True)
    
    # 순위 딕셔너리 생성
    ranking = {}
    for i, coin in enumerate(coin_list, 1):
        ranking[coin["market"]] = i
    
    print(f"생성된 순위 개수: {len(ranking)}")
    
    # 순위 파일 저장 테스트
    ranking_file = "data/test_ranking.json"
    try:
        with open(ranking_file, 'w') as f:
            json.dump(ranking, f, indent=2)
        print(f"순위 파일 저장 성공: {ranking_file}")
        
        # 파일 읽기 테스트
        with open(ranking_file, 'r') as f:
            loaded_ranking = json.load(f)
        print(f"순위 파일 로드 성공: {len(loaded_ranking)}개")
        
        # 특정 코인 순위 확인
        test_coins = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        for coin in test_coins:
            rank = loaded_ranking.get(coin)
            if rank:
                print(f"{coin}: {rank}위")
            else:
                print(f"{coin}: 순위 정보 없음")
                
        return loaded_ranking
        
    except Exception as e:
        print(f"순위 시스템 오류: {e}")
        return None

def test_rank_change(ranking):
    """순위 변동 테스트"""
    print("\n=== 순위 변동 테스트 ===")
    
    if not ranking:
        print("순위 데이터가 없음")
        return
    
    # 가상의 이전 순위 생성 (약간의 변동)
    previous_ranking = {}
    for market, rank in ranking.items():
        # 일부 코인의 순위를 임의로 변경
        if "BTC" in market:
            previous_ranking[market] = rank + 1  # 1단계 하락
        elif "ETH" in market:
            previous_ranking[market] = rank - 2  # 2단계 상승
        else:
            previous_ranking[market] = rank  # 변동 없음
    
    # 이전 순위 파일 저장
    backup_file = "data/test_ranking_backup.json"
    with open(backup_file, 'w') as f:
        json.dump(previous_ranking, f, indent=2)
    
    # 순위 변동 계산 테스트
    test_markets = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
    
    for market in test_markets:
        current_rank = ranking.get(market)
        previous_rank = previous_ranking.get(market)
        
        if current_rank and previous_rank:
            rank_change = previous_rank - current_rank
            
            if rank_change > 0:
                change_text = f"↑{rank_change}"
            elif rank_change < 0:
                change_text = f"↓{abs(rank_change)}"
            else:
                change_text = "→"
            
            print(f"{market}: 현재 {current_rank}위 (이전 {previous_rank}위) {change_text}")
        else:
            print(f"{market}: 순위 정보 불완전")

def main():
    """메인 테스트 실행"""
    print("거래량 순위 시스템 디버깅 테스트")
    print("=" * 50)
    
    # 1. 빗썸 API 테스트
    coin_list = test_bithumb_api()
    
    # 2. 순위 시스템 테스트
    ranking = test_ranking_system(coin_list)
    
    # 3. 순위 변동 테스트
    test_rank_change(ranking)
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    
    # 파일 정리
    test_files = [
        "data/test_ranking.json",
        "data/test_ranking_backup.json"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"테스트 파일 삭제: {file_path}")

if __name__ == "__main__":
    main()