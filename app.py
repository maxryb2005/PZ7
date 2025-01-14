# Импортируем необходимые библиотеки
from flask import Flask, render_template, redirect, url_for, request, session  # Импортируем модули Flask для создания веб-приложения и работы с HTTP-запросами
import psycopg2  # Импортируем библиотеку для работы с PostgreSQL и взаимодействия с базой данных
from psycopg2 import sql  # Импортируем модуль sql из psycopg2 для удобного выполнения SQL-запросов, что позволяет строить запросы с защитой от SQL-инъекций
from bs4 import BeautifulSoup  # Импортируем BeautifulSoup для парсинга HTML-страниц и извлечения данных
import requests  # Импортируем библиотеку requests для выполнения HTTP-запросов и получения контента веб-страниц
import hashlib  # Импортируем библиотеку hashlib для хеширования паролей, чтобы обеспечить безопасность пользовательских данных

# Создаем экземпляр приложения Flask
app = Flask(__name__)  # Инициализируем приложение Flask, передавая имя текущего модуля
app.secret_key = 'my_p_7'  # Устанавливаем секретный ключ для работы с сессиями, он необходим для защиты сессий пользователей

# Настройки подключения к базе данных PostgreSQL
db_conn = psycopg2.connect(
    dbname="belka",  # Имя базы данных, с которой мы собираемся работать
    user="postgres",  # Имя пользователя для подключения к базе данных
    password="3456", # Пароль для доступа к базе данных, используйте безопасный пароль в реальных проектах
    host="localhost"  # Хост, на котором запущена база данных, здесь мы используем локальный сервер
)

cursor = db_conn.cursor()  # Создаем курсор для выполнения SQL-запросов, он необходим для взаимодействия с базой данных

# Определяем маршрут для домашней страницы
@app.route('/')
def home():
    try:
        return render_template('home.html')  # Отправляем пользователя на страницу home.html с приветствием или основным содержимым
    except Exception as e:
        return render_template('error.html', error=str(e)), 500  # В случае ошибки отображаем страницу с ошибкой и отправляем код 500

# Определяем маршрут для страницы "О нас"
@app.route('/about')
def about():
    return render_template('about.html')  # Отправляем пользователя на страницу about.html с информацией о проекте или команде

# Определяем маршрут для страницы "Галерея"
@app.route('/gallery')
def gallery():
    # Список изображений, которые будут отображаться на странице галереи
    images = [
        'static/images/4.jpg',
        'static/images/2.png',
        'static/images/3.jpg',
        'static/images/8.jpg',
        'static/images/6.jpg',
        'static/images/5.jpg'
    ]
    return render_template('gallery.html', images=images)  # Отправляем список изображений на страницу gallery.html для отображения

# Определяем маршрут для регистрации пользователей
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Если запрос POST (т.е. при отправке формы регистрации)
        username = request.form['username']  # Получаем имя пользователя из формы
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()  # Хешируем пароль перед сохранением в базе данных

        try:
            # Выполняем SQL-запрос для добавления пользователя в базу данных
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            db_conn.commit()  # Коммитим изменения для сохранения нового пользователя
            return redirect(url_for('home'))  # Перенаправляем пользователя на домашнюю страницу после успешной регистрации
        except Exception as e:
            db_conn.rollback()  # В случае ошибки откатываем изменения, чтобы база данных осталась в целостном состоянии
            return f"Ошибка регистрации: {e}"  # Возвращаем сообщение об ошибке регистрации

    return render_template('register.html')  # Если GET-запрос, отображаем форму регистрации

# Определяем маршрут для входа пользователей
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Если запрос POST (т.е. при отправке формы входа)
        username = request.form['username']  # Получаем имя пользователя
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()  # Хешируем введенный пароль

        # Выполняем SQL-запрос для проверки существования пользователя в базе данных
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()  # Получаем первую запись (пользователя) из результата запроса

        if user:  # Если пользователь найден в базе данных
            session['username'] = username  # Сохраняем имя пользователя в сессии, чтобы поддерживать авторизацию
            return redirect(url_for('home'))  # Перенаправляем на домашнюю страницу при успешном входе
        else:
            return 'Неверный логин или пароль'  # Если пользователь не найден, выводим сообщение об ошибке входа

    return render_template('login.html')  # Если GET-запрос, отображаем форму для входа

# Определяем маршрут для выхода из учетной записи
@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаляем имя пользователя из сессии, чтобы завершить сеанс
    return redirect(url_for('home'))  # Перенаправляем на домашнюю страницу после выхода

# Определяем маршрут для парсинга данных
@app.route('/parse', methods=['POST'])
def parse():
    letter = request.form['letter']  # Получаем букву из формы, по которой будем фильтровать гонщиков
    url = "https://eldenring.fandom.com/ru/wiki/Категория:Обязательные_гонщиков"  # URL-адрес страницы с обязательными гонщиками
    response = requests.get(url)  # Отправляем HTTP-запрос для получения контента страницы
    soup = BeautifulSoup(response.content, 'html.parser')  # Парсим содержимое страницы с помощью BeautifulSoup

    # Находим всех боссов, имена которых начинаются на указанную букву
    sports = [sport.text for sport in soup.find_all('a') if sport.text.startswith(letter)]
    if not sports:  # Если список боссов пуст
        sports = ['гонщиков на эту букву нет']  # Добавляем сообщение о том, что гонщиокв нет

    return render_template('home.html', sports=sports)  # Отправляем список гонщиков на домашнюю страницу для отображения

# Запускаем приложение, если это основной модуль
if __name__ == '__main__':
    app.run(port=288, debug=True)  # Запускаем сервер на порту 228 с режимом отладки для разработки
