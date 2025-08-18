"""
Post Service API Routes
MSA 환경에서 독립적으로 동작하는 Post 서비스 API입니다.
"""

from flask import Blueprint, request, jsonify, abort, current_app
from .models import db, Post, Tag, PostTag, PostReaction, PostMedia, OutboxEvent
import uuid
import os
import requests
import json
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime

bp = Blueprint('post', __name__)

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
# 게시글 API 엔드포인트
# ============================================================================

@bp.route('/posts', methods=['GET'])
def list_posts():
    """게시글 목록 조회 (페이지네이션 + FULLTEXT 검색 + 필터링)"""
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 50)
    q = request.args.get('q', '').strip()
    visibility = request.args.get('visibility', 'PUBLIC')
    status = request.args.get('status', 'PUBLISHED')

    query = Post.query.filter_by(visibility=visibility, status=status)
    
    if q:
        # MySQL FULLTEXT 검색 사용
        query = query.filter(db.text("MATCH(title, content_md) AGAINST(:q IN BOOLEAN MODE)"), q=q)

    pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
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
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat() if p.updated_at else None
    } for p in pagination.items]

    return jsonify({
        "items": items,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages
    })

@bp.route('/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """게시글 단건 조회 (조회수 자동 증가)"""
    post = Post.query.get_or_404(post_id)
    post.view_count += 1
    db.session.commit()
    
    return jsonify({
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
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat() if post.updated_at else None
    })

@bp.route('/posts', methods=['POST'])
def create_post():
    """게시글 생성 (MSA: User 서비스 검증, Notification 서비스 알림)"""
    data = request.get_json(force=True, silent=False)
    title = (data.get('title') or '').strip()
    content_md = (data.get('content_md') or '').strip()
    content_s3url = data.get('content_s3url', '').strip()
    author_id = data.get('author_id')
    visibility = data.get('visibility', 'PUBLIC')
    status = data.get('status', 'DRAFT')
    
    if not title or not author_id:
        abort(400, description="title, author_id are required")

    # MSA: User 서비스에서 사용자 존재 여부 확인
    if not validate_user_exists(author_id):
        abort(400, description="User not found")

    post = Post(
        id=generate_id(),
        title=title,
        content_md=content_md if content_md else None,
        content_s3url=content_s3url if content_s3url else None,
        author_id=author_id,
        visibility=visibility,
        status=status
    )
    
    db.session.add(post)
    
    # Outbox 이벤트 생성 (CDC/DMS 수집용)
    outbox_event = OutboxEvent(
        aggregate_id=post.id,
        event_type='POST_CREATED',
        payload_json={
            'post_id': post.id,
            'author_id': post.author_id,
            'title': post.title,
            'visibility': post.visibility,
            'status': post.status
        }
    )
    db.session.add(outbox_event)
    
    db.session.commit()
    
    # MSA: Notification 서비스로 사용자 활동 알림
    notify_user_activity(author_id, "POST_CREATED", {
        "post_id": post.id,
        "title": post.title
    })
    
    return jsonify({"message": "Post created", "id": post.id}), 201

@bp.route('/posts/<post_id>', methods=['PUT', 'PATCH'])
def update_post(post_id):
    """게시글 수정 (PUT: 전체 교체, PATCH: 부분 수정)"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json(force=True, silent=False)

    if request.method == 'PUT':
        title = (data.get('title') or '').strip()
        content_md = (data.get('content_md') or '').strip()
        content_s3url = data.get('content_s3url', '').strip()
        author_id = data.get('author_id')
        visibility = data.get('visibility', 'PUBLIC')
        status = data.get('status', 'DRAFT')
        
        if not title or not author_id:
            abort(400, description="title, author_id are required")
            
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
    return jsonify({"message": "Post updated", "id": post.id})

@bp.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """게시글 삭제 (소프트 삭제: status를 'DELETED'로 변경)"""
    post = Post.query.get_or_404(post_id)
    post.status = 'DELETED'
    db.session.commit()
    return jsonify({"message": "Post deleted", "id": post.id})

# ============================================================================
# 게시글 반응 API
# ============================================================================

@bp.route('/posts/<post_id>/reaction', methods=['POST'])
def react_post(post_id):
    """게시글 반응 (좋아요/싫어요 토글)"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json(force=True, silent=False)
    user_id = data.get('user_id')
    action = data.get('action')
    
    if not user_id or action not in ['LIKE', 'DISLIKE']:
        abort(400, description="user_id and action (LIKE/DISLIKE) are required")
    
    existing_reaction = PostReaction.query.filter_by(post_id=post_id, user_id=user_id).first()
    
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
    return jsonify({"message": "ok", "like_count": post.like_count, "dislike_count": post.like_count})

# ============================================================================
# 태그 API
# ============================================================================

@bp.route('/tags', methods=['GET'])
def list_tags():
    """태그 목록 조회"""
    tags = Tag.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in tags])

@bp.route('/tags', methods=['POST'])
def create_tag():
    """새 태그 생성"""
    data = request.get_json(force=True, silent=False)
    name = (data.get('name') or '').strip()
    
    if not name:
        abort(400, description="tag name is required")
    
    tag = Tag(name=name)
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({"message": "Tag created", "id": tag.id, "name": tag.name}), 201

# ============================================================================
# 이미지 관리 API
# ============================================================================

@bp.route('/posts/<post_id>/images', methods=['POST'])
def upload_post_image(post_id):
    """게시글에 이미지 업로드 (개발: 로컬, 운영: S3)"""
    post = Post.query.get(post_id)
    if not post:
        abort(404, description="Post not found")
    
    if 'image' not in request.files:
        abort(400, description="No image file provided")
    
    file = request.files['image']
    if file.filename == '':
        abort(400, description="No file selected")
    
    if not allowed_file(file.filename):
        abort(400, description="File type not allowed")
    
    try:
        image_data = save_image_locally(file, post_id)
        
        post_media = PostMedia(
            post_id=post_id,
            s3_url=image_data['s3_url'],
            mime_type=image_data['mime_type'],
            width=image_data['width'],
            height=image_data['height']
        )
        
        db.session.add(post_media)
        db.session.commit()
        
        # Outbox 이벤트 생성
        outbox_event = OutboxEvent(
            aggregate_id=post_id,
            event_type='POST_IMAGE_UPLOADED',
            payload_json={
                'post_id': post_id,
                'media_id': post_media.id,
                's3_url': image_data['s3_url'],
                'mime_type': image_data['mime_type']
            }
        )
        db.session.add(outbox_event)
        db.session.commit()
        
        return jsonify({
            "message": "Image uploaded successfully",
            "media_id": post_media.id,
            "s3_url": image_data['s3_url'],
            "mime_type": image_data['mime_type'],
            "width": image_data['width'],
            "height": image_data['height']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Upload failed: {str(e)}")

@bp.route('/posts/<post_id>/images', methods=['GET'])
def get_post_images(post_id):
    """게시글의 이미지 목록 조회"""
    post = Post.query.get(post_id)
    if not post:
        abort(404, description="Post not found")
    
    images = PostMedia.query.filter_by(post_id=post_id).all()
    
    return jsonify({
        "post_id": post_id,
        "images": [{
            "id": img.id,
            "s3_url": img.s3_url,
            "mime_type": img.mime_type,
            "width": img.width,
            "height": img.height,
            "created_at": img.created_at.isoformat()
        } for img in images]
    })

@bp.route('/posts/<post_id>/images/<int:media_id>', methods=['DELETE'])
def delete_post_image(post_id, media_id):
    """게시글의 이미지 삭제"""
    post = Post.query.get(post_id)
    if not post:
        abort(404, description="Post not found")
    
    image = PostMedia.query.filter_by(id=media_id, post_id=post_id).first()
    if not image:
        abort(404, description="Image not found")
    
    try:
        # 로컬 파일 삭제 (개발 환경)
        if image.s3_url.startswith('/uploads/'):
            file_path = os.path.join(current_app.root_path, image.s3_url.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(image)
        
        # Outbox 이벤트 생성
        outbox_event = OutboxEvent(
            aggregate_id=post_id,
            event_type='POST_IMAGE_DELETED',
            payload_json={
                'post_id': post_id,
                'media_id': media_id,
                's3_url': image.s3_url
            }
        )
        db.session.add(outbox_event)
        db.session.commit()
        
        return jsonify({"message": "Image deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Deletion failed: {str(e)}")

