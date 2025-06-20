def register_namespaces(api):
    """注册所有API命名空间"""
    from .auth import auth_ns
    from .stores import stores_ns
    from .users import users_ns
    from .work_logs import work_logs_ns
    from .product_categories import categories_ns
    from .suppliers import suppliers_ns
    from .products import products_ns
    from .inventory import inventory_ns
    from .promotions import promotions_ns
    from .sales import sales_ns
    
    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(stores_ns, path='/api/stores')
    api.add_namespace(users_ns, path='/api/users')
    api.add_namespace(work_logs_ns, path='/api/work-logs')
    api.add_namespace(categories_ns, path='/api/categories')
    api.add_namespace(suppliers_ns, path='/api/suppliers')
    api.add_namespace(products_ns, path='/api/products')
    api.add_namespace(inventory_ns, path='/api/inventory')
    api.add_namespace(promotions_ns, path='/api/promotions')
    api.add_namespace(sales_ns, path='/api/sales') 