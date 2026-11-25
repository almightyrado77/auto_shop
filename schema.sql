CREATE TABLE IF NOT EXISTS users (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         VARCHAR2(255) NOT NULL UNIQUE,
    password_hash VARCHAR2(255) NOT NULL,
    name          VARCHAR2(100) NOT NULL,
    phone         VARCHAR2(30),
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id NUMBER NOT NULL REFERENCES categories (id),
    name        VARCHAR2(200) NOT NULL,
    description VARCHAR2(2000),
    price       NUMBER(10, 2) NOT NULL CHECK (price >= 0),
    stock       NUMBER(6) DEFAULT 0 NOT NULL CHECK (stock >= 0),
    image       VARCHAR2(255)
);

CREATE TABLE IF NOT EXISTS product_attributes (
    id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id NUMBER NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    attr_name  VARCHAR2(100) NOT NULL,
    attr_value VARCHAR2(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    NUMBER NOT NULL REFERENCES users (id),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    status     VARCHAR2(20) DEFAULT 'new' NOT NULL,
    total      NUMBER(10, 2) NOT NULL,
    address    VARCHAR2(500) NOT NULL,
    phone      VARCHAR2(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id   NUMBER NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_id NUMBER NOT NULL REFERENCES products (id),
    quantity   NUMBER(4) NOT NULL CHECK (quantity > 0),
    unit_price NUMBER(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS part_requests (
    id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      NUMBER REFERENCES orders (id),
    user_id       NUMBER REFERENCES users (id),
    contact_name  VARCHAR2(100) NOT NULL,
    contact_email VARCHAR2(255) NOT NULL,
    contact_phone VARCHAR2(30),
    car_make      VARCHAR2(50) NOT NULL,
    car_model     VARCHAR2(50) NOT NULL,
    car_year      NUMBER(4),
    vin           VARCHAR2(17),
    description   VARCHAR2(2000) NOT NULL,
    status        VARCHAR2(20) DEFAULT 'new' NOT NULL,
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
)