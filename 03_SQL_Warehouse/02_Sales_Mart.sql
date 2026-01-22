/* 파일명: 02_Sales_Mart.sql
   설명: 제품별 매출 정보와 해당 제품을 사용하는 장비 정보를 매핑
*/

WITH Equipment_Mapping AS (
    -- 1. 제품(SKU)별 사용 가능한 장비 매핑
    SELECT
        SKU,
        GROUP_CONCAT(DISTINCT 장비명 ORDER BY 장비명 SEPARATOR ', ') AS compatible_equipments,
        GROUP_CONCAT(DISTINCT 장비대분류명 ORDER BY 장비대분류명 SEPARATOR ', ') AS equipment_category
    FROM product_equipment_mapping -- (구: 장비정보)
    GROUP BY SKU
),

Sales_Summary AS (
    -- 2. 제품별 평균 매입가 산출
    SELECT
        제품_SKU AS SKU,
        제품_이름 AS product_name,
        AVG(`매입가 (vat.포함)`) AS avg_purchase_price
    FROM sales_transaction_data -- (구: 장비시약매칭 or 매출테이블)
    GROUP BY 제품_SKU, 제품_이름
)

-- [최종] 매출 분석용 데이터셋
SELECT
    s.SKU,
    s.product_name,
    s.avg_purchase_price,
    e.compatible_equipments,
    e.equipment_category
FROM Sales_Summary s
    LEFT JOIN Equipment_Mapping e ON s.SKU = e.SKU;