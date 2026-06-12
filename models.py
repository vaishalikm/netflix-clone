from datetime import datetime
from flask_login import UserMixin
from extensions import db, bcrypt, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and profile data."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    watchlist = db.relationship("Watchlist", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Movie(db.Model):
    """Movie model with metadata and media paths."""
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    genre = db.Column(db.String(50), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    duration = db.Column(db.String(20), nullable=False)
    thumbnail = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    watchlist_entries = db.relationship("Watchlist", backref="movie", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "genre": self.genre, "year": self.year, "rating": self.rating,
            "duration": self.duration, "thumbnail": self.thumbnail,
            "video_url": self.video_url, "is_featured": self.is_featured,
        }

    def __repr__(self):
        return f"<Movie {self.title}>"


class Watchlist(db.Model):
    """Watchlist linking users and movies."""
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id", name="unique_watchlist_entry"),)

    def __repr__(self):
        return f"<Watchlist user={self.user_id} movie={self.movie_id}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
