/* 파일명: 03_Equipment_Status.sql
   설명: SKU와 장비 모델명 간의 관계를 정제하고 유효 데이터 필터링
*/

WITH Valid_SKU_Mapping AS (
    -- 1. 중복 제거된 SKU-장비 매핑 테이블
    SELECT DISTINCT * FROM sku_equipment_matching -- (구: sku매칭)
),

Equipment_Enrichment AS (
    -- 2. 장비 대분류 정보 추가 및 특정 조건 필터링
    SELECT DISTINCT
        m.장비대분류명 AS category,
        e.장비_SKU,
        e.장비명 AS model_name,
        m.SKU,
        e.제품명 AS product_name
    FROM equipment_list e
        LEFT JOIN Valid_SKU_Mapping m USING(sku)
        LEFT JOIN client_equipment_status s ON s.장비_SKU = m.장비_SKU
    WHERE
        -- 특정 장비 제외 로직 (예: 구형 모델 필터링)
        NOT (e.장비명 = 'Legacy_Model_A' AND m.장비대분류명 = 'Urinalysis')
        OR e.장비명 IS NOT NULL
),

Aggregated_Equipment AS (
    -- 3. SKU별 장비 리스트 통합
    SELECT
        SKU,
        GROUP_CONCAT(DISTINCT model_name ORDER BY model_name SEPARATOR ', ') AS model_list,
        GROUP_CONCAT(DISTINCT category ORDER BY category SEPARATOR ', ') AS category_list
    FROM Equipment_Enrichment
    GROUP BY SKU
)

-- [최종] 정제된 장비 마스터
SELECT
    base.*,
    agg.model_list,
    agg.category_list
FROM Equipment_Enrichment base
    JOIN Aggregated_Equipment agg USING(SKU);