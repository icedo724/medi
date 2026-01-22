import pandas as pd
import json
import os

# 1. 데이터 로드
base_dir = '../data/raw'
file_path = os.path.join(base_dir, 'boxhero.csv')

if not os.path.exists(file_path):
    print("경고: boxhero.csv 파일이 없습니다. (테스트를 위해 빈 DataFrame 생성)")
    df = pd.DataFrame({'attributes': []})  # 더미 데이터
else:
    df = pd.read_csv(file_path)

print(f"원본 데이터 크기: {df.shape}")


# 2. JSON 파싱 함수 (완전한 로직)
def expand_attrs(row):
    """
    [{'name': 'Color', 'value': 'Red'}, ...] 형태의 문자열을
    {'Color': 'Red'} 딕셔너리로 변환
    """
    if pd.isna(row) or row == '':
        return {}

    try:
        # 문자열이면 JSON 로드, 리스트면 그대로 사용
        data = json.loads(row) if isinstance(row, str) else row

        if isinstance(data, list):
            result = {}
            for item in data:
                # name과 value 키가 있는지 확인
                if 'name' in item and 'value' in item:
                    result[item['name']] = item['value']
            return result
        return {}

    except (json.JSONDecodeError, TypeError):
        return {}


# 3. 적용 및 병합
if 'attributes' in df.columns:
    print("속성 파싱 중...")
    attr_df = df['attributes'].apply(expand_attrs).apply(pd.Series)

    # 원본과 병합
    df_cleaned = pd.concat([df, attr_df], axis=1)
    df_cleaned.drop(columns=['attributes'], inplace=True)
else:
    df_cleaned = df.copy()

# 4. 컬럼명 정제
# 특수문자 제거 및 공백 제거
df_cleaned.columns = df_cleaned.columns.str.replace('*', '', regex=False).str.strip()

# 5. 저장
processed_dir = '../data/processed'
os.makedirs(processed_dir, exist_ok=True)
save_path = os.path.join(processed_dir, 'inventory_cleaned.csv')

df_cleaned.to_csv(save_path, index=False, encoding='utf-8-sig')
print(f"전처리 완료. 저장 경로: {save_path}")