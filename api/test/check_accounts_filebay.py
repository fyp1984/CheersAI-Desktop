#!/usr/bin/env python3
"""查看所有账号及其 FileBay 配置信息"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import json
from flask import Flask
from extensions.ext_database import db
from models.account import Account, TenantAccountJoin, Tenant
from sqlalchemy import func


def print_separator(char="=", length=100):
    """打印分隔线"""
    print(char * length)


def mask_token(token):
    """脱敏 Token"""
    if not token:
        return "无"
    if len(token) <= 20:
        return "****"
    return f"{token[:10]}...{token[-10:]}"


def check_accounts():
    """查看所有账号及其配置"""
    from configs import dify_config
    
    # Create Flask app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        print_separator()
        print("账号和 FileBay 配置清单")
        print_separator()
        
        # 查询所有账号
        accounts = db.session.query(Account).order_by(Account.created_at.desc()).all()
        
        print(f"\n总账号数: {len(accounts)}")
        
        # 统计信息
        total_accounts = len(accounts)
        accounts_with_config = 0
        accounts_without_config = 0
        
        for idx, account in enumerate(accounts, 1):
            print_separator("-")
            print(f"\n[{idx}] 账号信息")
            print_separator("-")
            
            # 基本信息
            print(f"ID:           {account.id}")
            print(f"邮箱:         {account.email}")
            print(f"姓名:         {account.name}")
            print(f"状态:         {account.status}")
            print(f"创建时间:     {account.created_at}")
            print(f"最后登录:     {account.last_login_at or '从未登录'}")
            
            # 查询工作空间信息
            tenant_joins = db.session.query(TenantAccountJoin, Tenant).join(
                Tenant, TenantAccountJoin.tenant_id == Tenant.id
            ).filter(
                TenantAccountJoin.account_id == account.id
            ).all()
            
            if tenant_joins:
                print(f"\n工作空间数量: {len(tenant_joins)}")
                for tj, tenant in tenant_joins:
                    current_marker = " [当前]" if tj.current else ""
                    print(f"  - {tenant.name} (角色: {tj.role}){current_marker}")
            else:
                print(f"\n工作空间数量: 0")
            
            # FileBay 配置
            print(f"\nFileBay 配置:")
            
            config = account.custom_config_dict
            
            if config and config.get('gitea_url'):
                accounts_with_config += 1
                print(f"  状态:       ✓ 已配置")
                print(f"  URL:        {config.get('gitea_url')}")
                print(f"  Owner:      {config.get('gitea_owner')}")
                print(f"  Repo:       {config.get('gitea_repo')}")
                print(f"  Token:      {mask_token(config.get('gitea_token'))}")
                
                # 显示完整配置（JSON 格式）
                print(f"\n  完整配置 (JSON):")
                config_display = config.copy()
                if config_display.get('gitea_token'):
                    config_display['gitea_token'] = mask_token(config_display['gitea_token'])
                print(f"  {json.dumps(config_display, indent=4, ensure_ascii=False)}")
            else:
                accounts_without_config += 1
                print(f"  状态:       ✗ 未配置")
                if account.custom_config:
                    print(f"  原始数据:   {account.custom_config}")
        
        # 汇总统计
        print_separator()
        print("\n统计汇总")
        print_separator()
        print(f"总账号数:           {total_accounts}")
        print(f"已配置 FileBay:     {accounts_with_config} ({accounts_with_config/total_accounts*100:.1f}%)")
        print(f"未配置 FileBay:     {accounts_without_config} ({accounts_without_config/total_accounts*100:.1f}%)")
        
        # 按邮箱域名统计
        print(f"\n按邮箱域名统计:")
        domain_stats = {}
        for account in accounts:
            domain = account.email.split('@')[-1] if '@' in account.email else 'unknown'
            if domain not in domain_stats:
                domain_stats[domain] = {'total': 0, 'configured': 0}
            domain_stats[domain]['total'] += 1
            if account.custom_config_dict and account.custom_config_dict.get('gitea_url'):
                domain_stats[domain]['configured'] += 1
        
        for domain, stats in sorted(domain_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            print(f"  {domain:30} 总数: {stats['total']:3}  已配置: {stats['configured']:3}")
        
        # 最近登录的账号
        print(f"\n最近登录的 5 个账号:")
        recent_logins = db.session.query(Account).filter(
            Account.last_login_at.isnot(None)
        ).order_by(Account.last_login_at.desc()).limit(5).all()
        
        for account in recent_logins:
            config_status = "✓" if (account.custom_config_dict and account.custom_config_dict.get('gitea_url')) else "✗"
            print(f"  {config_status} {account.email:40} {account.last_login_at}")
        
        print_separator()


def check_specific_account(email):
    """查看特定账号的详细信息"""
    from configs import dify_config
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        account = db.session.query(Account).filter_by(email=email).first()
        
        if not account:
            print(f"✗ 未找到账号: {email}")
            return
        
        print_separator()
        print(f"账号详细信息: {email}")
        print_separator()
        
        # 基本信息
        print(f"\n基本信息:")
        print(f"  ID:               {account.id}")
        print(f"  邮箱:             {account.email}")
        print(f"  姓名:             {account.name}")
        print(f"  状态:             {account.status}")
        print(f"  界面语言:         {account.interface_language or '未设置'}")
        print(f"  时区:             {account.timezone or '未设置'}")
        print(f"  创建时间:         {account.created_at}")
        print(f"  更新时间:         {account.updated_at}")
        print(f"  最后登录时间:     {account.last_login_at or '从未登录'}")
        print(f"  最后登录IP:       {account.last_login_ip or '无'}")
        print(f"  最后活跃时间:     {account.last_active_at}")
        print(f"  初始化时间:       {account.initialized_at or '未初始化'}")
        
        # 工作空间信息
        print(f"\n工作空间信息:")
        tenant_joins = db.session.query(TenantAccountJoin, Tenant).join(
            Tenant, TenantAccountJoin.tenant_id == Tenant.id
        ).filter(
            TenantAccountJoin.account_id == account.id
        ).all()
        
        if tenant_joins:
            for tj, tenant in tenant_joins:
                current_marker = " [当前]" if tj.current else ""
                print(f"  工作空间: {tenant.name}{current_marker}")
                print(f"    - ID:         {tenant.id}")
                print(f"    - 角色:       {tj.role}")
                print(f"    - 状态:       {tenant.status}")
                print(f"    - 计划:       {tenant.plan}")
                print(f"    - 加入时间:   {tj.created_at}")
                print(f"    - 邀请人:     {tj.invited_by or '系统创建'}")
        else:
            print(f"  无工作空间")
        
        # FileBay 配置
        print(f"\nFileBay 配置:")
        config = account.custom_config_dict
        
        if config and config.get('gitea_url'):
            print(f"  状态:             ✓ 已配置")
            print(f"  URL:              {config.get('gitea_url')}")
            print(f"  Owner:            {config.get('gitea_owner')}")
            print(f"  Repo:             {config.get('gitea_repo')}")
            print(f"  Token (脱敏):     {mask_token(config.get('gitea_token'))}")
            print(f"  Token (完整):     {config.get('gitea_token')}")
            
            print(f"\n  完整配置 (JSON):")
            print(json.dumps(config, indent=4, ensure_ascii=False))
            
            # 测试配置
            print(f"\n  配置验证:")
            if config.get('gitea_url') and config.get('gitea_token'):
                print(f"    ✓ URL 和 Token 都已配置")
                
                # 尝试调用 Enterprise API
                try:
                    import requests
                    api_url = f"http://localhost:5001/inner/api/enterprise/gitea/config"
                    response = requests.get(api_url, params={'email': email}, timeout=5)
                    
                    if response.status_code == 200:
                        api_config = response.json()
                        print(f"    ✓ Enterprise API 返回成功")
                        print(f"      URL:   {api_config.get('gitea_url')}")
                        print(f"      Owner: {api_config.get('gitea_owner')}")
                        print(f"      Repo:  {api_config.get('gitea_repo')}")
                        
                        # 验证一致性
                        if api_config.get('gitea_url') == config.get('gitea_url'):
                            print(f"    ✓ API 配置与数据库一致")
                        else:
                            print(f"    ✗ API 配置与数据库不一致")
                    else:
                        print(f"    ✗ Enterprise API 返回错误: {response.status_code}")
                except Exception as e:
                    print(f"    ✗ 无法调用 Enterprise API: {e}")
            else:
                print(f"    ✗ 配置不完整")
        else:
            print(f"  状态:             ✗ 未配置")
            print(f"  原始数据:         {account.custom_config or '无'}")
        
        # 原始 custom_config
        print(f"\n原始 custom_config 字段:")
        print(f"  {account.custom_config or '无'}")
        
        print_separator()


def export_to_csv():
    """导出账号信息到 CSV"""
    from configs import dify_config
    import csv
    from datetime import datetime
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = dify_config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = dify_config.SQLALCHEMY_ENGINE_OPTIONS
    
    db.init_app(app)
    
    with app.app_context():
        accounts = db.session.query(Account).order_by(Account.created_at.desc()).all()
        
        filename = f"accounts_filebay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', '邮箱', '姓名', '状态', '创建时间', '最后登录',
                'FileBay状态', 'FileBay_URL', 'FileBay_Owner', 'FileBay_Repo', 'FileBay_Token'
            ])
            
            for account in accounts:
                config = account.custom_config_dict
                has_config = config and config.get('gitea_url')
                
                writer.writerow([
                    account.id,
                    account.email,
                    account.name,
                    account.status,
                    account.created_at,
                    account.last_login_at or '',
                    '已配置' if has_config else '未配置',
                    config.get('gitea_url', '') if has_config else '',
                    config.get('gitea_owner', '') if has_config else '',
                    config.get('gitea_repo', '') if has_config else '',
                    mask_token(config.get('gitea_token', '')) if has_config else '',
                ])
        
        print(f"✓ 已导出到: {filename}")
        print(f"  总账号数: {len(accounts)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "export":
            # 导出到 CSV
            export_to_csv()
        elif command == "check":
            if len(sys.argv) > 2:
                # 查看特定账号
                email = sys.argv[2]
                check_specific_account(email)
            else:
                print("用法: python check_accounts_filebay.py check <email>")
        else:
            print("未知命令")
            print("用法:")
            print("  python check_accounts_filebay.py              # 查看所有账号")
            print("  python check_accounts_filebay.py check <email>  # 查看特定账号")
            print("  python check_accounts_filebay.py export       # 导出到 CSV")
    else:
        # 查看所有账号
        check_accounts()
