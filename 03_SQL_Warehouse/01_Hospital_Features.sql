/* 파일명: 01_Hospital_Features.sql
   설명: 병원별 인프라(의사, 장비, 시설) 정보를 요약하여 Feature Table 생성
   작성일: 2026-01-22
*/

WITH Doctor_Stats AS (
    -- 1. 진료과목별 의사 수 집계 및 문자열 병합
    -- 예: "내과(5), 정형외과(3)"
    SELECT
        `암호화된 요양기호` AS ykiho,
        출력명 AS hospital_name,
        GROUP_CONCAT(
            CONCAT(진료과목코드명, '(', 의사수, ')')
            ORDER BY 진료과목코드 ASC SEPARATOR ', '
        ) AS doctors_by_subject
    FROM hospital_detail_dgsbjt_info
    GROUP BY `암호화된 요양기호`, 출력명
),

Equipment_Stats AS (
    -- 2. 보유 장비 목록 및 대수 집계
    SELECT
        `암호화된 요양기호` AS ykiho,
        GROUP_CONCAT(
            CONCAT(장비명, '(', 장비대수, ')')
            ORDER BY 장비코드 ASC SEPARATOR ', '
        ) AS equipment_list
    FROM hospital_detail_equip_info
    GROUP BY `암호화된 요양기호`
),

Nursing_Grade AS (
    -- 3. 간호 등급 정보 집계
    SELECT
        `암호화된 요양기호` AS ykiho,
        GROUP_CONCAT(
            CONCAT(`구분 코드명`, '(', 간호등급, ')')
            ORDER BY `구분 코드` ASC SEPARATOR ', '
        ) AS nursing_grade_info
    FROM hospital_detail_nursing_info
    GROUP BY `암호화된 요양기호`
),

Key_Equipment_Flag AS (
    -- 4. 핵심 장비(예: 투석기) 보유 여부 플래그 생성
    SELECT
        `암호화된 요양기호` AS ykiho,
        SUM(장비대수) AS total_equip_count,
        CASE
            WHEN SUM(CASE WHEN 장비명 LIKE '%인공신장기%' THEN 1 ELSE 0 END) > 0
            THEN 'Y' ELSE 'N'
        END AS has_dialysis_machine
    FROM hospital_detail_equip_info
    GROUP BY `암호화된 요양기호`
),

Specialist_Count AS (
    -- 5. 주요 진료과(내과, 가정의학과 등) 전문의 수 추출
    SELECT
        `암호화된 요양기호` AS ykiho,
        SUM(CASE WHEN 진료과목코드명 = '가정의학과' THEN `전문과목별 전문의 수` ELSE 0 END) AS cnt_family_med,
        SUM(CASE WHEN 진료과목코드명 = '내과' THEN `전문과목별 전문의 수` ELSE 0 END) AS cnt_internal_med,
        SUM(CASE WHEN 진료과목코드명 = '비뇨의학과' THEN `전문과목별 전문의 수` ELSE 0 END) AS cnt_urology
    FROM hospital_detail_sdr_info
    GROUP BY `암호화된 요양기호`
)

-- [최종] 분석용 마스터 테이블 생성
SELECT
    a.ykiho,
    a.hospital_name,
    b.doctors_by_subject,
    c.equipment_list,
    d.nursing_grade_info,
    e.total_equip_count,
    e.has_dialysis_machine,
    f.cnt_family_med,
    f.cnt_internal_med,
    f.cnt_urology,
    g.`상급 입원실(병상수)` AS vip_beds,
    g.`수술실(병상수)` AS operating_rooms
FROM Doctor_Stats a
    LEFT JOIN client_basic_info m ON a.ykiho = m.ykiho -- 거래처 마스터와 조인
    LEFT JOIN Doctor_Stats b ON a.ykiho = b.ykiho
    LEFT JOIN Equipment_Stats c ON a.ykiho = c.ykiho
    LEFT JOIN Nursing_Grade d ON a.ykiho = d.ykiho
    LEFT JOIN Key_Equipment_Flag e ON a.ykiho = e.ykiho
    LEFT JOIN Specialist_Count f ON a.ykiho = f.ykiho
    LEFT JOIN hospital_detail_facility_info g ON a.ykiho = g.`암호화된 요양기호`;