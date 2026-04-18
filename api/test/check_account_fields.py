"""检查 Account 模型的字段"""
from models.account import Account

# 打印 Account 模型的所有字段
print("Account 模型的字段:")
for column in Account.__table__.columns:
    print(f"  - {column.name}: {column.type}")
