import os
import sys

# Ensure the app directory is in sys.path so local modules resolve correctly
APP_DIR = os.path.abspath(os.path.dirname(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from flask import Flask
from extensions import db, login_manager, bcrypt


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Database Configuration ──────────────────────────────────────────────
    # MySQL (XAMPP) — set these environment variables to match your XAMPP setup,
    # or edit the defaults below directly.
    #   DB_HOST   : MySQL host        (default: localhost)
    #   DB_PORT   : MySQL port        (default: 3306)
    #   DB_USER   : MySQL username    (default: root)
    #   DB_PASS   : MySQL password    (default: empty — XAMPP default)
    #   DB_NAME   : Database name     (default: netflix_clone)
    #
    # You must create the database in phpMyAdmin (or MySQL CLI) first:
    #   CREATE DATABASE netflix_clone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    # ─────────────────────────────────────────────────────────────────────────
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASS = os.environ.get("DB_PASS", "")        # XAMPP root has no password by default
    DB_NAME = os.environ.get("DB_NAME", "netflix_clone")

    MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLITE_URI = f"sqlite:///{os.path.join(APP_DIR, 'netflix.db')}"

    # Try MySQL first; fall back to SQLite if the server is unreachable.
    def _mysql_reachable():
        try:
            import pymysql
            conn = pymysql.connect(
                host=DB_HOST, port=int(DB_PORT),
                user=DB_USER, password=DB_PASS,
                connect_timeout=3,
            )
            conn.close()
            return True
        except Exception:
            return False

    use_mysql = _mysql_reachable()
    DB_URI = MYSQL_URI if use_mysql else SQLITE_URI

    if use_mysql:
        print(f"[DB] Connected to MySQL: {DB_HOST}:{DB_PORT}/{DB_NAME}", flush=True)
    else:
        print("[DB] MySQL unavailable — falling back to SQLite (netflix.db)", flush=True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "netflix-clone-secret-key-2024")
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if use_mysql:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 280,
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 10},
        }
    app.config["UPLOAD_FOLDER"] = os.path.join(APP_DIR, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

    # Create upload folder
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Login manager settings
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Register blueprints
    from routes.auth import auth_bp
    from routes.movies import movies_bp
    from routes.watchlist import watchlist_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(admin_bp)

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Seed the database with sample movies and admin/demo users if not present."""
    from models import User, Movie

    # Create admin user
    if not User.query.filter_by(email="admin@netflix.com").first():
        admin = User(username="Admin", email="admin@netflix.com", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)

    # Create demo user
    if not User.query.filter_by(email="demo@netflix.com").first():
        demo = User(username="DemoUser", email="demo@netflix.com", is_admin=False)
        demo.set_password("demo123")
        db.session.add(demo)

    # Seed movies only if none exist
    if Movie.query.count() == 0:
        sample_movies = [
            {
                "title": "Cosmic Journey",
                "description": "A breathtaking odyssey through the cosmos as a crew of astronauts ventures beyond the known universe, discovering civilizations and confronting the mysteries of existence.",
                "genre": "Sci-Fi", "year": 2023, "rating": 8.7, "duration": "2h 28m",
                "thumbnail": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "is_featured": True,
            },
            {
                "title": "Shadow Protocol",
                "description": "When a rogue AI infiltrates global defense systems, a disgraced hacker must work with an elite black-ops team to prevent World War III.",
                "genre": "Action", "year": 2023, "rating": 7.9, "duration": "2h 5m",
                "thumbnail": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "is_featured": True,
            },
            {
                "title": "The Last Laugh",
                "description": "A stand-up comedian facing bankruptcy discovers a conspiracy inside the entertainment industry and must choose between fame and justice.",
                "genre": "Comedy", "year": 2022, "rating": 7.4, "duration": "1h 52m",
                "thumbnail": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_featured": False,
            },
            {
                "title": "Eternal Echoes",
                "description": "Two souls separated by centuries find their love transcends time itself, guided by a mysterious journal that appears across lifetimes.",
                "genre": "Romance", "year": 2023, "rating": 8.1, "duration": "2h 10m",
                "thumbnail": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
                "is_featured": True,
            },
            {
                "title": "Neon Nights",
                "description": "In a cyberpunk city where dreams are sold illegally, a detective hunts a killer who steals memories, only to discover the truth about her own past.",
                "genre": "Thriller", "year": 2022, "rating": 8.4, "duration": "2h 15m",
                "thumbnail": "https://images.unsplash.com/photo-1519608425089-7f3bfa6f6bb8?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "is_featured": True,
            },
            {
                "title": "The Dark Forest",
                "description": "A group of friends camping in the woods stumble upon an ancient evil buried beneath the earth. What awakens will change their lives forever.",
                "genre": "Horror", "year": 2023, "rating": 7.2, "duration": "1h 45m",
                "thumbnail": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "is_featured": False,
            },
            {
                "title": "Iron Fist Rising",
                "description": "After losing everything to a corrupt corporation, a former MMA champion trains in secret and returns to dismantle the criminal empire from within.",
                "genre": "Action", "year": 2022, "rating": 7.6, "duration": "2h 2m",
                "thumbnail": "https://images.unsplash.com/photo-1574117484476-2b4bb42d84f6?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "is_featured": False,
            },
            {
                "title": "Quantum Paradox",
                "description": "A physicist accidentally creates a portal to parallel universes, triggering a cascade of events that threatens to collapse all of reality.",
                "genre": "Sci-Fi", "year": 2021, "rating": 8.0, "duration": "2h 20m",
                "thumbnail": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_featured": False,
            },
            {
                "title": "Chef's Table: Tokyo",
                "description": "A world-renowned chef returns to his Tokyo roots after a decade of global success, rediscovering simple flavors and the family he left behind.",
                "genre": "Drama", "year": 2023, "rating": 8.3, "duration": "1h 58m",
                "thumbnail": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
                "is_featured": False,
            },
            {
                "title": "Wild Earth",
                "description": "An epic four-year documentary journey across seven continents, capturing the planet's most extraordinary wildlife in their natural habitats.",
                "genre": "Documentary", "year": 2022, "rating": 9.1, "duration": "3h 10m",
                "thumbnail": "https://images.unsplash.com/photo-1474511320723-9a56873867b5?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "is_featured": False,
            },
            {
                "title": "Campus Chaos",
                "description": "When the nerdiest kid on campus accidentally becomes the most popular student after a viral moment, everything spirals hilariously out of control.",
                "genre": "Comedy", "year": 2023, "rating": 7.0, "duration": "1h 40m",
                "thumbnail": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "is_featured": False,
            },
            {
                "title": "Blood Oath",
                "description": "A retired hitman is drawn back into the underworld when his daughter is kidnapped by a criminal syndicate seeking a hidden ledger.",
                "genre": "Thriller", "year": 2021, "rating": 8.2, "duration": "2h 8m",
                "thumbnail": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "is_featured": False,
            },
            {
                "title": "Midnight in Paris",
                "description": "A hopeless romantic novelist on a trip to Paris discovers a magical portal that takes him back to the 1920s, meeting the literary giants he idolizes.",
                "genre": "Romance", "year": 2022, "rating": 7.8, "duration": "1h 34m",
                "thumbnail": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_featured": False,
            },
            {
                "title": "The Haunting",
                "description": "A family moves into a beautiful Victorian mansion, only to discover it's inhabited by malevolent spirits tied to a dark family secret.",
                "genre": "Horror", "year": 2022, "rating": 7.5, "duration": "2h 0m",
                "thumbnail": "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
                "is_featured": False,
            },
            {
                "title": "Steel Nation",
                "description": "The untold story of workers in a dying steel town who fight back against corporate greed, forming an unlikely alliance that changes American labor forever.",
                "genre": "Drama", "year": 2021, "rating": 8.6, "duration": "2h 30m",
                "thumbnail": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "is_featured": False,
            },
            {
                "title": "Galactic Rebels",
                "description": "In a distant galaxy ruled by a tyrannical empire, a ragtag group of rebels discover an ancient weapon powerful enough to end the war or destroy the universe.",
                "genre": "Sci-Fi", "year": 2023, "rating": 8.9, "duration": "2h 45m",
                "thumbnail": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "is_featured": False,
            },
            {
                "title": "The Heist",
                "description": "Six strangers with nothing in common must work together to pull off the most audacious bank robbery in history with only 24 hours to plan.",
                "genre": "Thriller", "year": 2022, "rating": 7.7, "duration": "2h 3m",
                "thumbnail": "https://images.unsplash.com/photo-1584824486509-112e4181ff6b?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "is_featured": False,
            },
            {
                "title": "Ocean's Deep",
                "description": "Marine biologists discover a previously unknown civilization beneath the Pacific Ocean, triggering a race between governments and corporations to exploit it.",
                "genre": "Documentary", "year": 2023, "rating": 8.5, "duration": "1h 55m",
                "thumbnail": "https://images.unsplash.com/photo-1518020382113-a7e8fc38eac9?w=400&h=600&fit=crop",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_featured": False,
            },
        ]

        for m in sample_movies:
            movie = Movie(
                title=m["title"],
                description=m["description"],
                genre=m["genre"],
                year=m["year"],
                rating=m["rating"],
                duration=m["duration"],
                thumbnail=m["thumbnail"],
                video_url=m["video_url"],
                is_featured=m["is_featured"],
            )
            db.session.add(movie)

    db.session.commit()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=port, debug=False)
