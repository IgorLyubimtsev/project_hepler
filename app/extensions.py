"""extensions.py

Этот модуль инициализирует расширения, используемые во всем приложении Flask.
Инициализация происходит в factory-функции приложения, которая вызывает .init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# SQLAlchemy — для взаимодействия с базой данных
db: SQLAlchemy = SQLAlchemy()

# LoginManager — для управления сессиями пользователей
login_manager: LoginManager = LoginManager()

# Настройки login_manager будут применяться в create_app() или аналогичной factory-функции:
# login_manager.login_view = 'auth.login'   # например
# login_manager.login_message_category = 'warning'