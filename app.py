"""
Post Service Main Application
MSA 아키텍처에서 게시글 관리만을 담당하는 독립적인 서비스입니다.
"""

from flask import Flask, send_from_directory
from post.routes import bp as post_bp
from post.models import db
from flask_migrate import Migrate
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False  # UTF-8 지원

# 이미지 업로드 설정 (개발: 로컬, 운영: S3)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

db.init_app(app)
Migrate(app, db)  # 데이터베이스 마이그레이션
app.register_blueprint(post_bp)

# 업로드된 이미지 파일 서빙 (API용)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)




