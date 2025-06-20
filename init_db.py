#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import psycopg2
from werkzeug.security import generate_password_hash

def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='gaussdb',
        password='Lxh@26957'
    )

def init_all_tables():
    """创建所有必要的数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔧 创建数据库表...")
    
    tables_sql = """
    -- 门店表 (stores)
    DROP TABLE IF EXISTS work_logs CASCADE;
    DROP TABLE IF EXISTS sale_items CASCADE;
    DROP TABLE IF EXISTS sales CASCADE;
    DROP TABLE IF EXISTS promotion_items CASCADE;
    DROP TABLE IF EXISTS promotions CASCADE;
    DROP TABLE IF EXISTS inventory CASCADE;
    DROP TABLE IF EXISTS products CASCADE;
    DROP TABLE IF EXISTS product_categories CASCADE;
    DROP TABLE IF EXISTS suppliers CASCADE;
    DROP TABLE IF EXISTS users CASCADE;
    DROP TABLE IF EXISTS stores CASCADE;

    CREATE TABLE stores (
        store_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255)
    );
    
    -- 用户表 (users)
    CREATE TABLE users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'cashier')),
        store_id INT,
        FOREIGN KEY (store_id) REFERENCES stores(store_id)
    );
    
    -- 员工工作日志表 (work_logs)
    CREATE TABLE work_logs (
        log_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        store_id INT NOT NULL,
        clock_in_time TIMESTAMP WITH TIME ZONE,
        clock_out_time TIMESTAMP WITH TIME ZONE,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (store_id) REFERENCES stores(store_id)
    );
    
    -- 商品分类表 (product_categories)
    CREATE TABLE product_categories (
        category_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE
    );
    
    -- 供应商表 (suppliers)
    CREATE TABLE suppliers (
        supplier_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        contact_info TEXT
    );
    
    -- 商品表 (products)
    CREATE TABLE products (
        product_id SERIAL PRIMARY KEY,
        sku VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        category_id INT,
        supplier_id INT,
        FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    );
    
    -- 库存表 (inventory)
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
    
    -- 促销活动表 (promotions)
    CREATE TABLE promotions (
        promotion_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
        discount_value DECIMAL(10, 2) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL
    );
    
    -- 促销商品关联表 (promotion_items)
    CREATE TABLE promotion_items (
        id SERIAL PRIMARY KEY,
        promotion_id INT NOT NULL,
        product_id INT NOT NULL,
        FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    
    -- 销售单主表 (sales)
    CREATE TABLE sales (
        sale_id SERIAL PRIMARY KEY,
        store_id INT NOT NULL,
        cashier_id INT NOT NULL,
        sale_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (cashier_id) REFERENCES users(user_id)
    );
    
    -- 销售单详情表 (sale_items)
    CREATE TABLE sale_items (
        item_id SERIAL PRIMARY KEY,
        sale_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        price_per_unit DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """
    
    cursor.execute(tables_sql)
    conn.commit()
    print("✅ 数据库表创建成功！")
    
    cursor.close()
    conn.close()

def insert_demo_data():
    """插入演示数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("📊 插入演示数据...")
    
    try:
        # 插入门店数据
        stores_data = [
            ('总店', '北京市朝阳区建国路1号'),
            ('分店A', '北京市海淀区中关村大街100号'),
            ('分店B', '北京市西城区西单大街200号')
        ]
        
        for store_name, address in stores_data:
            cursor.execute(
                "INSERT INTO stores (name, address) VALUES (%s, %s)",
                (store_name, address)
            )
        
        # 插入用户数据
        users_data = [
            ('admin', 'admin123', 'admin', 1),
            ('manager1', 'manager123', 'manager', 1),
            ('cashier1', 'cashier123', 'cashier', 1),
            ('cashier2', 'cashier123', 'cashier', 2)
        ]
        
        for username, password, role, store_id in users_data:
            password_hash = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, store_id) VALUES (%s, %s, %s, %s)",
                (username, password_hash, role, store_id)
            )
        
        # 插入商品分类
        categories_data = ['食品', '饮料', '日用品', '文具', '电子产品']
        for category in categories_data:
            cursor.execute(
                "INSERT INTO product_categories (name) VALUES (%s)",
                (category,)
            )
        
        # 插入供应商数据
        suppliers_data = [
            ('供应商A', '联系人：张三，电话：13800138001'),
            ('供应商B', '联系人：李四，电话：13800138002'),
            ('供应商C', '联系人：王五，电话：13800138003')
        ]
        
        for supplier_name, contact_info in suppliers_data:
            cursor.execute(
                "INSERT INTO suppliers (name, contact_info) VALUES (%s, %s)",
                (supplier_name, contact_info)
            )
        
        # 插入商品数据
        products_data = [
            ('FOOD001', '苹果', '新鲜红苹果', 1, 1),
            ('FOOD002', '香蕉', '进口香蕉', 1, 1),
            ('DRINK001', '可乐', '经典可口可乐', 2, 2),
            ('DRINK002', '矿泉水', '天然矿泉水', 2, 2),
            ('DAILY001', '牙刷', '软毛牙刷', 3, 3)
        ]
        
        for sku, name, description, category_id, supplier_id in products_data:
            cursor.execute(
                "INSERT INTO products (sku, name, description, category_id, supplier_id) VALUES (%s, %s, %s, %s, %s)",
                (sku, name, description, category_id, supplier_id)
            )
        
        # 插入库存数据
        inventory_data = [
            (1, 1, 100, 5.99),  # 苹果在总店
            (2, 1, 80, 3.99),   # 香蕉在总店
            (3, 1, 50, 2.99),   # 可乐在总店
            (4, 1, 200, 1.99),  # 矿泉水在总店
            (5, 1, 30, 12.99),  # 牙刷在总店
        ]
        
        for product_id, store_id, quantity, price in inventory_data:
            cursor.execute(
                "INSERT INTO inventory (product_id, store_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (product_id, store_id, quantity, price)
            )
        
        conn.commit()
        print("✅ 演示数据插入成功！")
        
    except Exception as e:
        print(f"❌ 插入数据失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    print("🚀 初始化超市管理系统数据库")
    print("=" * 40)
    
    try:
        # 创建表
        init_all_tables()
        
        # 插入演示数据
        insert_demo_data()
        
        print("=" * 40)
        print("✅ 数据库初始化完成！")
        print("🎯 现在可以启动后端服务器了")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    return True

if __name__ == '__main__':
    main() 