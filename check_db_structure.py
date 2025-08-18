#!/usr/bin/env python3
"""
데이터베이스 구조 확인 스크립트
"""

import pymysql
from config import Config

def check_database_structure():
    """데이터베이스 구조 확인"""
    try:
        # 데이터베이스 연결
        connection = pymysql.connect(
            host='localhost',
            port=3307,
            user='root',
            password='1234',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("=== 데이터베이스 목록 ===")
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for db in databases:
            print(f"- {db[0]}")
        
        # post_service 데이터베이스가 있는지 확인
        post_service_exists = any(db[0] == 'post_service' for db in databases)
        
        if post_service_exists:
            print("\n=== post_service 데이터베이스 테이블 ===")
            cursor.execute("USE post_service")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"\n--- {table_name} 테이블 구조 ---")
                
                # 테이블 구조 확인
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                print(f"{'필드명':<20} {'타입':<20} {'NULL':<8} {'키':<8} {'기본값':<15}")
                print("-" * 80)
                
                for col in columns:
                    field, type_name, null, key, default, extra = col
                    print(f"{field:<20} {type_name:<20} {null:<8} {key:<8} {str(default):<15}")
                
                # 테이블 데이터 수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"총 레코드 수: {count}")
                
                # 샘플 데이터 확인 (최대 3개)
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    print("샘플 데이터:")
                    for row in sample_data:
                        print(f"  {row}")
        else:
            print("\npost_service 데이터베이스가 존재하지 않습니다.")
            print("데이터베이스를 생성하고 테이블을 만들어야 합니다.")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")

if __name__ == "__main__":
    check_database_structure()
