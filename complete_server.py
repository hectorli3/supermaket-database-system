#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整版超市管理系统后端服务器
支持用户认证、门店管理、商品管理、库存管理、销售管理等全部功能
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from datetime import datetime, date
import pytz
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

CORS(app)
jwt = JWTManager(app)

# 时区转换函数
def format_datetime_with_timezone(dt):
    """将UTC时间转换为北京时间并格式化"""
    if dt is None:
        return None
    
    # 如果datetime对象没有时区信息，假设它是UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # 转换为北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = dt.astimezone(beijing_tz)
    
    # 格式化为字符串
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S')

# 数据库连接函数
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='gaussdb',
        password='Lxh@26957'
    )

def log_action(user_id, action, details, conn=None):
    """记录用户操作日志"""
    try:
        close_conn = False
        if conn is None:
            conn = get_db_connection()
            close_conn = True
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO work_logs (user_id, action, details) VALUES (%s, %s, %s)",
            (user_id, action, details)
        )
        
        if close_conn:
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"记录日志失败: {str(e)}")

# 初始化所有数据库表
def init_all_tables():
    """创建所有必要的数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables_sql = """
    -- 门店表 (stores)
    CREATE TABLE IF NOT EXISTS stores (
        store_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 用户表 (users)
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('system_admin', 'store_manager', 'cashier')),
        store_id INT,
        FOREIGN KEY (store_id) REFERENCES stores(store_id)
    );
    
    -- 员工工作日志表 (work_logs)
    CREATE TABLE IF NOT EXISTS work_logs (
        log_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        action VARCHAR(100) NOT NULL,
        details TEXT,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
    -- 商品分类表 (product_categories)
    CREATE TABLE IF NOT EXISTS product_categories (
        category_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 供应商表 (suppliers)
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        contact_info TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 商品表 (products)
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        sku VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        category_id INT,
        supplier_id INT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES product_categories(category_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    );
    
    -- 库存表 (inventory)
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id SERIAL PRIMARY KEY,
        product_id INT NOT NULL,
        store_id INT NOT NULL,
        quantity INT NOT NULL CHECK (quantity >= 0),
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        UNIQUE (product_id, store_id)
    );
    
    -- 促销活动表 (promotions)
    CREATE TABLE IF NOT EXISTS promotions (
        promotion_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
        discount_value DECIMAL(10, 2) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        store_id INT,
        created_by INT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (created_by) REFERENCES users(user_id)
    );
    
    -- 促销商品关联表 (promotion_items)
    CREATE TABLE IF NOT EXISTS promotion_items (
        id SERIAL PRIMARY KEY,
        promotion_id INT NOT NULL,
        product_id INT NOT NULL,
        FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    
    -- 销售单主表 (sales)
    CREATE TABLE IF NOT EXISTS sales (
        sale_id SERIAL PRIMARY KEY,
        store_id INT NOT NULL,
        cashier_id INT NOT NULL,
        sale_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (store_id) REFERENCES stores(store_id),
        FOREIGN KEY (cashier_id) REFERENCES users(user_id)
    );
    
    -- 销售单详情表 (sale_items)
    CREATE TABLE IF NOT EXISTS sale_items (
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
    
    # 为现有表添加时间字段（如果不存在）
    alter_tables_sql = """
    -- 为stores表添加时间字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='stores' AND column_name='created_at') THEN
            ALTER TABLE stores ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='stores' AND column_name='updated_at') THEN
            ALTER TABLE stores ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    
    -- 为product_categories表添加时间字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='product_categories' AND column_name='created_at') THEN
            ALTER TABLE product_categories ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='product_categories' AND column_name='updated_at') THEN
            ALTER TABLE product_categories ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    
    -- 为suppliers表添加时间字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='suppliers' AND column_name='created_at') THEN
            ALTER TABLE suppliers ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='suppliers' AND column_name='updated_at') THEN
            ALTER TABLE suppliers ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    
    -- 为products表添加时间字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='products' AND column_name='created_at') THEN
            ALTER TABLE products ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='products' AND column_name='updated_at') THEN
            ALTER TABLE products ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    
    -- 为inventory表添加时间字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory' AND column_name='created_at') THEN
            ALTER TABLE inventory ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='inventory' AND column_name='updated_at') THEN
            ALTER TABLE inventory ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    
    -- 为promotions表添加门店和创建者字段
    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='store_id') THEN
            ALTER TABLE promotions ADD COLUMN store_id INT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='created_by') THEN
            ALTER TABLE promotions ADD COLUMN created_by INT;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='created_at') THEN
            ALTER TABLE promotions ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    """
    
    cursor.execute(alter_tables_sql)
    
    # 修复现有用户的门店ID问题
    fix_users_sql = """
    -- 为没有门店ID的用户分配默认门店ID（1）
    UPDATE users SET store_id = 1 WHERE store_id IS NULL AND role IN ('cashier', 'store_manager', 'system_admin');
    """
    
    cursor.execute(fix_users_sql)
    
    # 修复work_logs表结构问题
    fix_work_logs_sql = """
    -- 检查并修复work_logs表结构
    DO $$ 
    BEGIN 
        -- 如果action字段不存在，则添加它
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='work_logs' AND column_name='action') THEN
            ALTER TABLE work_logs ADD COLUMN action VARCHAR(100);
        END IF;
        
        -- 如果details字段不存在，则添加它
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='work_logs' AND column_name='details') THEN
            ALTER TABLE work_logs ADD COLUMN details TEXT;
        END IF;
        
        -- 如果timestamp字段不存在，则添加它
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='work_logs' AND column_name='timestamp') THEN
            ALTER TABLE work_logs ADD COLUMN timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        END IF;
    END $$;
    """
    
    cursor.execute(fix_work_logs_sql)
    
    # 删除工作日志功能和仪表盘功能（如果存在）
    delete_features_sql = """
    -- 删除工作日志功能和仪表盘功能
    DELETE FROM role_permissions WHERE feature_id IN (
        SELECT feature_id FROM system_features WHERE feature_code IN ('work_log_management', 'dashboard_view')
    );
    DELETE FROM system_features WHERE feature_code IN ('work_log_management', 'dashboard_view');
    """
    
    cursor.execute(delete_features_sql)
    
    # 创建功能权限管理表
    permission_tables_sql = """
    -- 系统功能表 (system_features)
    CREATE TABLE IF NOT EXISTS system_features (
        feature_id SERIAL PRIMARY KEY,
        feature_code VARCHAR(50) UNIQUE NOT NULL,
        feature_name VARCHAR(100) NOT NULL,
        description TEXT,
        module VARCHAR(50) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 角色权限表 (role_permissions)
    CREATE TABLE IF NOT EXISTS role_permissions (
        permission_id SERIAL PRIMARY KEY,
        role VARCHAR(20) NOT NULL,
        feature_id INT NOT NULL,
        can_view BOOLEAN DEFAULT FALSE,
        can_create BOOLEAN DEFAULT FALSE,
        can_edit BOOLEAN DEFAULT FALSE,
        can_delete BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (feature_id) REFERENCES system_features(feature_id),
        UNIQUE (role, feature_id)
    );
    """
    
    cursor.execute(permission_tables_sql)
    
    # 初始化系统功能数据
    init_features_sql = """
    -- 插入系统功能数据（如果不存在）
    DO $$
    BEGIN
        -- 插入系统功能
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'user_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('user_management', '用户管理', '管理系统用户账号', 'user');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'store_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('store_management', '门店管理', '管理门店信息', 'store');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'category_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('category_management', '分类管理', '管理商品分类', 'category');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'supplier_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('supplier_management', '供应商管理', '管理供应商信息', 'supplier');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'product_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('product_management', '商品管理', '管理商品信息', 'product');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'inventory_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('inventory_management', '库存管理', '管理商品库存', 'inventory');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'promotion_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('promotion_management', '促销管理', '管理促销活动', 'promotion');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'sales_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('sales_management', '销售管理', '查看销售记录', 'sales');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'pos_system') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('pos_system', '收银系统', '收银台操作', 'pos');
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM system_features WHERE feature_code = 'permission_management') THEN
            INSERT INTO system_features (feature_code, feature_name, description, module) 
            VALUES ('permission_management', '权限管理', '管理角色权限', 'permission');
        END IF;
    END $$;
    
    -- 为system_admin角色初始化所有权限
    INSERT INTO role_permissions (role, feature_id, can_view, can_create, can_edit, can_delete)
    SELECT 'system_admin', feature_id, TRUE, TRUE, TRUE, TRUE
    FROM system_features
    WHERE NOT EXISTS (
        SELECT 1 FROM role_permissions 
        WHERE role = 'system_admin' AND feature_id = system_features.feature_id
    );
    
    -- 为store_manager角色初始化基本权限
    INSERT INTO role_permissions (role, feature_id, can_view, can_create, can_edit, can_delete)
    SELECT 'store_manager', sf.feature_id, 
        CASE 
            WHEN sf.feature_code IN ('user_management', 'store_management', 'permission_management') THEN FALSE
            WHEN sf.feature_code IN ('category_management', 'supplier_management') THEN FALSE
            ELSE TRUE
        END,
        CASE 
            WHEN sf.feature_code IN ('user_management', 'store_management', 'permission_management') THEN FALSE
            WHEN sf.feature_code IN ('category_management', 'supplier_management') THEN FALSE
            WHEN sf.feature_code IN ('sales_management', 'promotion_management') THEN FALSE
            ELSE TRUE
        END,
        CASE 
            WHEN sf.feature_code IN ('user_management', 'store_management', 'permission_management') THEN FALSE
            WHEN sf.feature_code IN ('category_management', 'supplier_management') THEN FALSE
            WHEN sf.feature_code IN ('sales_management', 'promotion_management') THEN FALSE
            ELSE TRUE
        END,
        CASE 
            WHEN sf.feature_code IN ('user_management', 'store_management', 'permission_management') THEN FALSE
            WHEN sf.feature_code IN ('category_management', 'supplier_management') THEN FALSE
            WHEN sf.feature_code IN ('sales_management', 'promotion_management') THEN FALSE
            WHEN sf.feature_code IN ('product_management') THEN FALSE
            ELSE TRUE
        END
    FROM system_features sf
    WHERE NOT EXISTS (
        SELECT 1 FROM role_permissions 
        WHERE role = 'store_manager' AND feature_id = sf.feature_id
    );
    
    -- 为cashier角色初始化基本权限
    INSERT INTO role_permissions (role, feature_id, can_view, can_create, can_edit, can_delete)
    SELECT 'cashier', sf.feature_id,
        CASE 
            WHEN sf.feature_code IN ('pos_system', 'inventory_management', 'product_management') THEN TRUE
            ELSE FALSE
        END,
        CASE 
            WHEN sf.feature_code IN ('pos_system') THEN TRUE
            ELSE FALSE
        END,
        CASE 
            WHEN sf.feature_code IN ('inventory_management') THEN TRUE
            ELSE FALSE
        END,
        FALSE
    FROM system_features sf
    WHERE NOT EXISTS (
        SELECT 1 FROM role_permissions 
        WHERE role = 'cashier' AND feature_id = sf.feature_id
    );
    """
    
    cursor.execute(init_features_sql)
    
    conn.commit()
    cursor.close()
    conn.close()

# ==================== 健康检查 ====================
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'message': '超市管理系统运行正常'}, 200

# ==================== 认证相关 ====================
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'cashier')  # 默认收银员
        
        if not all([username, password]):
            return {'message': '用户名和密码不能为空'}, 400
        
        if role not in ['admin', 'manager', 'cashier']:
            return {'message': '角色必须是admin、manager或cashier'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '用户名已存在'}, 400
        
        # 创建用户
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s) RETURNING user_id",
            (username, password_hash, role)
        )
        user_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '用户注册成功',
            'user_id': user_id,
            'username': username,
            'role': role
        }, 201
        
    except Exception as e:
        return {'message': f'用户注册失败: {str(e)}'}, 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return {'message': '用户名和密码不能为空'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, username, password_hash, role, store_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user or not check_password_hash(user[2], password):
            return {'message': '用户名或密码错误'}, 401
        
        # 创建JWT token
        access_token = create_access_token(identity=str(user[0]))
        
        # 记录登录日志
        log_action(user[0], 'login', f'用户 {user[1]} 登录系统')
        
        return {
            'message': '登录成功',
            'access_token': access_token,
            'user': {
                'user_id': user[0],
                'username': user[1],
                'role': user[3],
                'store_id': user[4]
            }
        }, 200
        
    except Exception as e:
        return {'message': f'登录失败: {str(e)}'}, 500

# ==================== 用户管理 ====================
@app.route('/api/users/', methods=['POST'])
@jwt_required()
def create_user():
    try:
        current_user_id = int(get_jwt_identity())
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'cashier')
        store_id = data.get('store_id')
        
        if not all([username, password]):
            return {'message': '用户名和密码不能为空'}, 400
        
        # 修正角色名称以匹配数据库约束
        role_mapping = {
            'admin': 'system_admin',
            'manager': 'store_manager',
            'cashier': 'cashier'
        }
        
        if role not in role_mapping:
            return {'message': '角色必须是admin、manager或cashier'}, 400
        
        db_role = role_mapping[role]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 权限检查：门店经理只能创建收银员，且必须在自己的门店
        if current_role == 'store_manager':
            if db_role != 'cashier':
                cursor.close()
                conn.close()
                return {'message': '门店经理只能创建收银员账户'}, 403
            
            if store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '门店经理只能在自己的门店创建用户'}, 403
        
        # 系统管理员可以创建任何角色的用户
        # 收银员不能创建用户（这个检查可以在前端控制，但后端也应该有）
        elif current_role == 'cashier':
            cursor.close()
            conn.close()
            return {'message': '收银员无权创建用户'}, 403
        
        # 检查用户名是否已存在
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '用户名已存在'}, 400
        
        # 创建用户
        password_hash = generate_password_hash(password)
        
        # 设置门店ID的逻辑
        if db_role == 'system_admin':
            # 系统管理员分配到总店（ID: 1）
            store_id = 1
        elif db_role in ['store_manager', 'cashier']:
            # 门店经理和收银员必须指定门店ID
            if not store_id:
                # 如果没有指定门店ID，默认分配到门店1
                store_id = 1
        
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, store_id) VALUES (%s, %s, %s, %s) RETURNING user_id",
            (username, password_hash, db_role, store_id)
        )
        user_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '用户创建成功',
            'user_id': user_id,
            'username': username,
            'role': role
        }, 201
        
    except Exception as e:
        return {'message': f'用户创建失败: {str(e)}'}, 500

@app.route('/api/users/', methods=['GET'])
@jwt_required()
def get_users():
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 根据角色权限过滤用户
        if current_role == 'system_admin':
            # 系统管理员可以看到所有用户
            cursor.execute("""
                SELECT u.user_id, u.username, u.role, u.store_id, s.name as store_name,
                       u.created_at, u.updated_at
                FROM users u
                LEFT JOIN stores s ON u.store_id = s.store_id
                ORDER BY u.user_id DESC
            """)
        elif current_role == 'store_manager':
            # 门店经理只能看到自己门店的收银员和自己
            cursor.execute("""
                SELECT u.user_id, u.username, u.role, u.store_id, s.name as store_name,
                       u.created_at, u.updated_at
                FROM users u
                LEFT JOIN stores s ON u.store_id = s.store_id
                WHERE (u.store_id = %s AND u.role IN ('cashier', 'store_manager')) 
                   OR u.user_id = %s
                ORDER BY u.user_id DESC
            """, (current_store_id, current_user_id))
        else:
            # 收银员只能看到自己
            cursor.execute("""
                SELECT u.user_id, u.username, u.role, u.store_id, s.name as store_name,
                       u.created_at, u.updated_at
                FROM users u
                LEFT JOIN stores s ON u.store_id = s.store_id
                WHERE u.user_id = %s
                ORDER BY u.user_id DESC
            """, (current_user_id,))
        
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        users_list = []
        for user in users:
            # 转换角色名称为前端友好格式
            role_display = {
                'system_admin': 'admin',
                'store_manager': 'manager',
                'cashier': 'cashier'
            }.get(user[2], user[2])
            
            users_list.append({
                'user_id': user[0],
                'username': user[1],
                'role': role_display,
                'store_id': user[3],
                'store_name': user[4],
                'created_at': format_datetime_with_timezone(user[5]),
                'updated_at': format_datetime_with_timezone(user[6])
            })
        
        return {'users': users_list}, 200
        
    except Exception as e:
        return {'message': f'获取用户列表失败: {str(e)}'}, 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        data = request.get_json()
        username = data.get('username')
        role = data.get('role')
        store_id = data.get('store_id')
        password = data.get('password')  # 可选，如果提供则更新密码
        
        if not all([username, role]):
            return {'message': '用户名和角色不能为空'}, 400
        
        # 修正角色名称以匹配数据库约束
        role_mapping = {
            'admin': 'system_admin',
            'manager': 'store_manager',
            'cashier': 'cashier'
        }
        
        if role not in role_mapping:
            return {'message': '角色必须是admin、manager或cashier'}, 400
        
        db_role = role_mapping[role]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查要更新的用户是否存在，并获取其信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        target_role, target_store_id = target_user
        
        # 权限检查：门店经理只能更新自己门店的收银员
        if current_role == 'store_manager':
            # 不能更新系统管理员
            if target_role == 'system_admin':
                cursor.close()
                conn.close()
                return {'message': '门店经理无权更新系统管理员'}, 403
            
            # 只能更新自己门店的用户
            if target_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '门店经理只能更新自己门店的用户'}, 403
            
            # 只能将用户设置为收银员角色
            if db_role != 'cashier' and user_id != current_user_id:
                cursor.close()
                conn.close()
                return {'message': '门店经理只能将其他用户设置为收银员'}, 403
            
            # 只能在自己的门店内操作
            if store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '门店经理只能在自己的门店内操作'}, 403
        
        # 收银员只能更新自己的信息
        elif current_role == 'cashier':
            if user_id != current_user_id:
                cursor.close()
                conn.close()
                return {'message': '收银员只能更新自己的信息'}, 403
        
        # 检查用户名是否被其他用户使用
        cursor.execute("SELECT user_id FROM users WHERE username = %s AND user_id != %s", (username, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '用户名已被其他用户使用'}, 400
        
        # 如果是系统管理员，自动分配到总店（ID: 1）
        if db_role == 'system_admin':
            store_id = 1  # 总店ID
        
        # 更新用户信息
        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE users 
                SET username = %s, password_hash = %s, role = %s, store_id = %s
                WHERE user_id = %s
            """, (username, password_hash, db_role, store_id, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET username = %s, role = %s, store_id = %s
                WHERE user_id = %s
            """, (username, db_role, store_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '用户更新成功',
            'user_id': user_id,
            'username': username,
            'role': role
        }, 200
        
    except Exception as e:
        return {'message': f'用户更新失败: {str(e)}'}, 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # 不能删除自己
        if current_user_id == user_id:
            return {'message': '不能删除自己的账户'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查要删除的用户是否存在，并获取其信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (user_id,))
        target_user = cursor.fetchone()
        if not target_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        target_role, target_store_id = target_user
        
        # 权限检查：门店经理只能删除自己门店的收银员
        if current_role == 'store_manager':
            # 不能删除系统管理员
            if target_role == 'system_admin':
                cursor.close()
                conn.close()
                return {'message': '门店经理无权删除系统管理员'}, 403
            
            # 不能删除其他门店经理
            if target_role == 'store_manager':
                cursor.close()
                conn.close()
                return {'message': '门店经理无权删除其他门店经理'}, 403
            
            # 只能删除自己门店的收银员
            if target_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '门店经理只能删除自己门店的收银员'}, 403
        
        # 收银员不能删除任何用户
        elif current_role == 'cashier':
            cursor.close()
            conn.close()
            return {'message': '收银员无权删除用户'}, 403
        
        # 检查是否有关联数据
        cursor.execute("SELECT COUNT(*) FROM sales WHERE cashier_id = %s", (user_id,))
        sales_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_logs WHERE user_id = %s", (user_id,))
        logs_count = cursor.fetchone()[0]
        
        if sales_count > 0 or logs_count > 0:
            cursor.close()
            conn.close()
            return {'message': '无法删除：该用户存在销售记录或工作日志'}, 400
        
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '用户删除成功'}, 200
        
    except Exception as e:
        return {'message': f'用户删除失败: {str(e)}'}, 500

# ==================== 门店管理 ====================
@app.route('/api/stores/', methods=['POST'])
@jwt_required()
def create_store():
    try:
        data = request.get_json()
        name = data.get('name')
        address = data.get('address')
        
        if not name:
            return {'message': '门店名称不能为空'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO stores (name, address) VALUES (%s, %s) RETURNING store_id",
            (name, address)
        )
        store_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '门店创建成功',
            'store_id': store_id,
            'name': name,
            'address': address
        }, 201
        
    except Exception as e:
        return {'message': f'门店创建失败: {str(e)}'}, 500

@app.route('/api/stores/', methods=['GET'])
def get_stores():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT store_id, name, address, created_at, updated_at FROM stores ORDER BY store_id")
        stores = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        stores_list = []
        for store in stores:
            stores_list.append({
                'store_id': store[0],
                'name': store[1],
                'address': store[2],
                'created_at': format_datetime_with_timezone(store[3]),
                'updated_at': format_datetime_with_timezone(store[4])
            })
        
        return {'stores': stores_list}, 200
        
    except Exception as e:
        return {'message': f'获取门店列表失败: {str(e)}'}, 500

@app.route('/api/stores/<int:store_id>', methods=['PUT'])
@jwt_required()
def update_store(store_id):
    try:
        data = request.get_json()
        name = data.get('name')
        address = data.get('address')
        
        if not all([name, address]):
            return {'message': '缺少必要参数'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查门店是否存在
        cursor.execute("SELECT store_id FROM stores WHERE store_id = %s", (store_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '门店不存在'}, 404
        
        cursor.execute(
            "UPDATE stores SET name = %s, address = %s, updated_at = CURRENT_TIMESTAMP WHERE store_id = %s",
            (name, address, store_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '门店更新成功',
            'store_id': store_id,
            'name': name
        }, 200
        
    except Exception as e:
        return {'message': f'门店更新失败: {str(e)}'}, 500

@app.route('/api/stores/<int:store_id>', methods=['DELETE'])
@jwt_required()
def delete_store(store_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查门店是否存在
        cursor.execute("SELECT store_id FROM stores WHERE store_id = %s", (store_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '门店不存在'}, 404
        
        # 检查是否有关联数据
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE store_id = %s", (store_id,))
        inventory_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sales WHERE store_id = %s", (store_id,))
        sales_count = cursor.fetchone()[0]
        
        if inventory_count > 0 or sales_count > 0:
            cursor.close()
            conn.close()
            return {'message': '无法删除：该门店存在库存或销售记录'}, 400
        
        cursor.execute("DELETE FROM stores WHERE store_id = %s", (store_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '门店删除成功'}, 200
        
    except Exception as e:
        return {'message': f'门店删除失败: {str(e)}'}, 500

# ==================== 商品分类管理 ====================
@app.route('/api/categories/', methods=['POST'])
@jwt_required()
def create_category():
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return {'message': '分类名称不能为空'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO product_categories (name) VALUES (%s) RETURNING category_id",
            (name,)
        )
        category_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '分类创建成功',
            'category_id': category_id,
            'name': name
        }, 201
        
    except Exception as e:
        return {'message': f'分类创建失败: {str(e)}'}, 500

@app.route('/api/categories/', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT category_id, name, created_at, updated_at FROM product_categories ORDER BY category_id")
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        categories_list = []
        for category in categories:
            categories_list.append({
                'category_id': category[0],
                'name': category[1],
                'created_at': format_datetime_with_timezone(category[2]),
                'updated_at': format_datetime_with_timezone(category[3])
            })
        
        return {'categories': categories_list}, 200
        
    except Exception as e:
        return {'message': f'获取分类列表失败: {str(e)}'}, 500

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return {'message': '缺少分类名称'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查分类是否存在
        cursor.execute("SELECT category_id FROM product_categories WHERE category_id = %s", (category_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '分类不存在'}, 404
        
        cursor.execute(
            "UPDATE product_categories SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE category_id = %s",
            (name, category_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '分类更新成功',
            'category_id': category_id,
            'name': name
        }, 200
        
    except Exception as e:
        return {'message': f'分类更新失败: {str(e)}'}, 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查分类是否存在
        cursor.execute("SELECT category_id FROM product_categories WHERE category_id = %s", (category_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '分类不存在'}, 404
        
        # 检查是否有关联商品
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
        product_count = cursor.fetchone()[0]
        
        if product_count > 0:
            cursor.close()
            conn.close()
            return {'message': '无法删除：该分类下存在商品'}, 400
        
        cursor.execute("DELETE FROM product_categories WHERE category_id = %s", (category_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '分类删除成功'}, 200
        
    except Exception as e:
        return {'message': f'分类删除失败: {str(e)}'}, 500

# ==================== 工作日志管理 ====================
@app.route('/api/work-logs/', methods=['POST'])
@jwt_required()
def create_work_log():
    try:
        data = request.get_json()
        user_id = data.get('user_id', int(get_jwt_identity()))
        store_id = data.get('store_id')
        action = data.get('action')  # 'clock_in' 或 'clock_out'
        notes = data.get('notes', '')
        
        if not all([store_id, action]):
            return {'message': '缺少必要参数'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if action == 'clock_in':
            cursor.execute(
                "INSERT INTO work_logs (user_id, store_id, clock_in_time, notes) VALUES (%s, %s, CURRENT_TIMESTAMP, %s) RETURNING log_id",
                (user_id, store_id, notes)
            )
        elif action == 'clock_out':
            # 更新最近的打卡记录
            cursor.execute(
                "UPDATE work_logs SET clock_out_time = CURRENT_TIMESTAMP, notes = %s WHERE user_id = %s AND store_id = %s AND clock_out_time IS NULL ORDER BY clock_in_time DESC LIMIT 1 RETURNING log_id",
                (notes, user_id, store_id)
            )
        else:
            return {'message': '无效的操作类型'}, 400
        
        result = cursor.fetchone()
        if not result:
            return {'message': '操作失败'}, 400
            
        log_id = result[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': f'{"上班" if action == "clock_in" else "下班"}打卡成功',
            'log_id': log_id
        }, 201
        
    except Exception as e:
        return {'message': f'打卡失败: {str(e)}'}, 500

@app.route('/api/work-logs/', methods=['GET'])
@jwt_required()
def get_work_logs():
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        current_role = current_user[0]
        
        # 只有系统管理员可以查看工作日志
        if current_role != 'system_admin':
            cursor.close()
            conn.close()
            return {'message': '您没有权限查看工作日志'}, 403
        
        # 查询所有工作日志
            cursor.execute("""
            SELECT w.log_id, w.user_id, w.action, w.details, w.timestamp,
                   u.username
                FROM work_logs w
                JOIN users u ON w.user_id = u.user_id
            ORDER BY w.timestamp DESC
            LIMIT 1000
        """)
        
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logs_list = []
        for log in logs:
            logs_list.append({
                'log_id': log[0],
                'user_id': log[1],
                'action': log[2],
                'details': log[3],
                'timestamp': format_datetime_with_timezone(log[4]),
                'username': log[5]
            })
        
        return {'work_logs': logs_list}, 200
        
    except Exception as e:
        return {'message': f'获取工作日志失败: {str(e)}'}, 500

# ==================== 供应商管理 ====================
@app.route('/api/suppliers/', methods=['POST'])
@jwt_required()
def create_supplier():
    try:
        data = request.get_json()
        name = data.get('name')
        contact_info = data.get('contact_info', '')
        
        if not name:
            return {'message': '供应商名称不能为空'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO suppliers (name, contact_info) VALUES (%s, %s) RETURNING supplier_id",
            (name, contact_info)
        )
        supplier_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '供应商创建成功',
            'supplier_id': supplier_id,
            'name': name,
            'contact_info': contact_info
        }, 201
        
    except Exception as e:
        return {'message': f'供应商创建失败: {str(e)}'}, 500

@app.route('/api/suppliers/', methods=['GET'])
def get_suppliers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT supplier_id, name, contact_info, created_at, updated_at FROM suppliers ORDER BY supplier_id")
        suppliers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        suppliers_list = []
        for supplier in suppliers:
            suppliers_list.append({
                'supplier_id': supplier[0],
                'name': supplier[1],
                'contact_info': supplier[2],
                'created_at': format_datetime_with_timezone(supplier[3]),
                'updated_at': format_datetime_with_timezone(supplier[4])
            })
        
        return {'suppliers': suppliers_list}, 200
        
    except Exception as e:
        return {'message': f'获取供应商列表失败: {str(e)}'}, 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    try:
        data = request.get_json()
        name = data.get('name')
        contact_info = data.get('contact_info', '')
        
        if not name:
            return {'message': '缺少必要参数'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查供应商是否存在
        cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '供应商不存在'}, 404
        
        cursor.execute("""
            UPDATE suppliers 
            SET name = %s, contact_info = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE supplier_id = %s
        """, (name, contact_info, supplier_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '供应商更新成功',
            'supplier_id': supplier_id,
            'name': name
        }, 200
        
    except Exception as e:
        return {'message': f'供应商更新失败: {str(e)}'}, 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查供应商是否存在
        cursor.execute("SELECT supplier_id FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '供应商不存在'}, 404
        
        # 检查是否有关联商品
        cursor.execute("SELECT COUNT(*) FROM products WHERE supplier_id = %s", (supplier_id,))
        product_count = cursor.fetchone()[0]
        
        if product_count > 0:
            cursor.close()
            conn.close()
            return {'message': '无法删除：该供应商下存在商品'}, 400
        
        cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '供应商删除成功'}, 200
        
    except Exception as e:
        return {'message': f'供应商删除失败: {str(e)}'}, 500

# ==================== 商品管理 ====================
@app.route('/api/products/', methods=['POST'])
@jwt_required()
def create_product():
    try:
        data = request.get_json()
        name = data.get('name')
        sku = data.get('sku')
        category_id = data.get('category_id')
        supplier_id = data.get('supplier_id')
        description = data.get('description', '')
        
        if not all([name, sku]):
            return {'message': '商品名称和SKU不能为空'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO products (sku, name, description, category_id, supplier_id) VALUES (%s, %s, %s, %s, %s) RETURNING product_id",
            (sku, name, description, category_id, supplier_id)
        )
        product_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '商品创建成功',
            'product_id': product_id,
            'name': name,
            'sku': sku
        }, 201
        
    except Exception as e:
        return {'message': f'商品创建失败: {str(e)}'}, 500

@app.route('/api/products/', methods=['GET'])
def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.product_id, p.sku, p.name, p.description,
                   c.name as category_name, s.name as supplier_name,
                   p.created_at, p.updated_at
            FROM products p
            LEFT JOIN product_categories c ON p.category_id = c.category_id
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_id
        """)
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        products_list = []
        for product in products:
            products_list.append({
                'product_id': product[0],
                'sku': product[1],
                'name': product[2],
                'description': product[3],
                'category_name': product[4],
                'supplier_name': product[5],
                'created_at': format_datetime_with_timezone(product[6]),
                'updated_at': format_datetime_with_timezone(product[7])
            })
        
        return {'products': products_list}, 200
        
    except Exception as e:
        return {'message': f'获取商品列表失败: {str(e)}'}, 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        category_id = data.get('category_id')
        supplier_id = data.get('supplier_id')
        
        if not all([name, category_id, supplier_id]):
            return {'message': '缺少必要参数'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查商品是否存在
        cursor.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '商品不存在'}, 404
        
        cursor.execute("""
            UPDATE products 
            SET name = %s, description = %s, category_id = %s, supplier_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = %s
        """, (name, description, category_id, supplier_id, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '商品更新成功',
            'product_id': product_id,
            'name': name
        }, 200
        
    except Exception as e:
        return {'message': f'商品更新失败: {str(e)}'}, 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查商品是否存在
        cursor.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {'message': '商品不存在'}, 404
        
        # 检查是否有关联数据
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE product_id = %s", (product_id,))
        inventory_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sale_items WHERE product_id = %s", (product_id,))
        sales_count = cursor.fetchone()[0]
        
        if inventory_count > 0 or sales_count > 0:
            cursor.close()
            conn.close()
            return {'message': '无法删除：该商品存在库存或销售记录'}, 400
        
        # 删除促销关联
        cursor.execute("DELETE FROM promotion_items WHERE product_id = %s", (product_id,))
        
        # 删除商品
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '商品删除成功'}, 200
        
    except Exception as e:
        return {'message': f'商品删除失败: {str(e)}'}, 500

# ==================== 库存管理 ====================
@app.route('/api/inventory/', methods=['POST'])
@jwt_required()
def update_inventory():
    try:
        current_user_id = int(get_jwt_identity())
        
        data = request.get_json()
        store_id = data.get('store_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        price = data.get('price')
        
        if not all([store_id, product_id, quantity is not None, price is not None]):
            return {'message': '缺少必要参数'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 权限检查：门店经理和收银员只能更新自己门店的库存
        if current_role in ['store_manager', 'cashier']:
            if store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能管理自己门店的库存'}, 403
        
        # 先检查是否已存在该商品的库存记录
        cursor.execute("""
            SELECT inventory_id FROM inventory 
            WHERE product_id = %s AND store_id = %s
        """, (product_id, store_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有记录
            cursor.execute("""
                UPDATE inventory 
                SET quantity = %s, price = %s, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = %s AND store_id = %s
                RETURNING inventory_id
            """, (quantity, price, product_id, store_id))
        else:
            # 插入新记录
            cursor.execute("""
                INSERT INTO inventory (product_id, store_id, quantity, price)
                VALUES (%s, %s, %s, %s)
                RETURNING inventory_id
            """, (product_id, store_id, quantity, price))
        
        inventory_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '库存更新成功',
            'inventory_id': inventory_id,
            'store_id': store_id,
            'product_id': product_id,
            'quantity': quantity,
            'price': float(price)
        }, 200
        
    except Exception as e:
        return {'message': f'库存更新失败: {str(e)}'}, 500

@app.route('/api/inventory/', methods=['GET'])
@jwt_required()
def get_inventory():
    try:
        current_user_id = int(get_jwt_identity())
        store_id = request.args.get('store_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 权限检查：门店经理和收银员只能查看自己门店的库存
        if current_role in ['store_manager', 'cashier']:
            # 强制使用当前用户的门店ID，忽略请求参数中的store_id
            store_id = current_store_id
            cursor.execute("""
                SELECT i.inventory_id, i.product_id, i.store_id, i.quantity, i.price,
                       p.name as product_name, s.name as store_name, i.updated_at
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                JOIN stores s ON i.store_id = s.store_id
                WHERE i.store_id = %s
                ORDER BY i.inventory_id
            """, (store_id,))
        else:
            # 系统管理员可以查看所有门店或指定门店的库存
            if store_id:
                cursor.execute("""
                    SELECT i.inventory_id, i.product_id, i.store_id, i.quantity, i.price,
                               p.name as product_name, s.name as store_name, i.updated_at
                    FROM inventory i
                    JOIN products p ON i.product_id = p.product_id
                    JOIN stores s ON i.store_id = s.store_id
                    WHERE i.store_id = %s
                    ORDER BY i.inventory_id
                """, (store_id,))
            else:
                cursor.execute("""
                    SELECT i.inventory_id, i.product_id, i.store_id, i.quantity, i.price,
                               p.name as product_name, s.name as store_name, i.updated_at
                    FROM inventory i
                    JOIN products p ON i.product_id = p.product_id
                    JOIN stores s ON i.store_id = s.store_id
                    ORDER BY i.inventory_id
                """)
        
        inventory = cursor.fetchall()
        
        # 获取当前有效的促销信息
        current_date = date.today()  # 使用真实当前日期
        cursor.execute("""
            SELECT pi.product_id, pr.discount_type, pr.discount_value
            FROM promotion_items pi
            JOIN promotions pr ON pi.promotion_id = pr.promotion_id
            WHERE pr.start_date <= %s AND pr.end_date >= %s
        """, (current_date, current_date))
        
        promotions = cursor.fetchall()
        promotion_dict = {}
        for promo in promotions:
            product_id, discount_type, discount_value = promo
            promotion_dict[product_id] = {
                'discount_type': discount_type,
                'discount_value': float(discount_value)
            }
        
        cursor.close()
        conn.close()
        
        inventory_list = []
        for item in inventory:
            original_price = float(item[4]) if item[4] else 0
            final_price = original_price
            has_promotion = False
            
            # 计算促销价格
            if item[1] in promotion_dict:  # product_id
                promo = promotion_dict[item[1]]
                has_promotion = True
                if promo['discount_type'] == 'percentage':
                    final_price = original_price * (1 - promo['discount_value'] / 100)
                elif promo['discount_type'] == 'fixed':
                    final_price = max(0, original_price - promo['discount_value'])
            
            inventory_list.append({
                'inventory_id': item[0],
                'product_id': item[1],
                'store_id': item[2],
                'quantity': item[3],
                'original_price': original_price,
                'price': round(final_price, 2),  # 最终价格（含促销），保留两位小数
                'has_promotion': has_promotion,
                'product_name': item[5],
                'name': item[5],  # 收银台需要的字段名
                'store_name': item[6],
                'updated_at': format_datetime_with_timezone(item[7]) if item[7] else None
            })
        
        return {'inventory': inventory_list}, 200
        
    except Exception as e:
        return {'message': f'获取库存失败: {str(e)}'}, 500

# ==================== 促销管理 ====================
@app.route('/api/promotions/', methods=['POST'])
@jwt_required()
def create_promotion():
    try:
        current_user_id = int(get_jwt_identity())
        
        # 首先检查用户是否有创建促销的权限
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户权限
        cursor.execute("""
            SELECT rp.can_create
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND sf.feature_code = 'promotion_management'
        """, (current_user_id,))
        
        permission_result = cursor.fetchone()
        if not permission_result or not permission_result[0]:
            cursor.close()
            conn.close()
            return {'message': '您没有权限创建促销活动'}, 403
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        discount_type = data.get('discount_type')  # 'percentage' 或 'fixed'
        discount_value = data.get('discount_value')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        product_ids = data.get('product_ids', [])  # 参与促销的商品ID列表
        store_id = data.get('store_id')  # 门店ID，可选
        
        if not all([name, discount_type, discount_value, start_date, end_date]):
            cursor.close()
            conn.close()
            return {'message': '缺少必要参数'}, 400
        
        if not product_ids:
            cursor.close()
            conn.close()
            return {'message': '请选择参与促销的商品'}, 400
        
        if discount_type not in ['percentage', 'fixed']:
            cursor.close()
            conn.close()
            return {'message': '折扣类型必须是percentage或fixed'}, 400
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 权限检查和门店ID设置
        if current_role == 'system_admin':
            # 系统管理员可以创建全系统促销（store_id为NULL）或指定门店促销
            final_store_id = store_id  # 可以为None（全系统）或指定门店ID
        elif current_role == 'store_manager':
            # 门店经理只能为自己的门店创建促销
            final_store_id = current_store_id
            if store_id and store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能为自己的门店创建促销活动'}, 403
        else:
            # 收银员不能创建促销
            cursor.close()
            conn.close()
            return {'message': '您没有权限创建促销活动'}, 403
        
        # 创建促销活动
        cursor.execute(
            "INSERT INTO promotions (name, description, discount_type, discount_value, start_date, end_date, store_id, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING promotion_id",
            (name, description, discount_type, discount_value, start_date, end_date, final_store_id, current_user_id)
        )
        promotion_id = cursor.fetchone()[0]
        
        # 添加促销商品关联
        for product_id in product_ids:
            cursor.execute(
                "INSERT INTO promotion_items (promotion_id, product_id) VALUES (%s, %s)",
                (promotion_id, product_id)
            )
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'message': '促销活动创建成功',
            'promotion_id': promotion_id,
            'name': name,
            'store_id': final_store_id,
            'product_count': len(product_ids)
        }, 201
        
    except Exception as e:
        return {'message': f'促销活动创建失败: {str(e)}'}, 500

@app.route('/api/promotions/', methods=['GET'])
@jwt_required()
def get_promotions():
    try:
        from datetime import datetime, date
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 根据用户角色查询不同的促销活动
        if current_role == 'system_admin':
            # 系统管理员可以查看所有促销活动
            cursor.execute("""
                SELECT p.promotion_id, p.name, p.description, p.discount_type, p.discount_value, 
                       p.start_date, p.end_date, p.store_id, s.name as store_name, p.created_by
                FROM promotions p
                LEFT JOIN stores s ON p.store_id = s.store_id
                ORDER BY p.promotion_id DESC
            """)
        else:
            # 门店经理和收银员只能查看全系统促销和自己门店的促销
            cursor.execute("""
                SELECT p.promotion_id, p.name, p.description, p.discount_type, p.discount_value, 
                       p.start_date, p.end_date, p.store_id, s.name as store_name, p.created_by
                FROM promotions p
                LEFT JOIN stores s ON p.store_id = s.store_id
                WHERE p.store_id IS NULL OR p.store_id = %s
                ORDER BY p.promotion_id DESC
            """, (current_store_id,))
        
        promotions = cursor.fetchall()
        
        promotions_list = []
        current_date = date.today()
        
        for promotion in promotions:
            # 获取参与促销的商品
            cursor.execute("""
                SELECT p.product_id, p.name
                FROM promotion_items pi
                JOIN products p ON pi.product_id = p.product_id
                WHERE pi.promotion_id = %s
            """, (promotion[0],))
            products = cursor.fetchall()
            
            # 处理日期格式
            start_date = promotion[5]
            end_date = promotion[6]
            
            # 判断促销状态
            status = 'inactive'
            if start_date and end_date:
                # 确保日期类型一致，都转换为date类型
                if hasattr(start_date, 'date'):
                    start_date_cmp = start_date.date()
                else:
                    start_date_cmp = start_date
                    
                if hasattr(end_date, 'date'):
                    end_date_cmp = end_date.date()
                else:
                    end_date_cmp = end_date
                
                if current_date < start_date_cmp:
                    status = 'pending'  # 未开始
                elif start_date_cmp <= current_date <= end_date_cmp:
                    status = 'active'   # 进行中
                else:
                    status = 'expired'  # 已过期
            
            promotions_list.append({
                'promotion_id': promotion[0],
                'name': promotion[1],
                'description': promotion[2],
                'discount_type': promotion[3],
                'discount_value': float(promotion[4]) if promotion[4] else 0,
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                'store_id': promotion[7],
                'store_name': promotion[8] if promotion[8] else '全系统',
                'created_by': promotion[9],
                'status': status,
                'products': [{'product_id': p[0], 'name': p[1]} for p in products]
            })
        
        cursor.close()
        conn.close()
        
        return {'promotions': promotions_list}, 200
        
    except Exception as e:
        return {'message': f'获取促销活动失败: {str(e)}'}, 500

@app.route('/api/promotions/<int:promotion_id>', methods=['PUT'])
@jwt_required()
def update_promotion(promotion_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # 首先检查用户是否有编辑促销的权限
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户权限
        cursor.execute("""
            SELECT rp.can_edit
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND sf.feature_code = 'promotion_management'
        """, (current_user_id,))
        
        permission_result = cursor.fetchone()
        if not permission_result or not permission_result[0]:
            cursor.close()
            conn.close()
            return {'message': '您没有权限编辑促销活动'}, 403
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        discount_type = data.get('discount_type')
        discount_value = data.get('discount_value')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        product_ids = data.get('product_ids', [])
        
        if not all([name, discount_type, discount_value, start_date, end_date]):
            cursor.close()
            conn.close()
            return {'message': '缺少必要参数'}, 400
        
        if not product_ids:
            cursor.close()
            conn.close()
            return {'message': '请选择参与促销的商品'}, 400
        
        if discount_type not in ['percentage', 'fixed']:
            cursor.close()
            conn.close()
            return {'message': '折扣类型必须是percentage或fixed'}, 400
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查促销活动是否存在并获取其信息
        cursor.execute("SELECT store_id, created_by FROM promotions WHERE promotion_id = %s", (promotion_id,))
        promotion_info = cursor.fetchone()
        if not promotion_info:
            cursor.close()
            conn.close()
            return {'message': '促销活动不存在'}, 404
        
        promotion_store_id, promotion_created_by = promotion_info
        
        # 权限检查
        if current_role == 'system_admin':
            # 系统管理员可以修改所有促销活动
            pass
        elif current_role == 'store_manager':
            # 门店经理只能修改自己门店的促销活动或自己创建的全系统促销
            if promotion_store_id is not None and promotion_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能修改自己门店的促销活动'}, 403
            if promotion_store_id is None and promotion_created_by != current_user_id:
                cursor.close()
                conn.close()
                return {'message': '您只能修改自己创建的全系统促销活动'}, 403
        else:
            # 收银员不能修改促销
            cursor.close()
            conn.close()
            return {'message': '您没有权限修改促销活动'}, 403
        
        # 更新促销活动
        cursor.execute("""
            UPDATE promotions 
            SET name = %s, description = %s, discount_type = %s, discount_value = %s, 
                start_date = %s, end_date = %s
            WHERE promotion_id = %s
        """, (name, description, discount_type, discount_value, start_date, end_date, promotion_id))
        
        # 删除旧的商品关联
        cursor.execute("DELETE FROM promotion_items WHERE promotion_id = %s", (promotion_id,))
        
        # 添加新的商品关联
        for product_id in product_ids:
            cursor.execute(
                "INSERT INTO promotion_items (promotion_id, product_id) VALUES (%s, %s)",
                (promotion_id, product_id)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '促销活动更新成功',
            'promotion_id': promotion_id,
            'name': name,
            'product_count': len(product_ids)
        }, 200
        
    except Exception as e:
        return {'message': f'促销活动更新失败: {str(e)}'}, 500

@app.route('/api/promotions/<int:promotion_id>', methods=['DELETE'])
@jwt_required()
def delete_promotion(promotion_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先检查用户是否有删除促销的权限
        cursor.execute("""
            SELECT rp.can_delete
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND sf.feature_code = 'promotion_management'
        """, (current_user_id,))
        
        permission_result = cursor.fetchone()
        if not permission_result or not permission_result[0]:
            cursor.close()
            conn.close()
            return {'message': '您没有权限删除促销活动'}, 403
        
        # 获取当前用户信息以进行权限检查
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查促销活动是否存在并获取其信息
        cursor.execute("SELECT store_id, created_by FROM promotions WHERE promotion_id = %s", (promotion_id,))
        promotion_info = cursor.fetchone()
        if not promotion_info:
            cursor.close()
            conn.close()
            return {'message': '促销活动不存在'}, 404
        
        promotion_store_id, promotion_created_by = promotion_info
        
        # 权限检查
        if current_role == 'system_admin':
            # 系统管理员可以删除所有促销活动
            pass
        elif current_role == 'store_manager':
            # 门店经理只能删除自己门店的促销活动或自己创建的全系统促销
            if promotion_store_id is not None and promotion_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能删除自己门店的促销活动'}, 403
            if promotion_store_id is None and promotion_created_by != current_user_id:
                cursor.close()
                conn.close()
                return {'message': '您只能删除自己创建的全系统促销活动'}, 403
        else:
            # 收银员不能删除促销
            cursor.close()
            conn.close()
            return {'message': '您没有权限删除促销活动'}, 403
        
        # 删除商品关联
        cursor.execute("DELETE FROM promotion_items WHERE promotion_id = %s", (promotion_id,))
        
        # 删除促销活动
        cursor.execute("DELETE FROM promotions WHERE promotion_id = %s", (promotion_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '促销活动删除成功'}, 200
        
    except Exception as e:
        return {'message': f'促销活动删除失败: {str(e)}'}, 500

# ==================== 销售管理 ====================
@app.route('/api/sales/', methods=['POST'])
@jwt_required()
def create_sale():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        store_id = data.get('store_id')
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')
        
        # 调试信息 - 打印接收到的数据
        print(f"收到销售请求数据: store_id={store_id}, items={items}")
        
        if not all([store_id, items]):
            return {'message': '缺少必要参数'}, 400
        
        current_user_id = int(get_jwt_identity())
        print(f"当前用户ID: {current_user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询当前用户信息进行调试
        cursor.execute("SELECT user_id, username, role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        user_info = cursor.fetchone()
        if user_info:
            print(f"用户信息: ID={user_info[0]}, 用户名={user_info[1]}, 角色={user_info[2]}, 门店ID={user_info[3]}")
            
            # 检查用户门店ID与请求门店ID是否匹配
            user_store_id = user_info[3]
            if user_store_id is None:
                print(f"❌ 警告: 用户 {user_info[1]} 没有分配门店ID!")
            elif user_store_id != store_id:
                print(f"⚠️ 注意: 用户门店ID ({user_store_id}) 与请求门店ID ({store_id}) 不匹配")
        else:
            print(f"❌ 找不到用户ID {current_user_id} 的信息")
        
        # 计算总金额，支持unit_price或price_per_unit字段
        total_amount = 0
        for item in items:
            quantity = item['quantity']
            # 兼容两种价格字段名
            unit_price = item.get('unit_price') or item.get('price_per_unit', 0)
            total_amount += quantity * unit_price
        
        cursor.execute(
            "INSERT INTO sales (store_id, cashier_id, total_amount) VALUES (%s, %s, %s) RETURNING sale_id",
            (store_id, current_user_id, total_amount)
        )
        sale_id = cursor.fetchone()[0]
        
        # 处理每个销售项目
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            unit_price = item.get('unit_price') or item.get('price_per_unit', 0)
            
            # 检查库存是否足够
            cursor.execute(
                "SELECT quantity FROM inventory WHERE store_id = %s AND product_id = %s",
                (store_id, product_id)
            )
            stock_result = cursor.fetchone()
            
            if not stock_result or stock_result[0] < quantity:
                conn.rollback()
                cursor.close()
                conn.close()
                return {'message': f'商品ID {product_id} 库存不足，当前库存: {stock_result[0] if stock_result else 0}，需要: {quantity}'}, 400
            
            # 插入销售明细
            cursor.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, price_per_unit) VALUES (%s, %s, %s, %s)",
                (sale_id, product_id, quantity, unit_price)
            )
            
            # 更新库存 - 添加调试信息
            print(f"更新库存: 商品ID {product_id}, 门店ID {store_id}, 减少数量 {quantity}")
            cursor.execute(
                "UPDATE inventory SET quantity = quantity - %s WHERE store_id = %s AND product_id = %s",
                (quantity, store_id, product_id)
            )
            
            # 检查UPDATE语句影响的行数
            affected_rows = cursor.rowcount
            print(f"UPDATE影响的行数: {affected_rows}")
            
            if affected_rows == 0:
                print(f"❌ 警告: 没有找到匹配的库存记录! 门店ID: {store_id}, 商品ID: {product_id}")
                # 查询是否存在该商品的库存记录
                cursor.execute(
                    "SELECT store_id, product_id, quantity FROM inventory WHERE product_id = %s",
                    (product_id,)
                )
                all_inventory = cursor.fetchall()
                print(f"该商品的所有库存记录: {all_inventory}")
            
            # 验证更新结果
            cursor.execute(
                "SELECT quantity FROM inventory WHERE store_id = %s AND product_id = %s",
                (store_id, product_id)
            )
            new_quantity = cursor.fetchone()
            print(f"库存更新后: 商品ID {product_id}, 新库存 {new_quantity[0] if new_quantity else 'NULL'}")
        
        # 先提交销售和库存更新
        conn.commit()
        
        # 记录销售日志（单独处理，避免日志错误影响主事务）
        try:
            log_action(current_user_id, 'create_sale', f'创建销售订单 #{sale_id}，金额: ¥{total_amount:.2f}')
        except Exception as log_error:
            print(f"记录销售日志失败，但销售已成功: {log_error}")
        
        cursor.close()
        conn.close()
        
        return {
            'message': '销售记录创建成功',
            'sale_id': sale_id,
            'total_amount': float(total_amount),
            'items_count': len(items)
        }, 201
        
    except Exception as e:
        print(f"销售创建异常: {str(e)}")
        if conn:
            conn.rollback()
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return {'message': f'销售记录创建失败: {str(e)}'}, 500

@app.route('/api/sales/', methods=['GET'])
@jwt_required()
def get_sales():
    try:
        store_id = request.args.get('store_id')
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 根据角色权限过滤销售记录
        if current_role == 'system_admin':
            # 系统管理员可以看到所有销售记录
            if store_id:
                cursor.execute("""
                    SELECT s.sale_id, s.store_id, s.total_amount, s.sale_timestamp,
                           st.name as store_name, COALESCE(u.username, '未知') as cashier_name
                    FROM sales s
                    LEFT JOIN stores st ON s.store_id = st.store_id
                    LEFT JOIN users u ON s.cashier_id = u.user_id
                    WHERE s.store_id = %s
                    ORDER BY s.sale_timestamp DESC
                """, (store_id,))
            else:
                cursor.execute("""
                    SELECT s.sale_id, s.store_id, s.total_amount, s.sale_timestamp,
                           st.name as store_name, COALESCE(u.username, '未知') as cashier_name
                    FROM sales s
                    LEFT JOIN stores st ON s.store_id = st.store_id
                    LEFT JOIN users u ON s.cashier_id = u.user_id
                    ORDER BY s.sale_timestamp DESC
                """)
        elif current_role == 'store_manager':
            # 门店经理只能看到自己门店的销售记录
            cursor.execute("""
                SELECT s.sale_id, s.store_id, s.total_amount, s.sale_timestamp,
                       st.name as store_name, COALESCE(u.username, '未知') as cashier_name
                FROM sales s
                LEFT JOIN stores st ON s.store_id = st.store_id
                LEFT JOIN users u ON s.cashier_id = u.user_id
                WHERE s.store_id = %s
                ORDER BY s.sale_timestamp DESC
            """, (current_store_id,))
        else:
            # 收银员只能看到自己的销售记录
            cursor.execute("""
                SELECT s.sale_id, s.store_id, s.total_amount, s.sale_timestamp,
                       st.name as store_name, COALESCE(u.username, '未知') as cashier_name
                FROM sales s
                LEFT JOIN stores st ON s.store_id = st.store_id
                LEFT JOIN users u ON s.cashier_id = u.user_id
                WHERE s.cashier_id = %s
                ORDER BY s.sale_timestamp DESC
            """, (current_user_id,))
        
        sales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        sales_list = []
        for sale in sales:
            # 使用时区转换函数格式化时间
            timestamp_str = format_datetime_with_timezone(sale[3])
            
            sales_list.append({
                'sale_id': sale[0],
                'store_id': sale[1],
                'total_amount': float(sale[2]) if sale[2] else 0,
                'sale_date': timestamp_str,
                'sale_timestamp': timestamp_str,
                'store_name': sale[4],
                'user_name': sale[5],
                'cashier_name': sale[5]
            })
        
        return {'sales': sales_list}, 200
        
    except Exception as e:
        return {'message': f'获取销售记录失败: {str(e)}'}, 500

@app.route('/api/sales/<int:sale_id>/items', methods=['GET'])
@jwt_required()
def get_sale_items(sale_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取销售详情项目
        cursor.execute("""
            SELECT si.quantity, si.price_per_unit, p.name as product_name,
                   (si.quantity * si.price_per_unit) as subtotal
            FROM sale_items si
            JOIN products p ON si.product_id = p.product_id
            WHERE si.sale_id = %s
            ORDER BY si.item_id
        """, (sale_id,))
        
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        items_list = []
        for item in items:
            items_list.append({
                'quantity': item[0],
                'unit_price': float(item[1]) if item[1] else 0,
                'price_per_unit': float(item[1]) if item[1] else 0,
                'product_name': item[2],
                'subtotal': float(item[3]) if item[3] else 0
            })
        
        return {'items': items_list}, 200
        
    except Exception as e:
        return {'message': f'获取销售详情失败: {str(e)}'}, 500

@app.route('/api/sales/<int:sale_id>', methods=['DELETE'])
@jwt_required()
def delete_sale(sale_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先检查用户是否有删除销售记录的权限
        cursor.execute("""
            SELECT rp.can_delete
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND sf.feature_code = 'sales_management'
        """, (current_user_id,))
        
        permission_result = cursor.fetchone()
        if not permission_result or not permission_result[0]:
            cursor.close()
            conn.close()
            return {'message': '您没有权限删除销售记录'}, 403
        
        # 获取当前用户信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查销售记录是否存在并获取其信息
        cursor.execute("""
            SELECT store_id, cashier_id, total_amount 
            FROM sales 
            WHERE sale_id = %s
        """, (sale_id,))
        sale_info = cursor.fetchone()
        
        if not sale_info:
            cursor.close()
            conn.close()
            return {'message': '销售记录不存在'}, 404
        
        sale_store_id, sale_cashier_id, total_amount = sale_info
        
        # 权限检查
        if current_role == 'system_admin':
            # 系统管理员可以删除所有销售记录
            pass
        elif current_role == 'store_manager':
            # 门店经理只能删除自己门店的销售记录
            if sale_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能删除自己门店的销售记录'}, 403
        else:
            # 收银员只能删除自己的销售记录
            if sale_cashier_id != current_user_id:
                cursor.close()
                conn.close()
                return {'message': '您只能删除自己的销售记录'}, 403
        
        # 获取销售项目用于恢复库存
        cursor.execute("""
            SELECT product_id, quantity 
            FROM sale_items 
            WHERE sale_id = %s
        """, (sale_id,))
        sale_items = cursor.fetchall()
        
        # 删除销售项目
        cursor.execute("DELETE FROM sale_items WHERE sale_id = %s", (sale_id,))
        
        # 删除销售记录
        cursor.execute("DELETE FROM sales WHERE sale_id = %s", (sale_id,))
        
        # 恢复库存
        for product_id, quantity in sale_items:
            cursor.execute("""
                UPDATE inventory 
                SET quantity = quantity + %s, updated_at = CURRENT_TIMESTAMP
                WHERE store_id = %s AND product_id = %s
            """, (quantity, sale_store_id, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '销售记录删除成功，库存已恢复'}, 200
        
    except Exception as e:
        return {'message': f'销售记录删除失败: {str(e)}'}, 500

@app.route('/api/inventory/<int:inventory_id>', methods=['DELETE'])
@jwt_required()
def delete_inventory(inventory_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 首先检查用户是否有删除库存记录的权限
        cursor.execute("""
            SELECT rp.can_delete
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            JOIN users u ON u.role = rp.role
            WHERE u.user_id = %s AND sf.feature_code = 'inventory_management'
        """, (current_user_id,))
        
        permission_result = cursor.fetchone()
        if not permission_result or not permission_result[0]:
            cursor.close()
            conn.close()
            return {'message': '您没有权限删除库存记录'}, 403
        
        # 获取当前用户信息
        cursor.execute("SELECT role, store_id FROM users WHERE user_id = %s", (current_user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        current_role, current_store_id = current_user
        
        # 检查库存记录是否存在并获取其信息
        cursor.execute("""
            SELECT store_id, product_id, quantity
            FROM inventory 
            WHERE inventory_id = %s
        """, (inventory_id,))
        inventory_info = cursor.fetchone()
        
        if not inventory_info:
            cursor.close()
            conn.close()
            return {'message': '库存记录不存在'}, 404
        
        inventory_store_id, product_id, quantity = inventory_info
        
        # 权限检查
        if current_role == 'system_admin':
            # 系统管理员可以删除所有库存记录
            pass
        elif current_role in ['store_manager', 'cashier']:
            # 门店经理和收银员只能删除自己门店的库存记录
            if inventory_store_id != current_store_id:
                cursor.close()
                conn.close()
                return {'message': '您只能删除自己门店的库存记录'}, 403
        
        # 删除库存记录
        cursor.execute("DELETE FROM inventory WHERE inventory_id = %s", (inventory_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {'message': '库存记录删除成功'}, 200
        
    except Exception as e:
        return {'message': f'库存记录删除失败: {str(e)}'}, 500

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前用户的角色和门店信息
        cursor.execute("""
            SELECT role, store_id, username 
            FROM users 
            WHERE user_id = %s
        """, (current_user_id,))
        user_info = cursor.fetchone()
        
        if not user_info:
            return {'message': '用户信息不存在'}, 404
            
        user_role = user_info[0]
        user_store_id = user_info[1]
        username = user_info[2]
        
        # 根据用户角色决定查询范围
        store_filter = ""
        store_params = []
        
        if user_role == 'system_admin':
            # 系统管理员可以看到所有门店数据
            pass
        else:
            # 门店经理和收银员只能看到自己门店的数据
            if user_store_id:
                store_filter = "AND store_id = %s"
                store_params = [user_store_id]
            else:
                return {'message': '用户未关联任何门店'}, 403
        
        # 检查总的销售记录数（带权限过滤）
        total_query = f"SELECT COUNT(*) FROM sales WHERE 1=1 {store_filter}"
        cursor.execute(total_query, store_params)
        total_sales_count = cursor.fetchone()[0]
        
        # 检查最近7天的销售记录数（带权限过滤）
        recent_query = f"""
            SELECT COUNT(*) FROM sales 
            WHERE sale_timestamp >= CURRENT_DATE - INTERVAL '7 days' {store_filter}
        """
        cursor.execute(recent_query, store_params)
        recent_sales_count = cursor.fetchone()[0]
        
        # 直接按日期字符串分组汇总销售数据
        from datetime import date, timedelta, datetime
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        sales_by_date = {}
        max_amount = 0
        
        # 获取所有销售记录并在Python中进行汇总（带权限过滤）
        sales_query = f"""
            SELECT sale_timestamp, total_amount
            FROM sales
            WHERE sale_timestamp >= CURRENT_DATE - INTERVAL '7 days' {store_filter}
            ORDER BY sale_timestamp
        """
        cursor.execute(sales_query, store_params)
        
        all_sales = cursor.fetchall()
        
        # 在Python中按日期汇总
        for row in all_sales:
            timestamp = row[0]
            amount = float(row[1]) if row[1] else 0
            
            # 提取日期部分
            if isinstance(timestamp, datetime):
                date_str = timestamp.date().isoformat()
            else:
                # 如果是字符串，解析后提取日期
                try:
                    dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                    date_str = dt.date().isoformat()
                except:
                    date_str = str(timestamp)[:10]  # 简单提取前10个字符
            
            if date_str in sales_by_date:
                sales_by_date[date_str] += amount
            else:
                sales_by_date[date_str] = amount
                
            if sales_by_date[date_str] > max_amount:
                max_amount = sales_by_date[date_str]
        
        # 生成最近7天的数据
        sales_trend = []
        for i in range(7):
            target_date = date.today() - timedelta(days=6-i)
            date_str = target_date.isoformat()
            weekday = weekdays[target_date.weekday()]
            amount = sales_by_date.get(date_str, 0)
            
            sales_trend.append({
                'date': date_str,
                'label': weekday,
                'value': amount,
                'percentage': int((amount / max_amount * 100) if max_amount > 0 else 0)
            })
        
        # 获取商品分类统计
        cursor.execute("""
            SELECT 
                pc.name as category_name,
                COUNT(DISTINCT p.product_id) as product_count
            FROM product_categories pc
            LEFT JOIN products p ON pc.category_id = p.category_id
            GROUP BY pc.category_id, pc.name
            ORDER BY product_count DESC
        """)
        
        categories = []
        total_products = 0
        category_colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
        
        for i, row in enumerate(cursor.fetchall()):
            count = row[1] or 0
            categories.append({
                'name': row[0],
                'count': count,
                'color': category_colors[i % len(category_colors)]
            })
            total_products += count
        
        # 计算百分比
        for cat in categories:
            cat['value'] = round((cat['count'] / total_products * 100) if total_products > 0 else 0, 1)
        
        # 获取最近活动（带权限过滤）
        # 修改store_filter中的字段名，加上表别名
        activities_store_filter = store_filter.replace("store_id", "s.store_id") if store_filter else ""
        
        activities_query = f"""
            SELECT 
                'sale' as type,
                'info' as status,
                CONCAT('完成销售订单 #', s.sale_id, '，金额: ¥', s.total_amount) as description,
                s.sale_timestamp as timestamp,
                u.username as user_name
            FROM sales s
            LEFT JOIN users u ON s.cashier_id = u.user_id
            WHERE 1=1 {activities_store_filter}
            ORDER BY s.sale_timestamp DESC
            LIMIT 10
        """
        cursor.execute(activities_query, store_params)
        
        activities = []
        for row in cursor.fetchall():
            timestamp = format_datetime_with_timezone(row[3])
            activities.append({
                'type': row[1],  # 使用status字段作为type
                'description': row[2],
                'time': timestamp,
                'user': row[4] or '系统'
            })
        
        cursor.close()
        conn.close()
        
        return {
            'salesTrend': sales_trend,
            'categories': categories,
            'activities': activities
        }, 200
        
    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        return {'message': '获取统计数据失败'}, 500

# ==================== 权限管理 ====================
@app.route('/api/permissions/features', methods=['GET'])
@jwt_required()
def get_system_features():
    """获取系统功能列表"""
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查当前用户是否为系统管理员
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] != 'system_admin':
            cursor.close()
            conn.close()
            return {'message': '只有系统管理员可以访问权限管理'}, 403
        
        cursor.execute("""
            SELECT feature_id, feature_code, feature_name, description, module, is_active
            FROM system_features
            ORDER BY module, feature_name
        """)
        
        features = cursor.fetchall()
        cursor.close()
        conn.close()
        
        features_list = []
        for feature in features:
            features_list.append({
                'feature_id': feature[0],
                'feature_code': feature[1],
                'feature_name': feature[2],
                'description': feature[3],
                'module': feature[4],
                'is_active': feature[5]
            })
        
        return {'features': features_list}, 200
        
    except Exception as e:
        return {'message': f'获取系统功能失败: {str(e)}'}, 500

@app.route('/api/permissions/roles', methods=['GET'])
@jwt_required()
def get_role_permissions():
    """获取角色权限配置"""
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查当前用户是否为系统管理员
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] != 'system_admin':
            cursor.close()
            conn.close()
            return {'message': '只有系统管理员可以访问权限管理'}, 403
        
        cursor.execute("""
            SELECT rp.role, sf.feature_id, sf.feature_code, sf.feature_name, sf.module,
                   rp.can_view, rp.can_create, rp.can_edit, rp.can_delete
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            WHERE sf.is_active = TRUE
            ORDER BY rp.role, sf.module, sf.feature_name
        """)
        
        permissions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 按角色组织数据
        role_permissions = {}
        for perm in permissions:
            role = perm[0]
            if role not in role_permissions:
                role_permissions[role] = []
            
            role_permissions[role].append({
                'feature_id': perm[1],
                'feature_code': perm[2],
                'feature_name': perm[3],
                'module': perm[4],
                'can_view': perm[5],
                'can_create': perm[6],
                'can_edit': perm[7],
                'can_delete': perm[8]
            })
        
        return {'role_permissions': role_permissions}, 200
        
    except Exception as e:
        return {'message': f'获取角色权限失败: {str(e)}'}, 500

@app.route('/api/permissions/roles/<role>/features/<int:feature_id>', methods=['PUT'])
@jwt_required()
def update_role_permission(role, feature_id):
    """更新角色的功能权限"""
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查当前用户是否为系统管理员
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        user_role = cursor.fetchone()
        
        if not user_role or user_role[0] != 'system_admin':
            cursor.close()
            conn.close()
            return {'message': '只有系统管理员可以修改权限配置'}, 403
        
        data = request.get_json()
        can_view = data.get('can_view', False)
        can_create = data.get('can_create', False)
        can_edit = data.get('can_edit', False)
        can_delete = data.get('can_delete', False)
        
        # 验证角色是否有效
        valid_roles = ['system_admin', 'store_manager', 'cashier']
        if role not in valid_roles:
            cursor.close()
            conn.close()
            return {'message': '无效的角色'}, 400
        
        # 检查功能是否存在
        cursor.execute("SELECT feature_code FROM system_features WHERE feature_id = %s", (feature_id,))
        feature = cursor.fetchone()
        if not feature:
            cursor.close()
            conn.close()
            return {'message': '功能不存在'}, 404
        
        # 防止修改系统管理员的权限管理权限
        if role == 'system_admin' and feature[0] == 'permission_management':
            cursor.close()
            conn.close()
            return {'message': '不能修改系统管理员的权限管理权限'}, 400
        
        # 更新权限
        cursor.execute("""
            UPDATE role_permissions 
            SET can_view = %s, can_create = %s, can_edit = %s, can_delete = %s, updated_at = CURRENT_TIMESTAMP
            WHERE role = %s AND feature_id = %s
        """, (can_view, can_create, can_edit, can_delete, role, feature_id))
        
        if cursor.rowcount == 0:
            # 如果记录不存在，则插入新记录
            cursor.execute("""
                INSERT INTO role_permissions (role, feature_id, can_view, can_create, can_edit, can_delete)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (role, feature_id, can_view, can_create, can_edit, can_delete))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'message': '权限更新成功',
            'role': role,
            'feature_id': feature_id,
            'permissions': {
                'can_view': can_view,
                'can_create': can_create,
                'can_edit': can_edit,
                'can_delete': can_delete
            }
        }, 200
        
    except Exception as e:
        return {'message': f'权限更新失败: {str(e)}'}, 500

@app.route('/api/permissions/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_permissions(user_id):
    """获取用户的权限列表"""
    try:
        current_user_id = int(get_jwt_identity())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查权限：只能查看自己的权限，或者系统管理员可以查看所有用户权限
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        current_user_role = cursor.fetchone()
        
        if not current_user_role:
            cursor.close()
            conn.close()
            return {'message': '当前用户不存在'}, 404
        
        if current_user_id != user_id and current_user_role[0] != 'system_admin':
            cursor.close()
            conn.close()
            return {'message': '只能查看自己的权限'}, 403
        
        # 获取目标用户的角色
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        target_user = cursor.fetchone()
        
        if not target_user:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        target_role = target_user[0]
        
        # 获取该角色的权限
        cursor.execute("""
            SELECT sf.feature_code, sf.feature_name, sf.module,
                   rp.can_view, rp.can_create, rp.can_edit, rp.can_delete
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            WHERE rp.role = %s AND sf.is_active = TRUE
            ORDER BY sf.module, sf.feature_name
        """, (target_role,))
        
        permissions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        permissions_list = []
        for perm in permissions:
            permissions_list.append({
                'feature_code': perm[0],
                'feature_name': perm[1],
                'module': perm[2],
                'can_view': perm[3],
                'can_create': perm[4],
                'can_edit': perm[5],
                'can_delete': perm[6]
            })
        
        return {
            'user_id': user_id,
            'role': target_role,
            'permissions': permissions_list
        }, 200
        
    except Exception as e:
        return {'message': f'获取用户权限失败: {str(e)}'}, 500

@app.route('/api/permissions/check', methods=['POST'])
@jwt_required()
def check_permission():
    """检查用户是否有特定功能的权限"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        feature_code = data.get('feature_code')
        action = data.get('action', 'view')  # view, create, edit, delete
        
        if not feature_code:
            return {'message': '缺少功能代码'}, 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取用户角色
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (current_user_id,))
        user_role = cursor.fetchone()
        
        if not user_role:
            cursor.close()
            conn.close()
            return {'message': '用户不存在'}, 404
        
        role = user_role[0]
        
        # 检查权限
        permission_column = f'can_{action}'
        cursor.execute(f"""
            SELECT {permission_column}
            FROM role_permissions rp
            JOIN system_features sf ON rp.feature_id = sf.feature_id
            WHERE rp.role = %s AND sf.feature_code = %s AND sf.is_active = TRUE
        """, (role, feature_code))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        has_permission = result[0] if result else False
        
        return {
            'user_id': current_user_id,
            'role': role,
            'feature_code': feature_code,
            'action': action,
            'has_permission': has_permission
        }, 200
        
    except Exception as e:
        return {'message': f'权限检查失败: {str(e)}'}, 500

# ==================== 启动服务器 ====================
if __name__ == '__main__':
    print("🚀 启动完整版超市管理系统...")
    print("=" * 60)
    
    try:
        print("📦 初始化数据库表...")
        init_all_tables()
        print("✅ 数据库表创建成功")
        
        print("✅ Flask应用创建成功")
        print("💚 健康检查: http://localhost:5000/health")
        print("🔑 认证API: /api/auth/register, /api/auth/login")
        print("🏪 门店API: /api/stores/")
        print("📦 分类API: /api/categories/")
        print("🏭 供应商API: /api/suppliers/")
        print("📱 商品API: /api/products/")
        print("📊 库存API: /api/inventory/")
        print("💰 销售API: /api/sales/")
        print("=" * 60)
        print("🔥 服务器启动中... (按 Ctrl+C 停止)")
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)