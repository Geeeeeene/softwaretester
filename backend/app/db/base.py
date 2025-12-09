"""数据库基类"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 注意：不要在这里导入模型，会导致循环导入
# 模型导入应该在需要时进行，或在 app/db/__init__.py 中统一导入
