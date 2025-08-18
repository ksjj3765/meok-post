from .models import Post, db

class PostService:
    @staticmethod
    def get_all_posts():
        return Post.query.all()
    
    @staticmethod
    def create_post(title, content, author_id):
        post = Post(title=title, content=content, author_id=author_id)
        db.session.add(post)
        db.session.commit()
        return post
    
    @staticmethod
    def get_post_by_id(post_id):
        return Post.query.get(post_id)





