import pandas as pd
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote
import time
import os
from dotenv import load_dotenv

load_dotenv()
api_key = unquote(os.getenv("DATA_GO_KR_API_KEY"))

# 1. 수집 대상 설정
# API별 오퍼레이션 명칭 매핑
API_TARGETS = {
    "dgsbjt_info": "getMdlrtSbjectInfoList",  # 진료과목
    "equip_info": "getHospEquipInfoList",  # 장비정보 (예시)
    "nursing_info": "getNursigGradeInfoList",  # 간호등급
    "facility_info": "getFcltyInfoList"  # 시설정보
}

BASE_URL = "http://apis.data.go.kr/B551182/hospInfoServicev2/"

# 2. 요양기호 로드
input_file = '../data/raw/hospital_basic_info.csv'
if not os.path.exists(input_file):
    raise FileNotFoundError("02번 스크립트를 먼저 실행하여 기본 정보를 수집하세요.")

df_basic = pd.read_csv(input_file)
target_ykiho_list = df_basic['ykiho'].unique()
print(f"상세 정보 수집 대상: {len(target_ykiho_list)}개 병원")


# 3. 수집 함수
def fetch_detail(ykiho, operation):
    url = BASE_URL + operation
    params = {'ServiceKey': api_key, 'ykiho': ykiho, 'numOfRows': 100}
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            items = root.findall('.//item')
            parsed_data = []
            for item in items:
                # 모든 하위 태그를 딕셔너리로 변환
                row = {child.tag: child.text for child in item}
                row['ykiho'] = ykiho  # 식별자 추가
                parsed_data.append(row)
            return parsed_data
        return []
    except Exception:
        return []


# 4. 실행 루프
results = {k: [] for k in API_TARGETS.keys()}

print("상세 정보 수집 시작 (시간이 오래 걸릴 수 있습니다)...")

for idx, ykiho in enumerate(target_ykiho_list):
    for key, operation in API_TARGETS.items():
        data = fetch_detail(ykiho, operation)
        if data:
            results[key].extend(data)

    if (idx + 1) % 50 == 0:
        print(f"진행률: {idx + 1}/{len(target_ykiho_list)}")
    time.sleep(0.05)  # API 호출 제한 고려

# 5. 저장
output_dir = '../data/raw'
for key, data_list in results.items():
    if data_list:
        df = pd.DataFrame(data_list)
        save_name = os.path.join(output_dir, f'hospital_detail_{key}.csv')
        df.to_csv(save_name, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {save_name} ({len(df)}건)")
    else:
        print(f"데이터 없음: {key}")