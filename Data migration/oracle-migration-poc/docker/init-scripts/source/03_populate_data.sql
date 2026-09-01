-- Populate sample data for migration POC
-- Kept at 1,000 rows per main table so init finishes quickly in XE
-- Scale up by changing the loop bounds if you have more RAM/disk

SET SERVEROUTPUT ON SIZE UNLIMITED

-- Disable FK constraints for fast bulk load
ALTER TABLE ORDER_ITEMS DISABLE CONSTRAINT FK_ORDER_ITEMS_ORDER;
ALTER TABLE ORDER_ITEMS DISABLE CONSTRAINT FK_ORDER_ITEMS_PRODUCT;
ALTER TABLE ORDERS      DISABLE CONSTRAINT FK_ORDERS_CUSTOMER;
ALTER TABLE PAYMENTS    DISABLE CONSTRAINT FK_PAYMENTS_ORDER;

DECLARE
  v_count NUMBER := 0;
BEGIN
  -- ---------------------------------------------------------------
  -- CUSTOMERS  (1 000 rows)
  -- ---------------------------------------------------------------
  DBMS_OUTPUT.PUT_LINE('Inserting CUSTOMER records...');
  FOR i IN 1..1000 LOOP
    INSERT INTO CUSTOMER (
      CUSTOMER_ID, FIRST_NAME, LAST_NAME, EMAIL, PHONE,
      ADDRESS, CITY, STATE, ZIP_CODE, COUNTRY,
      REGISTRATION_DATE, STATUS
    ) VALUES (
      i,
      'First' || i,
      'Last'  || i,
      'customer' || i || '@example.com',
      '555-' || LPAD(MOD(i, 10000), 4, '0'),
      i || ' Main St',
      CASE MOD(i,5) WHEN 0 THEN 'New York' WHEN 1 THEN 'Los Angeles'
                    WHEN 2 THEN 'Chicago'  WHEN 3 THEN 'Houston' ELSE 'Phoenix' END,
      CASE MOD(i,5) WHEN 0 THEN 'NY' WHEN 1 THEN 'CA'
                    WHEN 2 THEN 'IL' WHEN 3 THEN 'TX' ELSE 'AZ' END,
      LPAD(MOD(i,100000), 5, '0'),
      'USA',
      SYSDATE - MOD(i,365),
      CASE WHEN MOD(i,10) = 0 THEN 'INACTIVE' ELSE 'ACTIVE' END
    );
  END LOOP;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('  1 000 CUSTOMER rows inserted.');

  -- ---------------------------------------------------------------
  -- PRODUCTS  (500 rows)
  -- ---------------------------------------------------------------
  DBMS_OUTPUT.PUT_LINE('Inserting PRODUCTS records...');
  FOR i IN 1..500 LOOP
    INSERT INTO PRODUCTS (
      PRODUCT_ID, PRODUCT_NAME, DESCRIPTION, CATEGORY,
      UNIT_PRICE, STOCK_QUANTITY, IS_ACTIVE
    ) VALUES (
      i,
      'Product ' || i,
      'Description for product ' || i,
      CASE MOD(i,10) WHEN 0 THEN 'Electronics' WHEN 1 THEN 'Clothing'
                     WHEN 2 THEN 'Books'        WHEN 3 THEN 'Home'
                     WHEN 4 THEN 'Toys'         WHEN 5 THEN 'Sports'
                     WHEN 6 THEN 'Food'         WHEN 7 THEN 'Beauty'
                     WHEN 8 THEN 'Automotive'   ELSE 'Other' END,
      ROUND(DBMS_RANDOM.VALUE(10, 1000), 2),
      ROUND(DBMS_RANDOM.VALUE(0,  1000)),
      CASE WHEN MOD(i,20) = 0 THEN 'N' ELSE 'Y' END
    );
  END LOOP;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('  500 PRODUCTS rows inserted.');

  -- ---------------------------------------------------------------
  -- ORDERS  (2 500 rows  — 2-3 per customer)
  -- ---------------------------------------------------------------
  DBMS_OUTPUT.PUT_LINE('Inserting ORDERS records...');
  FOR i IN 1..2500 LOOP
    INSERT INTO ORDERS (
      ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS,
      TOTAL_AMOUNT, SHIPPING_ADDRESS, SHIPPING_CITY,
      SHIPPING_STATE, SHIPPING_ZIP, PAYMENT_METHOD
    ) VALUES (
      i,
      MOD(i-1, 1000) + 1,
      SYSDATE - MOD(i, 730),
      CASE MOD(i,5) WHEN 0 THEN 'PENDING'  WHEN 1 THEN 'PROCESSING'
                    WHEN 2 THEN 'SHIPPED'  WHEN 3 THEN 'DELIVERED'
                    ELSE 'COMPLETED' END,
      ROUND(DBMS_RANDOM.VALUE(50, 5000), 2),
      i || ' Ship Ave',
      'City ' || MOD(i,100),
      'ST',
      LPAD(MOD(i,100000), 5, '0'),
      CASE MOD(i,3) WHEN 0 THEN 'CREDIT_CARD'
                    WHEN 1 THEN 'PAYPAL' ELSE 'DEBIT_CARD' END
    );
  END LOOP;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('  2 500 ORDERS rows inserted.');

  -- ---------------------------------------------------------------
  -- ORDER_ITEMS  (3 per order = 7 500 rows)
  -- ---------------------------------------------------------------
  DBMS_OUTPUT.PUT_LINE('Inserting ORDER_ITEMS records...');
  v_count := 0;
  FOR i IN 1..2500 LOOP
    FOR j IN 1..3 LOOP
      v_count := v_count + 1;
      INSERT INTO ORDER_ITEMS (
        ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID,
        QUANTITY, UNIT_PRICE, DISCOUNT_PERCENT, LINE_TOTAL
      ) VALUES (
        v_count,
        i,
        MOD(v_count-1, 500) + 1,
        ROUND(DBMS_RANDOM.VALUE(1, 5)),
        ROUND(DBMS_RANDOM.VALUE(10, 500), 2),
        CASE WHEN MOD(v_count,10) = 0 THEN ROUND(DBMS_RANDOM.VALUE(5,20),2) ELSE 0 END,
        ROUND(DBMS_RANDOM.VALUE(10, 2500), 2)
      );
    END LOOP;
  END LOOP;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('  7 500 ORDER_ITEMS rows inserted.');

  -- ---------------------------------------------------------------
  -- PAYMENTS  (2 per order = 5 000 rows)
  -- ---------------------------------------------------------------
  DBMS_OUTPUT.PUT_LINE('Inserting PAYMENTS records...');
  v_count := 0;
  FOR i IN 1..2500 LOOP
    FOR j IN 1..2 LOOP
      v_count := v_count + 1;
      INSERT INTO PAYMENTS (
        PAYMENT_ID, ORDER_ID, PAYMENT_DATE,
        AMOUNT, PAYMENT_METHOD, TRANSACTION_ID, PAYMENT_STATUS
      ) VALUES (
        v_count,
        i,
        SYSDATE - MOD(i, 730),
        ROUND(DBMS_RANDOM.VALUE(25, 2500), 2),
        CASE MOD(v_count,3) WHEN 0 THEN 'CREDIT_CARD'
                            WHEN 1 THEN 'PAYPAL' ELSE 'DEBIT_CARD' END,
        'TXN-' || LPAD(v_count, 10, '0'),
        CASE MOD(v_count,20) WHEN 0 THEN 'PENDING'
                             WHEN 1 THEN 'FAILED' ELSE 'COMPLETED' END
      );
    END LOOP;
  END LOOP;
  COMMIT;
  DBMS_OUTPUT.PUT_LINE('  5 000 PAYMENTS rows inserted.');

  DBMS_OUTPUT.PUT_LINE('========================================');
  DBMS_OUTPUT.PUT_LINE('Data population complete!');
  DBMS_OUTPUT.PUT_LINE('  CUSTOMER:    1 000 rows');
  DBMS_OUTPUT.PUT_LINE('  PRODUCTS:      500 rows');
  DBMS_OUTPUT.PUT_LINE('  ORDERS:      2 500 rows');
  DBMS_OUTPUT.PUT_LINE('  ORDER_ITEMS: 7 500 rows');
  DBMS_OUTPUT.PUT_LINE('  PAYMENTS:    5 000 rows');
  DBMS_OUTPUT.PUT_LINE('  TOTAL:      16 500 rows');
  DBMS_OUTPUT.PUT_LINE('========================================');
END;
/

-- Re-enable FK constraints
ALTER TABLE ORDER_ITEMS ENABLE CONSTRAINT FK_ORDER_ITEMS_ORDER;
ALTER TABLE ORDER_ITEMS ENABLE CONSTRAINT FK_ORDER_ITEMS_PRODUCT;
ALTER TABLE ORDERS      ENABLE CONSTRAINT FK_ORDERS_CUSTOMER;
ALTER TABLE PAYMENTS    ENABLE CONSTRAINT FK_PAYMENTS_ORDER;

-- Note: GATHER_SCHEMA_STATS skipped intentionally.
-- On Oracle XE 21c in Docker, background job crashes (ORA-600 [12803])
-- can abort the stats call. num_rows in user_tables may read 0 but
-- COUNT(*) on the actual tables will return the correct values.

COMMIT;
