-- 门店表 (stores) - 原pharmacies表
CREATE TABLE stores (
    store_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255)
);

-- 用户表 (users) - 角色更新
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('system_admin', 'store_manager', 'cashier')),
    store_id INT, -- 员工所属门店
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- 【新】员工工作日志表 (work_logs) - 整合点子二
CREATE TABLE work_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    store_id INT NOT NULL,
    clock_in_time TIMESTAMP WITH TIME ZONE, -- 上班打卡时间
    clock_out_time TIMESTAMP WITH TIME ZONE, -- 下班打卡时间
    notes TEXT, -- 备注
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- 【新】商品分类表 (product_categories)
CREATE TABLE product_categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- 【新】供应商表 (suppliers)
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_info TEXT
);

-- 商品表 (products) - 原drugs表，结构扩展
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL, -- Stock Keeping Unit，商品条码
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category_id INT,
    supplier_id INT,
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- 库存表 (inventory) - 结构不变，但意义更广
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    store_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    UNIQUE (product_id, store_id)
);

-- 【新】促销活动表 (promotions) - 整合点子三
CREATE TABLE promotions (
    promotion_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

-- 【新】促销商品关联表 (promotion_items)
CREATE TABLE promotion_items (
    id SERIAL PRIMARY KEY,
    promotion_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 销售单主表 (sales) - 记录每笔交易的总体信息
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    store_id INT NOT NULL,
    cashier_id INT NOT NULL,
    sale_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL, -- 最终支付总额
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (cashier_id) REFERENCES users(user_id)
);

-- 销售单详情表 (sale_items) - 记录每笔交易中包含的具体商品
CREATE TABLE sale_items (
    item_id SERIAL PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_per_unit DECIMAL(10, 2) NOT NULL, -- 销售时的单价（可能已应用折扣）
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);