#!/usr/bin/env python3
"""
postdb 데이터베이스 구조 확인 스크립트
"""

import pymysql

def check_postdb_structure():
    """postdb 데이터베이스 구조 확인"""
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3307,
            user='root',
            password='1234',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("=== postdb 데이터베이스 테이블 ===")
        cursor.execute("USE postdb")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            for table in tables:
                table_name = table[0]
                print(f"\n--- {table_name} 테이블 구조 ---")
                
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                print(f"{'필드명':<20} {'타입':<20} {'NULL':<8} {'키':<8} {'기본값':<15}")
                print("-" * 80)
                
                for col in columns:
                    field, type_name, null, key, default, extra = col
                    print(f"{field:<20} {type_name:<20} {null:<8} {key:<8} {str(default):<15}")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"총 레코드 수: {count}")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    print("샘플 데이터:")
                    for row in sample_data:
                        print(f"  {row}")
        else:
            print("postdb에 테이블이 없습니다.")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")

if __name__ == "__main__":
    check_postdb_structure()
