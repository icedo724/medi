import pandas as pd
import os
import glob

# 1. 경로 설정
input_dir = '../data/raw'
output_dir = '../data/processed'
os.makedirs(output_dir, exist_ok=True)

# 2. 컬럼명 한글 매핑 (사용자 파일 기반 확장)
col_map = {
    'ykiho': '암호화된 요양기호',
    'yadmNm': '병원명',
    'addr': '주소',
    'clCd': '종별코드',
    'clCdNm': '종별코드명',
    'dgsbjtCdNm': '진료과목코드명',
    'dgsbjtCd': '진료과목코드',
    'ddt': '의사수',
    'mdeptSdrCnt': '전문과목별 전문의 수',
    'grade': '간호등급',
    'gradeNm': '구분 코드명'
}

# 3. 파일 병합 로직
target_pattern = os.path.join(input_dir, "hospital_detail_*.csv")
file_list = glob.glob(target_pattern)

output_excel = os.path.join(output_dir, 'hospital_detail_combined.xlsx')

if not file_list:
    print("처리할 CSV 파일이 없습니다.")
else:
    print(f"총 {len(file_list)}개의 파일을 병합합니다.")

    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        for file_path in file_list:
            # 파일명 파싱 (예: hospital_detail_equip_info.csv -> equip_info)
            filename = os.path.basename(file_path)
            sheet_name = filename.replace('hospital_detail_', '').replace('.csv', '')

            # 엑셀 시트 이름 길이 제한 (31자)
            sheet_name = sheet_name[:31]

            try:
                # 모든 데이터를 문자열로 읽어서 데이터 손실 방지
                df = pd.read_csv(file_path, dtype=str)

                # 컬럼명 변경
                df.rename(columns=col_map, inplace=True)

                # 시트에 쓰기
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✅ 시트 생성: {sheet_name} (행: {len(df)})")

            except Exception as e:
                print(f"❌ 실패 ({filename}): {e}")

    print(f"\n모든 작업 완료. 결과 파일: {output_excel}")