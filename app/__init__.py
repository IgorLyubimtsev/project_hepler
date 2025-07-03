from flask import Flask
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from .extensions import db, login_manager
from app.models import Users, register_background_tasks
from flask_session import Session
from datetime import timedelta
from app.logging import logger

csrf = CSRFProtect()

def create_app():
    """
    Фабрика приложения Flask.
    Инициализирует и настраивает приложение, расширения, blueprint-ы и фоновые задачи.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Asmadey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/projects.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
    app.config['SESSION_FILE_DIR'] = './flask_session'
    Session(app)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'  # Редирект при попытке доступа к защищенным страницам без авторизации

    # Регистрация blueprint-ов
    from .routes.auth_routes import auth_bp
    from .routes.project_routes import project_bp
    from .routes.admin_routes import admin_bp
    from .routes.actions_routes import act_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(act_bp)

    # Регистрируем фоновые задачи, если есть
    register_background_tasks(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Загружает пользователя по ID для Flask-Login."""
        return Users.query.get(int(user_id))

    def fio_to_initials(value):
        """
        Фильтр Jinja2 для преобразования ФИО в формат 'Фамилия И.О.'.
        Пример: Иванов Иван Иванович -> Иванов И.И.
        """
        import re
        pattern = r'^(\S+)\s+(\S)\S*\s+(\S)\S*$'
        return re.sub(pattern, r'\1 \2.\3.', value)

    app.jinja_env.filters['fio_to_initials'] = fio_to_initials

    with app.app_context():
        db.create_all()

        from .utils import create_excel_backup

        scheduler = BackgroundScheduler()
        try:
            scheduler.add_job(func=create_excel_backup, trigger='interval', hours=24)
            scheduler.start()
        except Exception as e:
            logger.error(f"Ошибка при запуске планировщика: {e}")

    return app