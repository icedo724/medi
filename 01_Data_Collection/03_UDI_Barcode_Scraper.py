import pandas as pd
import requests
import ssl
from urllib3 import poolmanager
from requests.adapters import HTTPAdapter
import xml.etree.ElementTree as ET
import os
import time
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
api_key = os.getenv("DATA_GO_KR_API_KEY")

if not api_key:
    raise ValueError("ERROR: .env 파일에 'DATA_GO_KR_API_KEY'가 설정되지 않았습니다.")


# 2. SSL 인증서 오류 해결을 위한 어댑터 설정
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        self.poolmanager = poolmanager.PoolManager(*args, ssl_context=ctx, **kwargs)


session = requests.session()
adapter = TLSAdapter()
session.mount("https://", adapter)

# 3. 데이터 로드 (수집 대상 바코드)
# 상위 폴더의 data/raw 경로 참조
input_path = '../data/raw/target_barcodes.csv'

if not os.path.exists(input_path):
    print(f"파일이 없습니다: {input_path}")
    # 테스트용 데이터 생성 (실제 사용 시 제거 가능)
    df = pd.DataFrame({'barcode': ['08800026300229', '08806125619033']})
else:
    df = pd.read_csv(input_path)

target_barcodes = df['barcode'].unique()
print(f"총 조회 대상: {len(target_barcodes)}건")

# 4. API 설정
url = 'https://apis.data.go.kr/1471000/MdrUdiSvc/getUdiInfo'
results = []
no_data_list = []

print("데이터 수집을 시작합니다...")

# 5. 수집 루프
for i, barcode in enumerate(target_barcodes):
    params = {
        'serviceKey': api_key,  # Decoding 된 키 사용 (필요시 unquote 사용)
        'udi_di_code': barcode,
        'numOfRows': 1,
        'pageNo': 1
    }

    try:
        response = session.get(url, params=params, timeout=10)

        # XML 파싱
        try:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')

            if items:
                for item in items:
                    data = {
                        'barcode': barcode,
                        'company_name': item.findtext('mnfcoNm'),  # 제조사
                        'product_name': item.findtext('prductNm'),  # 제품명
                        'model_name': item.findtext('mdlNm'),  # 모델명
                        'storage_method': item.findtext('strgMthd')  # 보관방법
                    }
                    results.append(data)
            else:
                no_data_list.append(barcode)

        except ET.ParseError:
            print(f"XML Parsing Error: {barcode}")
            no_data_list.append(barcode)

    except Exception as e:
        print(f"Network Error ({barcode}): {e}")

    # 진행상황 출력 (10건 단위)
    if (i + 1) % 10 == 0:
        print(f"진행 중... ({i + 1}/{len(target_barcodes)})")

    time.sleep(0.1)  # API 부하 방지

# 6. 결과 저장
output_dir = '../data/raw'
os.makedirs(output_dir, exist_ok=True)

if results:
    df_result = pd.DataFrame(results)
    save_path = os.path.join(output_dir, 'udi_collection_result.csv')
    df_result.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"✅ 수집 완료! 저장 경로: {save_path}")
    print(f"데이터 있음: {len(df_result)}건, 없음: {len(no_data_list)}건")
else:
    print("수집된 데이터가 없습니다.")