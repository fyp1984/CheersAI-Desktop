#!/usr/bin/env python
"""
知识库调试工具集

提供一组用于调试和管理知识库文档的工具函数。
可以通过命令行参数指定知识库 ID。

使用示例:
    python knowledge_base_tools.py status --dataset-id <your-dataset-id>
    python knowledge_base_tools.py details --dataset-id <your-dataset-id>
    python knowledge_base_tools.py reset --dataset-id <your-dataset-id>
"""

import argparse
from typing import Optional

import psycopg2


class KnowledgeBaseTools:
    """知识库调试工具类"""
    
    def __init__(self, dataset_id: str, db_config: Optional[dict] = None):
        """
        初始化工具类
        
        Args:
            dataset_id: 知识库 ID
            db_config: 数据库配置，如果为 None 则使用默认配置
        """
        self.dataset_id = dataset_id
        self.db_config = db_config or {
            'host': '127.0.0.1',
            'port': 5432,
            'database': 'dify',
            'user': 'postgres',
            'password': 'difyai123456'
        }
    
    def _get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(**self.db_config)
    
    def check_status_counts(self):
        """检查文档状态统计"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT indexing_status, COUNT(*)
            FROM documents
            WHERE dataset_id = %s
            GROUP BY indexing_status
        """, (self.dataset_id,))
        
        print(f'\n知识库 {self.dataset_id} 文档状态统计:')
        print('-' * 50)
        
        results = cur.fetchall()
        if results:
            total = sum(count for _, count in results)
            for status, count in results:
                percentage = (count / total * 100) if total > 0 else 0
                print(f'  {status:15s}: {count:3d} ({percentage:5.1f}%)')
            print(f'  {"总计":15s}: {total:3d}')
        else:
            print('  没有找到文档')
        
        cur.close()
        conn.close()
    
    def check_doc_details(self, limit: int = 20):
        """
        检查文档详情
        
        Args:
            limit: 显示的文档数量限制
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, indexing_status, created_at, data_source_type
            FROM documents
            WHERE dataset_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (self.dataset_id, limit))
        
        print(f'\n知识库 {self.dataset_id} 最近 {limit} 个文档:')
        print('-' * 100)
        print(f'{"文档名称":<40s} {"状态":<15s} {"数据源":<15s} {"创建时间":<20s}')
        print('-' * 100)
        
        results = cur.fetchall()
        if results:
            for doc_id, name, status, created_at, source_type in results:
                # 截断过长的文件名
                display_name = name[:37] + '...' if len(name) > 40 else name
                print(f'{display_name:<40s} {status:<15s} {source_type:<15s} {str(created_at):<20s}')
        else:
            print('没有找到文档')
        
        cur.close()
        conn.close()
    
    def check_error_docs(self):
        """检查错误文档详情"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, error, created_at
            FROM documents
            WHERE dataset_id = %s
            AND indexing_status = 'error'
            ORDER BY created_at DESC
        """, (self.dataset_id,))
        
        print(f'\n知识库 {self.dataset_id} 错误文档:')
        print('-' * 100)
        
        results = cur.fetchall()
        if results:
            for i, (doc_id, name, error, created_at) in enumerate(results, 1):
                print(f'\n{i}. {name}')
                print(f'   ID: {doc_id}')
                print(f'   创建时间: {created_at}')
                print(f'   错误信息: {error[:200]}...' if len(error) > 200 else f'   错误信息: {error}')
        else:
            print('没有找到错误文档')
        
        cur.close()
        conn.close()
    
    def reset_error_docs(self, confirm: bool = False):
        """
        重置错误文档状态
        
        Args:
            confirm: 是否确认执行（防止误操作）
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        # 先查询错误文档数量
        cur.execute("""
            SELECT COUNT(*)
            FROM documents
            WHERE dataset_id = %s
            AND indexing_status = 'error'
        """, (self.dataset_id,))
        
        count = cur.fetchone()[0]
        
        if count == 0:
            print('没有找到错误文档')
            cur.close()
            conn.close()
            return
        
        print(f'\n找到 {count} 个错误文档')
        
        if not confirm:
            response = input('确认要重置这些文档吗？(yes/no): ')
            if response.lower() != 'yes':
                print('操作已取消')
                cur.close()
                conn.close()
                return
        
        # 执行重置
        cur.execute("""
            UPDATE documents
            SET indexing_status = 'waiting',
                error = NULL,
                updated_at = NOW()
            WHERE dataset_id = %s
            AND indexing_status = 'error'
        """, (self.dataset_id,))
        
        conn.commit()
        print(f'✓ 已重置 {count} 个文档状态为 waiting')
        print('\n请在知识库界面点击"重新索引"按钮来触发处理')
        
        cur.close()
        conn.close()
    
    def check_waiting_docs(self):
        """检查等待处理的文档"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, name, created_at, dataset_process_rule_id
            FROM documents
            WHERE dataset_id = %s
            AND indexing_status = 'waiting'
            ORDER BY created_at DESC
        """, (self.dataset_id,))
        
        print(f'\n知识库 {self.dataset_id} 等待处理的文档:')
        print('-' * 100)
        
        results = cur.fetchall()
        if results:
            for i, (doc_id, name, created_at, rule_id) in enumerate(results, 1):
                rule_status = '✓ 有规则' if rule_id else '✗ 缺少规则'
                print(f'{i}. {name}')
                print(f'   创建时间: {created_at}')
                print(f'   处理规则: {rule_status}')
        else:
            print('没有找到等待处理的文档')
        
        cur.close()
        conn.close()
    
    def get_summary(self):
        """获取知识库摘要信息"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        # 获取基本统计
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN indexing_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN indexing_status = 'error' THEN 1 END) as error,
                COUNT(CASE WHEN indexing_status = 'waiting' THEN 1 END) as waiting,
                COUNT(CASE WHEN indexing_status = 'indexing' THEN 1 END) as indexing
            FROM documents
            WHERE dataset_id = %s
        """, (self.dataset_id,))
        
        stats = cur.fetchone()
        total, completed, error, waiting, indexing = stats
        
        # 获取知识库名称
        cur.execute("""
            SELECT name, created_at
            FROM datasets
            WHERE id = %s
        """, (self.dataset_id,))
        
        dataset_info = cur.fetchone()
        
        print(f'\n{"=" * 60}')
        print('知识库摘要')
        print(f'{"=" * 60}')
        
        if dataset_info:
            print(f'名称: {dataset_info[0]}')
            print(f'创建时间: {dataset_info[1]}')
        
        print(f'ID: {self.dataset_id}')
        print('\n文档统计:')
        print(f'  总计: {total}')
        print(f'  已完成: {completed} ({completed / total * 100:.1f}%)' if total > 0 else '  已完成: 0')
        print(f'  错误: {error} ({error / total * 100:.1f}%)' if total > 0 else '  错误: 0')
        print(f'  等待中: {waiting}')
        print(f'  处理中: {indexing}')
        
        # 健康度评分
        if total > 0:
            health_score = (completed / total) * 100
            if health_score >= 90:
                health_status = '优秀 ✓'
            elif health_score >= 70:
                health_status = '良好'
            elif health_score >= 50:
                health_status = '一般'
            else:
                health_status = '需要关注 ✗'
            
            print(f'\n健康度: {health_score:.1f}% ({health_status})')
        
        print(f'{"=" * 60}\n')
        
        cur.close()
        conn.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='知识库调试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态统计
  python knowledge_base_tools.py status --dataset-id <id>
  
  # 查看文档详情
  python knowledge_base_tools.py details --dataset-id <id>
  
  # 查看错误文档
  python knowledge_base_tools.py errors --dataset-id <id>
  
  # 重置错误文档
  python knowledge_base_tools.py reset --dataset-id <id>
  
  # 查看摘要
  python knowledge_base_tools.py summary --dataset-id <id>
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'details', 'errors', 'reset', 'waiting', 'summary'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        '--dataset-id',
        required=True,
        help='知识库 ID'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='显示的文档数量限制（仅用于 details 命令）'
    )
    
    parser.add_argument(
        '--yes',
        action='store_true',
        help='自动确认操作（用于 reset 命令）'
    )
    
    args = parser.parse_args()
    
    # 创建工具实例
    tools = KnowledgeBaseTools(args.dataset_id)
    
    # 执行命令
    if args.command == 'status':
        tools.check_status_counts()
    elif args.command == 'details':
        tools.check_doc_details(limit=args.limit)
    elif args.command == 'errors':
        tools.check_error_docs()
    elif args.command == 'reset':
        tools.reset_error_docs(confirm=args.yes)
    elif args.command == 'waiting':
        tools.check_waiting_docs()
    elif args.command == 'summary':
        tools.get_summary()


if __name__ == '__main__':
    main()
