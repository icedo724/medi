import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, pearsonr, f_oneway
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import platform
import warnings

# --- 1. 환경 설정 ---
# 경고 무시
warnings.filterwarnings('ignore')

# OS별 한글 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # Mac
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False


def get_resource_path(relative_path):
    """
    개발 환경(Python 스크립트)과 배포 환경(PyInstaller EXE)
    모두에서 파일 경로를 올바르게 찾아주는 함수
    """
    try:
        # PyInstaller로 빌드된 경우 임시 경로(_MEIPASS) 사용
        base_path = sys._MEIPASS
    except AttributeError:
        # 일반 파이썬 실행 시 현재 경로 사용
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- 2. 데이터 로드 함수 ---
def load_dataset():
    """
    데이터 파일을 로드합니다.
    1순위: 개발용 폴더 (../data/processed/)
    2순위: 배포용 번들 (EXE 내부)
    """
    print("\n[System] 데이터베이스를 로딩 중입니다...")

    # 개발 환경 경로 (상위 폴더 참조)
    dev_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed', 'analysis_mart.xlsx')

    # 배포 환경 경로 (같은 폴더 혹은 번들 내부)
    bundled_path = get_resource_path('analysis_data.xlsx')

    target_path = None

    if os.path.exists(dev_path):
        target_path = dev_path
    elif os.path.exists(bundled_path):
        target_path = bundled_path
    else:
        # 로컬 테스트용 (같은 폴더에 파일이 있을 경우)
        local_path = 'analysis_mart.xlsx'
        if os.path.exists(local_path):
            target_path = local_path

    if target_path is None:
        print("❌ 오류: 데이터 파일을 찾을 수 없습니다.")
        print(f"확인된 경로:\n1) {dev_path}\n2) {bundled_path}")
        return None

    try:
        # 엑셀의 모든 시트를 딕셔너리 형태로 로드
        df_dict = pd.read_excel(target_path, sheet_name=None)
        print(f"✅ 데이터 로드 완료! (파일: {os.path.basename(target_path)})")
        print(f"   포함된 시트: {list(df_dict.keys())}")
        return df_dict
    except Exception as e:
        print(f"❌ 데이터 로드 중 치명적 오류 발생: {e}")
        return None


# --- 3. 분석 함수들 ---

def run_chi2_test(df):
    """카이제곱 검정: 두 범주형 변수 간의 독립성 검정"""
    print("\n--- 📊 카이제곱 검정 (Chi-Square Test) ---")
    print("설명: 두 범주형 변수(예: 장비보유여부 vs 등급)가 서로 연관성이 있는지 확인합니다.")

    # 범주형 컬럼만 추출
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if len(cat_cols) < 2:
        print("⚠️ 분석할 범주형 변수가 부족합니다. (최소 2개 필요)")
        return

    print(f"\n[분석 가능 변수 목록]\n{cat_cols}")

    try:
        col1 = input("첫 번째 변수명을 입력하세요: ").strip()
        if col1 not in cat_cols: raise ValueError("존재하지 않는 변수입니다.")

        col2 = input("두 번째 변수명을 입력하세요: ").strip()
        if col2 not in cat_cols: raise ValueError("존재하지 않는 변수입니다.")

        # 교차표 생성
        contingency_table = pd.crosstab(df[col1], df[col2])
        print("\n[교차표 (Observed)]")
        print(contingency_table)

        # 검정 수행
        chi2, p, dof, expected = chi2_contingency(contingency_table)

        print(f"\n[검정 결과]")
        print(f" - Chi2 통계량: {chi2:.4f}")
        print(f" - P-value: {p:.4f}")

        if p < 0.05:
            print("🔴 결과 해석: P-value < 0.05 이므로, 두 변수는 통계적으로 유의미한 연관성이 **있습니다**.")
        else:
            print("🔵 결과 해석: P-value >= 0.05 이므로, 두 변수는 서로 독립적입니다 (연관성 없음).")

        # 시각화
        plt.figure(figsize=(10, 6))
        sns.heatmap(contingency_table, annot=True, fmt='d', cmap='YlGnBu')
        plt.title(f'Chi-Square Heatmap: {col1} vs {col2}')
        plt.show()

    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")


def run_anova_test(df):
    """분산 분석(ANOVA): 범주형 그룹에 따른 수치형 변수의 평균 차이 검정"""
    print("\n--- 📊 분산 분석 (One-way ANOVA) ---")
    print("설명: 그룹(예: 등급) 간에 수치(예: 매출액)의 평균 차이가 있는지 확인합니다.")

    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not cat_cols or not num_cols:
        print("⚠️ 변수가 부족합니다. (범주형 1개, 수치형 1개 이상 필요)")
        return

    print(f"\n[그룹 변수(범주형)]: {cat_cols}")
    print(f"[값 변수(수치형)]: {num_cols}")

    try:
        group_col = input("그룹을 나눌 변수(예: 등급)를 입력하세요: ").strip()
        if group_col not in cat_cols: raise ValueError("존재하지 않는 그룹 변수입니다.")

        value_col = input("평균을 비교할 변수(예: 매출)를 입력하세요: ").strip()
        if value_col not in num_cols: raise ValueError("존재하지 않는 수치 변수입니다.")

        # 그룹별 데이터 준비
        groups = [group[value_col].dropna() for name, group in df.groupby(group_col)]

        if len(groups) < 2:
            print("⚠️ 비교할 그룹이 2개 미만입니다.")
            return

        # 검정 수행
        f_stat, p_val = f_oneway(*groups)

        print(f"\n[검정 결과]")
        print(f" - F-statistic: {f_stat:.4f}")
        print(f" - P-value: {p_val:.4f}")

        if p_val < 0.05:
            print(f"🔴 결과 해석: 그룹 간 '{value_col}'의 평균 차이가 통계적으로 **유의미합니다**.")
        else:
            print(f"🔵 결과 해석: 그룹 간 평균 차이가 없다고 볼 수 있습니다.")

        # 시각화 (Boxplot)
        plt.figure(figsize=(10, 6))
        sns.boxplot(x=group_col, y=value_col, data=df)
        plt.title(f'ANOVA Boxplot: {value_col} by {group_col}')
        plt.show()

    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")


def run_correlation_analysis(df):
    """상관관계 분석: 두 수치형 변수 간의 관계"""
    print("\n--- 📊 상관관계 분석 (Pearson Correlation) ---")

    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    if len(num_cols) < 2:
        print("⚠️ 수치형 변수가 2개 이상 필요합니다.")
        return

    print(f"\n[수치형 변수 목록]\n{num_cols}")

    try:
        col1 = input("변수 1: ").strip()
        col2 = input("변수 2: ").strip()

        if col1 not in num_cols or col2 not in num_cols:
            raise ValueError("잘못된 변수명입니다.")

        # 결측치 제거 후 계산
        temp_df = df[[col1, col2]].dropna()
        coef, p_val = pearsonr(temp_df[col1], temp_df[col2])

        print(f"\n[분석 결과]")
        print(f" - 상관계수(r): {coef:.4f}")
        print(f" - P-value: {p_val:.4f}")

        if abs(coef) > 0.7:
            strength = "매우 강한"
        elif abs(coef) > 0.5:
            strength = "강한"
        elif abs(coef) > 0.3:
            strength = "뚜렷한"
        else:
            strength = "약한"

        direction = "양(+)" if coef > 0 else "음(-)"

        print(f"📝 해석: 두 변수는 **{strength} {direction}의 상관관계**를 가집니다.")

        # 시각화 (Scatter)
        plt.figure(figsize=(8, 6))
        sns.regplot(x=col1, y=col2, data=temp_df)
        plt.title(f'Correlation: {col1} vs {col2}')
        plt.show()

    except Exception as e:
        print(f"❌ 오류: {e}")


# --- 4. 메인 실행 루프 ---
def main():
    print("===========================================")
    print("   🏥 병원 영업 데이터 분석 솔루션 v2.0   ")
    print("   (Data Load -> Analysis -> Visualization)")
    print("===========================================")

    # 데이터 로드
    df_dict = load_dataset()
    if df_dict is None:
        input("엔터 키를 누르면 종료합니다...")
        return

    while True:
        print("\n[메인 메뉴]")
        print("1. 데이터셋 선택 및 확인")
        print("2. 카이제곱 검정 (장비-등급 연관성)")
        print("3. 분산 분석 (ANOVA, 그룹별 매출차이)")
        print("4. 상관관계 분석 (RFM 지표 관계)")
        print("Q. 종료")

        choice = input(">> 선택: ").strip().upper()

        if choice == '1':
            print("\n[현재 로드된 시트 목록]")
            for i, sheet in enumerate(df_dict.keys()):
                print(f"{i + 1}. {sheet} (행: {len(df_dict[sheet])}개)")

        elif choice in ['2', '3', '4']:
            # 분석할 시트 선택
            sheet_name = input(f"분석할 시트 이름을 입력하세요 (예: {list(df_dict.keys())[0]}): ").strip()
            if sheet_name in df_dict:
                target_df = df_dict[sheet_name]
                if choice == '2':
                    run_chi2_test(target_df)
                elif choice == '3':
                    run_anova_test(target_df)
                elif choice == '4':
                    run_correlation_analysis(target_df)
            else:
                print("⚠️ 잘못된 시트 이름입니다.")

        elif choice == 'Q':
            print("프로그램을 종료합니다. 감사합니다.")
            break
        else:
            print("⚠️ 올바른 번호를 입력해주세요.")


if __name__ == "__main__":
    main()