import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, DateField, IntegerField,
    SelectField, BooleanField
)
from wtforms.validators import (
    DataRequired, Optional, Regexp, NumberRange, ValidationError, Email
)


def validate_team(form, field):
    """
    Валидатор: проверяет, что поле `Команда` содержит табельные номера
    через `;`, завершающиеся на `;` и состоящие только из восьмизначных чисел.

    Пример валидного ввода: "12345678;87654321;"
    """
    pattern = r'\d{8}(;\d{8})*;$'
    if not re.match(pattern, field.data.strip()):
        raise ValidationError('Введите табельные номера через ; (только цифры и без пробелов). Пример: 12345678;09876541;')
    
class EditProjectForm(FlaskForm):
    """
    Форма редактирования проекта. Используется при доступе к /edit/<id>.
    """
    rating_id = IntegerField('ID проекта в рейтинге ТБ', validators=[Optional(), NumberRange(min=0)])
    km_sup = StringField('КМ в СУП', validators=[
        Optional(),
        Regexp(r'KM-\d{2}-\d{5}$', message='Формат должен быть KM-00-00000')
    ])
    sprint_id = IntegerField('ID Спринта в реестре спринтов BL СВА', validators=[Optional(), NumberRange(min=0)])
    title = StringField('Название проекта', validators=[DataRequired(message='Поле обязательно для заполнения')])

    project_type = SelectField('Тип проекта', choices=[
        ('I', 'I'), ('RnD', 'RnD'), ('I, RnD', 'I, RnD'), ('P', 'P'), ('Доклад', 'Доклад')
    ], validators=[DataRequired(message='Поле обязательно для заполнения')])

    curator = StringField('Куратор', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Regexp(r'^\d{8}$', message='Поле должно содержать 8 цифр')
    ])
    product_owner = StringField('P.Owner (Спикер)', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Regexp(r'^\d{8}$', message='Поле должно содержать 8 цифр')
    ])
    team = StringField('Команда', validators=[DataRequired(), validate_team])

    deadline = DateField('Deadline', format='%Y-%m-%d')
    tech_extensions = IntegerField('Количество технических продлений')

    agile_open_date = DateField('Дата открытия на Agile BL', format='%Y-%m-%d', validators=[DataRequired()])
    open_protocol = IntegerField('Номер протокола (открытие)', validators=[DataRequired(), NumberRange(min=0)])

    agile_close_date = DateField('Дата закрытия на Agile BL', format='%Y-%m-%d', validators=[Optional()])
    close_protocol = IntegerField('Номер протокола (закрытие)', validators=[Optional()])

    base_bank = SelectField('Базовый Банк', choices=[
        ('ББ', 'ББ'), ('ВВБ', 'ВВБ'), ('ДВБ', 'ДВБ'), ('МБ', 'МБ'), ('ПБ', 'ПБ'),
        ('СЗБ', 'СЗБ'), ('СибБ', 'СибБ'), ('СРБ', 'СРБ'), ('УБ', 'УБ'), ('ЦЧБ', 'ЦЧБ'), ('ЮЗБ', 'ЮЗБ')
    ], validators=[DataRequired()])

    # Чекбоксы банков
    bb = BooleanField('ББ')
    vvb = BooleanField('ВВБ')
    dvb = BooleanField("ДВБ")
    mb = BooleanField("МБ")
    pb = BooleanField("ПБ")
    szb = BooleanField("СЗБ")
    sibb = BooleanField("СибБ")
    srb = BooleanField("СРБ")
    ub = BooleanField("УБ")
    ccb = BooleanField("ЦЧБ")
    yuzb = BooleanField("ЮЗБ")

    status = StringField('Статус', render_kw={'readonly': True})
    creator = IntegerField('Управляющий проектом', validators=[Optional()])
    submit = SubmitField('Сохранить')

class CreateProjectForm(FlaskForm):
    """
    Форма создания нового проекта. Используется в маршруте создания проекта.
    """
    title = StringField('Название проекта', validators=[DataRequired()])
    project_type = SelectField('Тип проекта', choices=[
        ('I', 'I'), ('RnD', 'RnD'), ('I, RnD', 'I, RnD'), ('P', 'P'), ('Доклад', 'Доклад')
    ], validators=[DataRequired()], render_kw={"class": "form-select", "required": True, "id": "project_type"})

    curator = StringField('Куратор', validators=[DataRequired(), Regexp(r'^\d{8}$')])
    product_owner = StringField('P.Owner (Спикер)', validators=[DataRequired(), Regexp(r'^\d{8}$')])
    team = StringField('Команда', validators=[DataRequired(), validate_team])

    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    agile_open_date = DateField('Дата открытия на Agile BL', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"class": "form-control"})
    open_protocol = IntegerField('Номер протокола (открытие)', validators=[DataRequired(), NumberRange(min=0)])
    base_bank = SelectField('Базовый Банк', choices=[
        ('ББ', 'ББ'), ('ВВБ', 'ВВБ'), ('ДВБ', 'ДВБ'), ('МБ', 'МБ'), ('ПБ', 'ПБ'),
        ('СЗБ', 'СЗБ'), ('СибБ', 'СибБ'), ('СРБ', 'СРБ'), ('УБ', 'УБ'), ('ЦЧБ', 'ЦЧБ'), ('ЮЗБ', 'ЮЗБ')
    ], validators=[DataRequired()], render_kw={"class": "form-select", "required": True, "id": "base_bank"})

    # Чекбоксы
    bb = BooleanField('ББ')
    vvb = BooleanField('ВВБ')
    dvb = BooleanField("ДВБ")
    mb = BooleanField("МБ")
    pb = BooleanField("ПБ")
    szb = BooleanField("СЗБ")
    sibb = BooleanField("СибБ")
    srb = BooleanField("СРБ")
    ub = BooleanField("УБ")
    ccb = BooleanField("ЦЧБ")
    yuzb = BooleanField("ЮЗБ")

    submit = SubmitField('Создать проект')
        
class SearchForm(FlaskForm):
    """Форма для поиска проектов по названию."""
    search = StringField('Поиск по названию')
    submit = SubmitField('Найти')


class TechnicalExtensionForm(FlaskForm):
    """Форма технического продления срока проекта."""
    new_deadline = DateField('Новый дедлайн', validators=[DataRequired()])
    submit_extension = SubmitField('Оформить продление')


class LoginForm(FlaskForm):
    """Форма авторизации по табельному номеру и паролю."""
    staff_number = StringField('Табельный номер', validators=[DataRequired(), Regexp(r'^\d{8}$')])
    password = StringField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Авторизоваться')


class RegisterForm(FlaskForm):
    """Форма регистрации нового пользователя."""
    full_name = StringField('ФИО', validators=[DataRequired()])
    staff_number = StringField('Табельный номер', validators=[DataRequired(), Regexp(r'^\d{8}$')])
    position = StringField('Должность', validators=[DataRequired()])
    department = StringField('Отдел', validators=[DataRequired()])
    email = StringField('Внутренняя почта', validators=[DataRequired(), Email()])
    submit = SubmitField('Зарегистрироваться')


class PasswordRecovery(FlaskForm):
    """Форма восстановления пароля (по табельному номеру)."""
    staff_number = StringField('Табельный номер', validators=[DataRequired(), Regexp(r'^\d{8}$')])
    submit = SubmitField('Выслать пароль')


class DummyForm(FlaskForm):
    """Пустая форма-заглушка, может быть использована для CSRF или модальных окон."""
    pass