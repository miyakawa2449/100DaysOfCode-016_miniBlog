#!/usr/bin/env python3
"""
SQLiteからMySQLへのデータ移行スクリプト
"""

import sqlite3
import pymysql
import os
from datetime import datetime

def connect_sqlite():
    """SQLite接続"""
    return sqlite3.connect('instance/miniblog.db')

def connect_mysql():
    """MySQL接続"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='miniblog',
        charset='utf8mb4'
    )

def get_mysql_columns(cursor, table_name):
    """MySQLテーブルの実際のカラムを取得"""
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    return [col[0] for col in columns]

def migrate_table(sqlite_cursor, mysql_cursor, table_name, sqlite_columns):
    """テーブルデータを移行"""
    print(f"移行中: {table_name}")
    
    # MySQLの実際のカラムを取得
    mysql_columns = get_mysql_columns(mysql_cursor, table_name)
    
    # 共通カラムのみを使用
    common_columns = [col for col in sqlite_columns if col in mysql_columns]
    excluded_columns = [col for col in sqlite_columns if col not in mysql_columns]
    
    if excluded_columns:
        print(f"  除外されたカラム: {excluded_columns}")
    
    print(f"  使用カラム: {common_columns}")
    
    # SQLiteから共通カラムのみを読み取り
    column_indices = [sqlite_columns.index(col) for col in common_columns]
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    all_rows = sqlite_cursor.fetchall()
    
    if not all_rows:
        print(f"  {table_name}: データなし")
        return
    
    # 共通カラムのデータのみを抽出
    filtered_rows = []
    for row in all_rows:
        filtered_row = [row[i] for i in column_indices]
        filtered_rows.append(filtered_row)
    
    # MySQLに挿入
    placeholders = ', '.join(['%s'] * len(common_columns))
    query = f"INSERT INTO {table_name} ({', '.join(common_columns)}) VALUES ({placeholders})"
    
    try:
        mysql_cursor.executemany(query, filtered_rows)
        print(f"  {table_name}: {len(filtered_rows)} レコード移行完了")
    except Exception as e:
        print(f"  {table_name}: エラー - {e}")
        # エラーの場合は個別に挿入を試行
        for i, row in enumerate(filtered_rows):
            try:
                mysql_cursor.execute(query, row)
            except Exception as row_error:
                print(f"    レコード {i+1}: {row_error}")

def get_actual_columns(cursor, table_name):
    """実際のテーブル構造を取得"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [col[1] for col in columns]  # カラム名のリストを返す

def main():
    print("SQLite → MySQL データ移行開始")
    print("=" * 50)
    
    # 接続
    sqlite_conn = connect_sqlite()
    mysql_conn = connect_mysql()
    
    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # 実際のテーブル構造に基づく移行順序（外部キー制約を考慮）
        tables_to_migrate = [
            'users',
            'categories', 
            'articles',
            'article_categories',
            'comments',
            'uploaded_images'
        ]
        
        # MySQLのauto_increment設定を無効化（IDを保持するため）
        mysql_cursor.execute("SET foreign_key_checks = 0")
        
        # 各テーブルを移行
        for table_name in tables_to_migrate:
            # 実際のカラム構造を取得
            sqlite_columns = get_actual_columns(sqlite_cursor, table_name)
            print(f"\n{table_name} カラム: {sqlite_columns}")
            migrate_table(sqlite_cursor, mysql_cursor, table_name, sqlite_columns)
        
        # 変更をコミット
        mysql_conn.commit()
        
        # auto_increment値をリセット
        for table_name in tables_to_migrate:
            if table_name not in ['article_categories']:  # 中間テーブルは除く
                mysql_cursor.execute(f"SELECT MAX(id) FROM {table_name}")
                max_id = mysql_cursor.fetchone()[0]
                if max_id:
                    mysql_cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {max_id + 1}")
        
        mysql_cursor.execute("SET foreign_key_checks = 1")
        mysql_conn.commit()
        
        print("=" * 50)
        print("データ移行完了！")
        
        # 移行結果確認
        print("\nMySQL データ確認:")
        for table_name in tables_to_migrate:
            mysql_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = mysql_cursor.fetchone()[0]
            print(f"  {table_name}: {count} レコード")
            
    except Exception as e:
        print(f"移行エラー: {e}")
        mysql_conn.rollback()
    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    main()