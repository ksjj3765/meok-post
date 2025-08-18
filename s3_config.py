"""
AWS S3 Configuration for Post Service
개발 환경: 로컬 파일 시스템, 운영 환경: S3 + CloudFront CDN
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class S3Config:
    """AWS S3 설정 및 연동 클래스"""
    
    def __init__(self):
        # AWS 자격 증명 (환경 변수에서 설정)
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.environ.get('AWS_REGION', 'ap-northeast-2')  # 서울 리전
        
        # S3 버킷 및 CDN 설정
        self.s3_bucket_name = os.environ.get('S3_BUCKET_NAME', 'meokgroom-post-images')
        self.cdn_domain = os.environ.get('CDN_DOMAIN', '')  # CloudFront 도메인
        
        self.s3_client = None
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """S3 클라이언트 초기화"""
        if self.aws_access_key_id and self.aws_secret_access_key:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.aws_region
                )
            except Exception as e:
                print(f"S3 클라이언트 초기화 실패: {e}")
                self.s3_client = None
    
    def is_configured(self):
        """S3 설정 완료 여부 확인"""
        return (
            self.aws_access_key_id is not None and
            self.aws_secret_access_key is not None and
            self.s3_client is not None
        )
    
    def get_s3_url(self, key):
        """S3 객체 URL 생성 (CDN 우선, 없으면 S3 직접)"""
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        else:
            return f"https://{self.s3_bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"
    
    def upload_file(self, file_path, s3_key):
        """파일을 S3에 업로드"""
        if not self.is_configured():
            print("S3가 설정되지 않았습니다.")
            return False
        
        try:
            self.s3_client.upload_file(file_path, self.s3_bucket_name, s3_key)
            print(f"파일 업로드 성공: {s3_key}")
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"S3 업로드 실패: {e}")
            return False
    
    def delete_file(self, s3_key):
        """S3에서 파일 삭제"""
        if not self.is_configured():
            print("S3가 설정되지 않았습니다.")
            return False
        
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=s3_key)
            print(f"파일 삭제 성공: {s3_key}")
            return True
        except (ClientError, NoCredentialsError) as e:
            print(f"S3 삭제 실패: {e}")
            return False
    
    def get_file_info(self, s3_key):
        """S3 파일 정보 조회"""
        if not self.is_configured():
            print("S3가 설정되지 않았습니다.")
            return None
        
        try:
            response = self.s3_client.head_object(Bucket=self.s3_bucket_name, Key=s3_key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag')
            }
        except ClientError as e:
            print(f"파일 정보 조회 실패: {e}")
            return None

# 전역 S3 설정 인스턴스
s3_config = S3Config()

def get_s3_url(key):
    """S3 URL 생성 헬퍼 함수"""
    return s3_config.get_s3_url(key)

def is_s3_configured():
    """S3 설정 완료 여부 확인 헬퍼 함수"""
    return s3_config.is_configured()


