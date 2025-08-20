"""
Post Service Business Logic Layer
비즈니스 로직을 담당하는 서비스 클래스들입니다.
"""

from .models import db, Post, PostReaction
from datetime import datetime
import uuid

class PostService:
    """게시글 관련 비즈니스 로직"""
    
    @staticmethod
    def create_post(title, content_md, content_s3url, author_id, visibility='PUBLIC', status='DRAFT'):
        """게시글 생성"""
        post = Post(
            id=str(uuid.uuid4()).replace('-', ''),
            title=title,
            content_md=content_md,
            content_s3url=content_s3url,
            author_id=author_id,
            visibility=visibility,
            status=status
        )
        
        db.session.add(post)
        db.session.commit()
        return post
    
    @staticmethod
    def get_post(post_id):
        """게시글 조회 (조회수 증가)"""
        post = Post.query.get(post_id)
        if post:
            post.view_count += 1
            db.session.commit()
        return post
    
    @staticmethod
    def update_post(post_id, **kwargs):
        """게시글 수정"""
        post = Post.query.get(post_id)
        if not post:
            return None
            
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        return post
    
    @staticmethod
    def delete_post(post_id):
        """게시글 삭제 (소프트 삭제)"""
        post = Post.query.get(post_id)
        if not post:
            return False
            
        post.status = 'DELETED'
        post.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def search_posts(q, visibility='PUBLIC', status='PUBLISHED', page=1, per_page=10):
        """게시글 검색"""
        query = Post.query.filter_by(visibility=visibility, status=status)
        
        if q:
            query = query.filter(db.text("MATCH(title, content_md) AGAINST(:q IN BOOLEAN MODE)"), q=q)
        
        return query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )



class ReactionService:
    """반응 관련 비즈니스 로직"""
    
    @staticmethod
    def toggle_reaction(post_id, user_id, action):
        """게시글 반응 토글"""
        post = Post.query.get(post_id)
        if not post:
            return None
            
        existing_reaction = PostReaction.query.filter_by(
            post_id=post_id, user_id=user_id
        ).first()
        
        if existing_reaction:
            if existing_reaction.type == action:
                # 같은 리액션 제거 (토글)
                db.session.delete(existing_reaction)
                if action == 'LIKE':
                    post.like_count = max(0, post.like_count - 1)
                else:
                    post.like_count = max(0, post.like_count - 1)
            else:
                # 다른 리액션으로 변경
                existing_reaction.type = action
                if action == 'LIKE':
                    post.like_count += 1
                    post.like_count = max(0, post.like_count - 1)
                else:
                    post.like_count = max(0, post.like_count - 1)
                    post.like_count += 1
        else:
            # 새 리액션 추가
            reaction = PostReaction(post_id=post_id, user_id=user_id, type=action)
            db.session.add(reaction)
            if action == 'LIKE':
                post.like_count += 1
            else:
                post.like_count += 1
        
        db.session.commit()
        return post





