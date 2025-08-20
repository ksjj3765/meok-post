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
    
    id = db.Column(db.String(32), primary_key=True, default=generate_id)
    author_id = db.Column(db.String(32), nullable=False, index=True)  # userdb.users.id 참조
    category_id = db.Column(db.String(32), db.ForeignKey('categories.id'), nullable=False, index=True)  # 카테고리
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
    
    # 관계 설정
    category = db.relationship('Category', backref='posts')

class Category(db.Model):
    """카테고리 정보"""
    __tablename__ = 'categories'
    id = db.Column(db.String(32), primary_key=True, default=generate_id)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))  # 카테고리 설명
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)

class Tag(db.Model):
    """태그 정보"""
    __tablename__ = 'tags'
    id = db.Column(db.String(32), primary_key=True, default=generate_id)
    name = db.Column(db.String(50), nullable=False, unique=True)


class PostReaction(db.Model):
    """게시글 좋아요 (한 유저당 한 게시글에 한 번만)"""
    __tablename__ = 'post_reactions'
    post_id = db.Column(db.String(32), db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.String(32), db.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    created_at = db.Column(db.DateTime(3), nullable=False, default=datetime.utcnow)
    
    # 복합 기본키로 한 유저당 한 게시글에 한 번만 좋아요 가능
    __table_args__ = (
        db.PrimaryKeyConstraint('post_id', 'user_id'),
    )



