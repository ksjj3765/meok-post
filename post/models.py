"""
Post Service Database Models
MSA 아키텍처에서 Post 서비스가 관리하는 데이터 구조입니다.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_id():
    """32자리 UUID 생성"""
    return str(uuid.uuid4()).replace('-', '')

class Post(db.Model):
    """게시글 기본 정보 (userdb.users와 author_id로 연결)"""
    __tablename__ = 'posts'
    
    id = db.Column(db.String(26), primary_key=True, default=generate_id)
    author_id = db.Column(db.String(26), nullable=False, index=True)  # userdb.users.id 참조
    title = db.Column(db.String(200), nullable=False)
    content_md = db.Column(db.Text)  # 마크다운 내용
    content_s3url = db.Column(db.String(512))  # S3 URL
    visibility = db.Column(db.Enum('PUBLIC', 'PRIVATE', 'UNLISTED'), nullable=False, default='PUBLIC')
    status = db.Column(db.Enum('PUBLISHED', 'DRAFT', 'DELETED'), nullable=False, default='PUBLISHED')
    view_count = db.Column(db.Integer, nullable=False, default=0)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Tag(db.Model):
    """태그 정보"""
    __tablename__ = 'tags'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class PostTag(db.Model):
    """게시글-태그 연결 (다대다 관계)"""
    __tablename__ = 'post_tags'
    post_id = db.Column(db.String(26), db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    tag_id = db.Column(db.BigInteger, db.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)

class PostReaction(db.Model):
    """게시글 반응 (좋아요/싫어요)"""
    __tablename__ = 'post_reactions'
    post_id = db.Column(db.String(26), db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.String(26), nullable=False, index=True)  # userdb.users.id 참조
    type = db.Column(db.Enum('LIKE', 'DISLIKE'), nullable=False, default='LIKE')
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)

class PostMedia(db.Model):
    """게시글 첨부 이미지 (개발: 로컬, 운영: S3)"""
    __tablename__ = 'post_media'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.String(26), db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, index=True)
    s3_url = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(100))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)

class OutboxEvent(db.Model):
    """이벤트 발행용 (CDC/DMS 수집, MSA 이벤트 스트림)"""
    __tablename__ = 'outbox_events'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    aggregate_id = db.Column(db.String(26), nullable=False, index=True)  # posts.id 등
    event_type = db.Column(db.String(100), nullable=False)  # POST_CREATED 등
    payload_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)

