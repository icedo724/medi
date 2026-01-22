import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import os
from urllib.parse import unquote
from dotenv import load_dotenv
from rapidfuzz import process, fuzz  # pip install rapidfuzz

# 1. 설정
load_dotenv()
api_key = unquote(os.getenv("DATA_GO_KR_API_KEY"))  # 인코딩된 키일 경우 디코딩
url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"


# 2. 수집 함수 정의
def get_hospital_list(page_no, num_rows=1000):
    params = {
        'ServiceKey': api_key,
        'pageNo': page_no,
        'numOfRows': num_rows,
        'clCd': '01',  # 상급종합병원 (필요에 따라 11, 21 등 추가)
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            items = root.findall(".//item")

            data_list = []
            for item in items:
                data_list.append({
                    'ykiho': item.findtext('ykiho'),  # 암호화된 요양기호
                    'yadmNm': item.findtext('yadmNm'),  # 병원명
                    'sgguCdNm': item.findtext('sgguCdNm'),  # 시군구명
                    'addr': item.findtext('addr'),  # 주소
                    'clCdNm': item.findtext('clCdNm')  # 종별코드명
                })
            return data_list
        else:
            print(f"API Error Code: {resp.status_code}")
            return None
    except Exception as e:
        print(f"Error on page {page_no}: {e}")
        return None


# 3. 데이터 수집 실행
all_hospitals = []
max_pages = 10  # 예시 (실제 데이터 양에 맞춰 조절)

print("병원 기본 정보를 수집합니다...")
for page in range(1, max_pages + 1):
    data = get_hospital_list(page)
    if data:
        all_hospitals.extend(data)
        if page % 5 == 0:
            print(f"{page}페이지 완료...")
    else:
        print(f"{page}페이지에서 데이터가 없거나 에러가 발생하여 종료합니다.")
        break
    time.sleep(0.1)

df_hospitals = pd.DataFrame(all_hospitals)
print(f"수집된 병원 수: {len(df_hospitals)}건")

# 4. 결과 저장
output_path = '../data/raw/hospital_basic_info.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_hospitals.to_csv(output_path, index=False, encoding='utf-8-sig')

# 5. 유사도 검사 (내부 거래처 vs 공공데이터 병원명)
client_file = '../data/raw/client_list.csv'

if os.path.exists(client_file) and not df_hospitals.empty:
    print("\n[유사도 검사 시작]")
    df_clients = pd.read_csv(client_file)

    # 비교 대상 병원명 리스트
    public_names = df_hospitals['yadmNm'].tolist()

    results = []

    for client_name in df_clients['client_name']:  # 'client_name' 컬럼 가정
        # 가장 유사한 상위 1개 추출
        match = process.extractOne(client_name, public_names, scorer=fuzz.token_sort_ratio)
        if match:
            best_match, score, index = match
            results.append({
                'internal_name': client_name,
                'public_name': best_match,
                'score': score,
                'ykiho': df_hospitals.iloc[index]['ykiho']
            })

    df_match = pd.DataFrame(results)
    match_save_path = '../data/processed/name_similarity_check.csv'
    df_match.to_csv(match_save_path, index=False, encoding='utf-8-sig')
    print(f"유사도 검사 완료. 저장 경로: {match_save_path}")
else:
    print("\n거래처 파일이 없거나 수집된 데이터가 없어 유사도 검사를 건너뜁니다.")