-- Create sample schema for migration POC
-- Runs as migration_user in XEPDB1 (gvenzl runs APP_USER scripts automatically)

-- Drop tables if they exist (idempotent re-runs)
-- Each statement wrapped in its own exception handler so one failure
-- does not abort the whole block.
BEGIN
  FOR t IN (SELECT table_name FROM user_tables) LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP TABLE "' || t.table_name || '" CASCADE CONSTRAINTS PURGE';
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

-- Drop sequences if they exist
BEGIN
  FOR s IN (SELECT sequence_name FROM user_sequences) LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP SEQUENCE "' || s.sequence_name || '"';
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

-- ----------------------------------------------------------------
-- CUSTOMER
-- ----------------------------------------------------------------
CREATE TABLE CUSTOMER (
  CUSTOMER_ID       NUMBER(10)    PRIMARY KEY,
  FIRST_NAME        VARCHAR2(50)  NOT NULL,
  LAST_NAME         VARCHAR2(50)  NOT NULL,
  EMAIL             VARCHAR2(100) UNIQUE NOT NULL,
  PHONE             VARCHAR2(20),
  ADDRESS           VARCHAR2(200),
  CITY              VARCHAR2(50),
  STATE             VARCHAR2(50),
  ZIP_CODE          VARCHAR2(10),
  COUNTRY           VARCHAR2(50)  DEFAULT 'USA',
  REGISTRATION_DATE DATE          DEFAULT SYSDATE,
  LAST_LOGIN_DATE   DATE,
  STATUS            VARCHAR2(20)  DEFAULT 'ACTIVE',
  CREATED_AT        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  UPDATED_AT        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------
-- PRODUCTS
-- ----------------------------------------------------------------
CREATE TABLE PRODUCTS (
  PRODUCT_ID      NUMBER(10)    PRIMARY KEY,
  PRODUCT_NAME    VARCHAR2(100) NOT NULL,
  DESCRIPTION     VARCHAR2(500),
  CATEGORY        VARCHAR2(50),
  UNIT_PRICE      NUMBER(10,2)  NOT NULL,
  STOCK_QUANTITY  NUMBER(10)    DEFAULT 0,
  SUPPLIER_ID     NUMBER(10),
  IS_ACTIVE       CHAR(1)       DEFAULT 'Y',
  CREATED_AT      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  UPDATED_AT      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------
-- ORDERS
-- ----------------------------------------------------------------
CREATE TABLE ORDERS (
  ORDER_ID          NUMBER(10)    PRIMARY KEY,
  CUSTOMER_ID       NUMBER(10)    NOT NULL,
  ORDER_DATE        DATE          DEFAULT SYSDATE,
  SHIP_DATE         DATE,
  DELIVERY_DATE     DATE,
  ORDER_STATUS      VARCHAR2(20)  DEFAULT 'PENDING',
  TOTAL_AMOUNT      NUMBER(12,2),
  SHIPPING_ADDRESS  VARCHAR2(200),
  SHIPPING_CITY     VARCHAR2(50),
  SHIPPING_STATE    VARCHAR2(50),
  SHIPPING_ZIP      VARCHAR2(10),
  PAYMENT_METHOD    VARCHAR2(20),
  CREATED_AT        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  UPDATED_AT        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_ORDERS_CUSTOMER FOREIGN KEY (CUSTOMER_ID)
    REFERENCES CUSTOMER(CUSTOMER_ID)
);

-- ----------------------------------------------------------------
-- ORDER_ITEMS
-- ----------------------------------------------------------------
CREATE TABLE ORDER_ITEMS (
  ORDER_ITEM_ID     NUMBER(10)   PRIMARY KEY,
  ORDER_ID          NUMBER(10)   NOT NULL,
  PRODUCT_ID        NUMBER(10)   NOT NULL,
  QUANTITY          NUMBER(5)    NOT NULL,
  UNIT_PRICE        NUMBER(10,2) NOT NULL,
  DISCOUNT_PERCENT  NUMBER(5,2)  DEFAULT 0,
  LINE_TOTAL        NUMBER(12,2),
  CREATED_AT        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_ORDER_ITEMS_ORDER   FOREIGN KEY (ORDER_ID)
    REFERENCES ORDERS(ORDER_ID) ON DELETE CASCADE,
  CONSTRAINT FK_ORDER_ITEMS_PRODUCT FOREIGN KEY (PRODUCT_ID)
    REFERENCES PRODUCTS(PRODUCT_ID)
);

-- ----------------------------------------------------------------
-- PAYMENTS
-- ----------------------------------------------------------------
CREATE TABLE PAYMENTS (
  PAYMENT_ID      NUMBER(10)    PRIMARY KEY,
  ORDER_ID        NUMBER(10)    NOT NULL,
  PAYMENT_DATE    DATE          DEFAULT SYSDATE,
  AMOUNT          NUMBER(12,2)  NOT NULL,
  PAYMENT_METHOD  VARCHAR2(20),
  TRANSACTION_ID  VARCHAR2(100) UNIQUE,
  PAYMENT_STATUS  VARCHAR2(20)  DEFAULT 'COMPLETED',
  CREATED_AT      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FK_PAYMENTS_ORDER FOREIGN KEY (ORDER_ID)
    REFERENCES ORDERS(ORDER_ID)
);

-- ----------------------------------------------------------------
-- Sequences
-- ----------------------------------------------------------------
CREATE SEQUENCE SEQ_CUSTOMER_ID   START WITH 1 INCREMENT BY 1 NOCACHE NOORDER;
CREATE SEQUENCE SEQ_PRODUCT_ID    START WITH 1 INCREMENT BY 1 NOCACHE NOORDER;
CREATE SEQUENCE SEQ_ORDER_ID      START WITH 1 INCREMENT BY 1 NOCACHE NOORDER;
CREATE SEQUENCE SEQ_ORDER_ITEM_ID START WITH 1 INCREMENT BY 1 NOCACHE NOORDER;
CREATE SEQUENCE SEQ_PAYMENT_ID    START WITH 1 INCREMENT BY 1 NOCACHE NOORDER;

-- ----------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------
CREATE INDEX IDX_CUSTOMER_EMAIL    ON CUSTOMER(EMAIL);
CREATE INDEX IDX_CUSTOMER_STATUS   ON CUSTOMER(STATUS);
CREATE INDEX IDX_ORDERS_CUSTOMER   ON ORDERS(CUSTOMER_ID);
CREATE INDEX IDX_ORDERS_DATE       ON ORDERS(ORDER_DATE);
CREATE INDEX IDX_ORDERS_STATUS     ON ORDERS(ORDER_STATUS);
CREATE INDEX IDX_ORDER_ITEMS_ORDER ON ORDER_ITEMS(ORDER_ID);
CREATE INDEX IDX_ORDER_ITEMS_PROD  ON ORDER_ITEMS(PRODUCT_ID);
CREATE INDEX IDX_PAYMENTS_ORDER    ON PAYMENTS(ORDER_ID);
CREATE INDEX IDX_PAYMENTS_STATUS   ON PAYMENTS(PAYMENT_STATUS);

-- ----------------------------------------------------------------
-- View
-- ----------------------------------------------------------------
CREATE OR REPLACE VIEW V_CUSTOMER_ORDERS AS
SELECT
  c.CUSTOMER_ID,
  c.FIRST_NAME || ' ' || c.LAST_NAME AS CUSTOMER_NAME,
  c.EMAIL,
  o.ORDER_ID,
  o.ORDER_DATE,
  o.ORDER_STATUS,
  o.TOTAL_AMOUNT
FROM CUSTOMER c
LEFT JOIN ORDERS o ON c.CUSTOMER_ID = o.CUSTOMER_ID;

COMMIT;
