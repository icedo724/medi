import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import platform

# 1. 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
else:
    plt.rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

# 2. 데이터 로드
# 03단계 SQL 결과를 엑셀로 저장했다고 가정
data_path = '../data/processed/analysis_mart.xlsx'

if not os.path.exists(data_path):
    print(f"파일 없음: {data_path}. (더미 데이터를 생성합니다)")
    # 데모용 더미 데이터
    data = {
        'ykiho': ['A001', 'A002', 'A003', 'A001', 'A002'],
        'sales_date': pd.to_datetime(['2025-01-01', '2025-02-01', '2024-12-01', '2025-03-01', '2025-01-15']),
        'amount': [100000, 200000, 50000, 150000, 30000],
        'order_id': [1, 2, 3, 4, 5]
    }
    df_sales = pd.DataFrame(data)
else:
    df_sales = pd.read_excel(data_path, sheet_name='Sales_Data')

print(f"데이터 로드: {df_sales.shape}")

# 3. RFM 계산
reference_date = pd.to_datetime('2025-06-30')

rfm = df_sales.groupby('ykiho').agg({
    'sales_date': lambda x: (reference_date - pd.to_datetime(x).max()).days, # Recency
    'order_id': 'count', # Frequency
    'amount': 'sum'      # Monetary
}).rename(columns={
    'sales_date': 'Recency',
    'order_id': 'Frequency',
    'amount': 'Monetary'
})

# 4. 등급 산정 (Quantile)
r_labels = range(5, 0, -1) # 값이 작을수록 높은 점수
f_labels = range(1, 6)     # 값이 클수록 높은 점수
m_labels = range(1, 6)

rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=r_labels).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'], q=5, labels=f_labels).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=5, labels=m_labels).astype(int)

rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

# 5. 고객 세분화 함수
def segment_customer(score):
    if score >= 13: return 'VIP (최우수)'
    elif score >= 9: return 'Loyal (우수)'
    elif score >= 5: return 'Potential (잠재)'
    else: return 'Risk (이탈위험)'

rfm['Segment'] = rfm['RFM_Score'].apply(segment_customer)

# 6. 시각화 및 결과 확인
print("\n[고객 세분화 결과 요약]")
print(rfm['Segment'].value_counts())

plt.figure(figsize=(10, 6))
sns.countplot(x='Segment', data=rfm, order=['VIP (최우수)', 'Loyal (우수)', 'Potential (잠재)', 'Risk (이탈위험)'])
plt.title('고객 등급별 분포')
plt.show()

# 7. 저장
save_path = '../data/processed/client_rfm_result.csv'
rfm.to_csv(save_path, encoding='utf-8-sig')
print(f"분석 저장 완료: {save_path}")