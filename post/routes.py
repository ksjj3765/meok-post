"""
Post Service API Routes
MSA 환경에서 독립적으로 동작하는 Post 서비스 API입니다.
"""

from flask import Blueprint, request, jsonify, abort, current_app
from .models import db, Post, PostReaction, Category
from .services import PostService
from .validators import PostValidator
import uuid
import os
import requests
import json
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime
from functools import wraps

bp = Blueprint('post', __name__)

# ============================================================================
# 유틸리티 함수들
# ============================================================================

def get_config():
    """MSA 서비스 설정값 가져오기"""
    from flask import current_app
    return {
        'USER_SERVICE_URL': current_app.config.get('USER_SERVICE_URL', 'http://localhost:8081'),
        'NOTIFICATION_SERVICE_URL': current_app.config.get('NOTIFICATION_SERVICE_URL', 'http://localhost:8082'),
        'ENVIRONMENT': current_app.config.get('ENVIRONMENT', 'development')
    }

def call_user_service(endpoint, method="GET", data=None, headers=None):
    """User 서비스 호출 (MSA 통신)"""
    try:
        config = get_config()
        url = f"{config['USER_SERVICE_URL']}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.warning(f"User service call failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"User service connection error: {str(e)}")
        return None

def validate_user_exists(user_id):
    """사용자 존재 여부 확인 (개발 환경에서는 검증 건너뛰기)"""
    if get_config()['ENVIRONMENT'] == 'development':
        current_app.logger.info("Development mode: Skipping user validation")
        return True
    
    try:
        user_info = call_user_service(f"/api/users/{user_id}")
        return user_info is not None
    except Exception as e:
        current_app.logger.error(f"User service validation failed: {str(e)}")
        return False

def notify_user_activity(user_id, activity_type, data):
    """사용자 활동 알림 (개발 환경에서는 알림 건너뛰기)"""
    if get_config()['ENVIRONMENT'] == 'development':
        current_app.logger.info("Development mode: Skipping notification")
        return
    
    try:
        notification_data = {
            "user_id": user_id,
            "activity_type": activity_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = requests.post(
            f"{get_config()['NOTIFICATION_SERVICE_URL']}/api/notifications",
            json=notification_data,
            timeout=5
        )
        
        if response.status_code == 200:
            current_app.logger.info(f"Notification sent: {activity_type}")
        else:
            current_app.logger.warning(f"Notification failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Notification service error: {str(e)}")

def generate_id():
    """32자리 UUID 생성"""
    return str(uuid.uuid4()).replace('-', '')

def allowed_file(filename):
    """허용된 이미지 파일 형식 확인"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_locally(file, post_id):
    """로컬에 이미지 저장 (개발 환경용, 운영에서는 S3 사용)"""
    upload_folder = os.path.join(current_app.root_path, 'uploads', str(post_id))
    os.makedirs(upload_folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    timestamp = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(filename)
    safe_filename = f"{name}_{timestamp}{ext}"
    
    file_path = os.path.join(upload_folder, safe_filename)
    file.save(file_path)
    
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            mime_type = f"image/{img.format.lower()}"
    except Exception as e:
        width, height = None, None
        mime_type = file.content_type or 'application/octet-stream'
    
    relative_path = f"/uploads/{post_id}/{safe_filename}"
    
    return {
        's3_url': relative_path,
        'mime_type': mime_type,
        'width': width,
        'height': height
    }

# ============================================================================
# API 응답 표준화
# ============================================================================

def api_response(data=None, message="Success", status_code=200, meta=None):
    """표준화된 API 응답 생성"""
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data
    }
    
    if meta:
        response["meta"] = meta
    
    return jsonify(response), status_code

def api_error(message="Error", status_code=400, details=None):
    """표준화된 API 에러 응답 생성"""
    response = {
        "success": False,
        "message": message,
        "error": {
            "code": status_code,
            "details": details
        }
    }
    
    return jsonify(response), status_code

# ============================================================================
# 게시글 API 엔드포인트
# ============================================================================

@bp.route('/posts', methods=['GET'])
def list_posts():
    """
    게시글 목록 조회
    ---
    tags:
      - Posts
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: 페이지 번호
      - name: per_page
        in: query
        type: integer
        default: 10
        maximum: 50
        description: 페이지당 항목 수
      - name: q
        in: query
        type: string
        description: 검색어 (제목, 내용)
      - name: visibility
        in: query
        type: string
        enum: [PUBLIC, PRIVATE, UNLISTED]
        default: PUBLIC
        description: 게시글 공개 설정
      - name: status
        in: query
        type: string
        enum: [PUBLISHED, DRAFT, DELETED]
        default: PUBLISHED
        description: 게시글 상태
    responses:
      200:
        description: 게시글 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/Post'
            meta:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)
        q = request.args.get('q', '').strip()
        visibility = request.args.get('visibility', 'PUBLIC')
        status = request.args.get('status', None)  # 기본값 제거하여 모든 상태 조회
        category_id = request.args.get('category_id', None)  # 카테고리 필터
        sort = request.args.get('sort', 'latest')  # 정렬 방식 (latest: 최신순, popular: 인기순)

        query = Post.query.filter_by(visibility=visibility)
        if status:
            query = query.filter_by(status=status)
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if q:
            # SQLite에서는 LIKE 검색 사용
            query = query.filter(
                db.or_(
                    Post.title.like(f'%{q}%'),
                    Post.content_md.like(f'%{q}%')
                )
            )

        # 정렬 적용
        if sort == 'popular':
            query = query.order_by(Post.like_count.desc(), Post.created_at.desc())
        else:  # latest (기본값)
            query = query.order_by(Post.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        items = [{
            "id": p.id,
            "title": p.title,
            "content_md": p.content_md,
            "content_s3url": p.content_s3url,
            "author_id": p.author_id,
            "visibility": p.visibility,
            "status": p.status,
            "view_count": p.view_count,
            "like_count": p.like_count,
            "comment_count": p.comment_count,
            "category": {
                "id": p.category.id,
                "name": p.category.name,
                "description": p.category.description
            } if p.category else None,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        } for p in pagination.items]

        meta = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }

        return api_response(data=items, meta=meta)
        
    except Exception as e:
        current_app.logger.error(f"Error in list_posts: {str(e)}")
        return api_error("게시글 목록 조회 중 오류가 발생했습니다", 500)

@bp.route('/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """
    게시글 단건 조회
    ---
    tags:
      - Posts
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
        description: 게시글 ID
    responses:
      200:
        description: 게시글 조회 성공
        schema:
          $ref: '#/definitions/Post'
      404:
        description: 게시글을 찾을 수 없음
    """
    try:
        post = Post.query.get(post_id)
        if not post:
            return api_error("게시글을 찾을 수 없습니다", 404)
            
        post.view_count += 1
        db.session.commit()
        
        data = {
            "id": post.id,
            "title": post.title,
            "content_md": post.content_md,
            "content_s3url": post.content_s3url,
            "author_id": post.author_id,
            "visibility": post.visibility,
            "status": post.status,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "category": {
                "id": post.category.id,
                "name": post.category.name,
                "description": post.category.description
            } if post.category else None,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat() if post.updated_at else None
        }
        
        return api_response(data=data)
        
    except Exception as e:
        current_app.logger.error(f"Error in get_post: {str(e)}")
        return api_error("게시글 조회 중 오류가 발생했습니다", 500)





@bp.route('/posts', methods=['POST'])
def create_post():
    """
    게시글 생성
    ---
    tags:
      - Posts
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - author_id
          properties:
            title:
              type: string
              description: 게시글 제목
            content_md:
              type: string
              description: 마크다운 내용
            content_s3url:
              type: string
              description: S3 URL
            author_id:
              type: string
              description: 작성자 ID
            visibility:
              type: string
              enum: [PUBLIC, PRIVATE, UNLISTED]
              default: PUBLIC
            status:
              type: string
              enum: [PUBLISHED, DRAFT]
              default: DRAFT
    responses:
      201:
        description: 게시글 생성 성공
      400:
        description: 잘못된 요청 데이터
    """
    try:
        data = request.get_json(force=True, silent=False)
        title = (data.get('title') or '').strip()
        content_md = (data.get('content_md') or '').strip()
        content_s3url = data.get('content_s3url', '').strip()
        author_id = data.get('author_id')
        visibility = data.get('visibility', 'PUBLIC')
        status = data.get('status', 'DRAFT')
        
        category_id = data.get('category_id')
        if not title or not author_id or not category_id:
            return api_error("제목, 작성자 ID, 카테고리는 필수입니다", 400)
        
        # 카테고리 존재 여부 확인
        category = Category.query.get(category_id)
        if not category:
            return api_error("존재하지 않는 카테고리입니다", 400)

        # MSA: User 서비스에서 사용자 존재 여부 확인
        if not validate_user_exists(author_id):
            return api_error("존재하지 않는 사용자입니다", 400)

        post = Post(
            id=generate_id(),
            title=title,
            content_md=content_md if content_md else None,
            content_s3url=content_s3url if content_s3url else None,
            author_id=author_id,
            category_id=category_id,
            visibility=visibility,
            status=status
        )
        
        db.session.add(post)
        
        db.session.commit()
        
        # MSA: Notification 서비스로 사용자 활동 알림
        notify_user_activity(author_id, "POST_CREATED", {
            "post_id": post.id,
            "title": post.title
        })
        
        return api_response(
            data={"id": post.id}, 
            message="게시글이 성공적으로 생성되었습니다", 
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_post: {str(e)}")
        return api_error("게시글 생성 중 오류가 발생했습니다", 500)

@bp.route('/posts/<post_id>', methods=['PUT', 'PATCH'])
def update_post(post_id):
    """
    게시글 수정
    ---
    tags:
      - Posts
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
        description: 게시글 ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            content_md:
              type: string
            content_s3url:
              type: string
            author_id:
              type: string
            visibility:
              type: string
              enum: [PUBLIC, PRIVATE, UNLISTED]
            status:
              type: string
              enum: [PUBLISHED, DRAFT]
    responses:
      200:
        description: 게시글 수정 성공
      404:
        description: 게시글을 찾을 수 없음
    """
    try:
        post = Post.query.get(post_id)
        if not post:
            return api_error("게시글을 찾을 수 없습니다", 404)
        data = request.get_json(force=True, silent=False)

        if request.method == 'PUT':
            title = (data.get('title') or '').strip()
            content_md = (data.get('content_md') or '').strip()
            content_s3url = data.get('content_s3url', '').strip()
            author_id = data.get('author_id')
            visibility = data.get('visibility', 'PUBLIC')
            status = data.get('status', 'DRAFT')
            
            if not title or not author_id:
                return api_error("제목과 작성자 ID는 필수입니다", 400)
                
            post.title = title
            post.content_md = content_md if content_md else None
            post.content_s3url = content_s3url if content_s3url else None
            post.author_id = author_id
            post.visibility = visibility
            post.status = status
        else:
            if 'title' in data:
                post.title = (data['title'] or '').strip()
            if 'content_md' in data:
                post.content_md = (data['content_md'] or '').strip()
            if 'content_s3url' in data:
                post.content_s3url = (data['content_s3url'] or '').strip()
            if 'author_id' in data:
                post.author_id = data['author_id']
            if 'visibility' in data:
                post.visibility = data['visibility']
            if 'status' in data:
                post.status = data['status']

        db.session.commit()
        return api_response(message="게시글이 성공적으로 수정되었습니다")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in update_post: {str(e)}")
        return api_error("게시글 수정 중 오류가 발생했습니다", 500)

@bp.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """
    게시글 삭제
    ---
    tags:
      - Posts
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
        description: 게시글 ID
    responses:
      200:
        description: 게시글 삭제 성공
      404:
        description: 게시글을 찾을 수 없음
    """
    try:
        post = Post.query.get(post_id)
        if not post:
            return api_error("게시글을 찾을 수 없습니다", 404)
        post.status = 'DELETED'
        db.session.commit()
        return api_response(message="게시글이 성공적으로 삭제되었습니다")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_post: {str(e)}")
        return api_error("게시글 삭제 중 오류가 발생했습니다", 500)

# ============================================================================
# 게시글 반응 API
# ============================================================================

@bp.route('/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    """
    게시글 좋아요 (한 유저당 한 게시글에 한 번만)
    ---
    tags:
      - Reactions
    parameters:
      - name: post_id
        in: path
        type: string
        required: true
        description: 게시글 ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: string
              description: 사용자 ID
    responses:
      200:
        description: 좋아요 처리 성공
      400:
        description: 잘못된 요청 데이터
      409:
        description: 이미 좋아요를 누른 게시글
    """
    try:
        post = Post.query.get(post_id)
        if not post:
            return api_error("게시글을 찾을 수 없습니다", 404)
        
        data = request.get_json(force=True, silent=False)
        user_id = data.get('user_id')
        
        if not user_id:
            return api_error("사용자 ID는 필수입니다", 400)
        
        # 이미 좋아요를 누른 경우
        existing_reaction = PostReaction.query.filter_by(post_id=post_id, user_id=user_id).first()
        if existing_reaction:
            return api_error("이미 좋아요를 누른 게시글입니다", 409)
        
        # 새 좋아요 추가
        reaction = PostReaction(post_id=post_id, user_id=user_id)
        db.session.add(reaction)
        post.like_count += 1
        
        db.session.commit()
        return api_response(data={
            "like_count": post.like_count,
            "message": "좋아요가 추가되었습니다"
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in like_post: {str(e)}")
        return api_error("좋아요 처리 중 오류가 발생했습니다", 500)

# ============================================================================
# 카테고리 API
# ============================================================================

@bp.route('/categories', methods=['GET'])
def list_categories():
    """
    카테고리 목록 조회
    ---
    tags:
      - Categories
    responses:
      200:
        description: 카테고리 목록 조회 성공
    """
    try:
        categories = Category.query.all()
        items = [{
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "created_at": c.created_at.isoformat()
        } for c in categories]
        
        return api_response(data=items)
        
    except Exception as e:
        current_app.logger.error(f"Error in list_categories: {str(e)}")
        return api_error("카테고리 목록 조회 중 오류가 발생했습니다", 500)

@bp.route('/categories', methods=['POST'])
def create_category():
    """
    새 카테고리 생성
    ---
    tags:
      - Categories
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 카테고리 이름
            description:
              type: string
              description: 카테고리 설명
    responses:
      201:
        description: 카테고리 생성 성공
      400:
        description: 잘못된 요청 데이터
    """
    try:
        data = request.get_json(force=True, silent=False)
        name = data.get('name', '').strip()
        
        if not name:
            return api_error("카테고리 이름은 필수입니다", 400)
        
        # 중복 카테고리 확인
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return api_error("이미 존재하는 카테고리입니다", 400)
        
        category = Category(
            name=name,
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        
        return api_response(data={
            "id": category.id,
            "name": category.name,
            "description": category.description
        }, message="카테고리가 생성되었습니다")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_category: {str(e)}")
        return api_error("카테고리 생성 중 오류가 발생했습니다", 500)

# ============================================================================
# 태그 API
# ============================================================================

@bp.route('/tags', methods=['GET'])
def list_tags():
    """
    태그 목록 조회
    ---
    tags:
      - Tags
    responses:
      200:
        description: 태그 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/Tag'
    """
    try:
        tags = Tag.query.all()
        data = [{"id": t.id, "name": t.name} for t in tags]
        return api_response(data=data)
        
    except Exception as e:
        current_app.logger.error(f"Error in list_tags: {str(e)}")
        return api_error("태그 목록 조회 중 오류가 발생했습니다", 500)

@bp.route('/tags', methods=['POST'])
def create_tag():
    """
    새 태그 생성
    ---
    tags:
      - Tags
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 태그 이름
    responses:
      201:
        description: 태그 생성 성공
      400:
        description: 잘못된 요청 데이터
    """
    try:
        data = request.get_json(force=True, silent=False)
        name = (data.get('name') or '').strip()
        
        if not name:
            return api_error("태그 이름은 필수입니다", 400)
        
        tag = Tag(name=name)
        db.session.add(tag)
        db.session.commit()
        
        return api_response(
            data={"id": tag.id, "name": tag.name}, 
            message="태그가 성공적으로 생성되었습니다", 
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_tag: {str(e)}")
        return api_error("태그 생성 중 오류가 발생했습니다", 500)

# ============================================================================
# 이미지 관리 API
# ============================================================================



