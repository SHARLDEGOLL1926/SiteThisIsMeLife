from flask import Flask, render_template, redirect, abort, request
from data import db_session
from data.users import User
from data.shops import Shop
from forms.user import RegisterForm
from forms.login import LoginForm
from forms.shops import ShopsForm
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
import requests
from io import BytesIO
from PIL import Image


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)

    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/shops',  methods=['GET', 'POST'])
@login_required
def add_shops():
    form = ShopsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        shop = Shop()
        shop.title = form.title.data
        shop.content = form.content.data
        shop.coordinats = form.coordinats.data
        current_user.shop.append(shop)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('shop.html', title='Добавление магазина',
                           form=form)


@app.route('/shops/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_shops(id):
    form = ShopsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        shops = db_sess.query(Shop).filter(Shop.id == id,
                                           Shop.user == current_user
                                           ).first()
        if shops:
            form.title.data = shops.title
            form.content.data = shops.content
            form.coordinats.data = shops.coordinats
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        shops = db_sess.query(Shop).filter(Shop.id == id,
                                           Shop.user == current_user
                                           ).first()
        if shops:
            shops.title = form.title.data
            shops.content = form.content.data
            shops.coordinats = form.coordinats.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('shop.html',
                           title='Редактирование магазина',
                           form=form
                           )


@app.route('/shops_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_shops(id):
    return render_template("index.html", title="Удалить", )


@app.route('/?text=<text>&submit=<submit>#', methods=['GET', 'POST'])
@login_required
def find_shops(text):
    return render_template("index.html", title="Удалить", )


@app.route('/api_shops/<address>/<title>', methods=['GET', 'POST'])
@login_required
def api_shops(address, title):
    toponym_to_find = address
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        pass
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    toponym_coodrinates = toponym["Point"]["pos"]
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
    delta = "0.005"
    map_params = {
        "ll": ",".join([toponym_longitude, toponym_lattitude]),
        "spn": ",".join([delta, delta]),
        "l": "map"
    }
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)
    img = Image.open(BytesIO(response.content))
    return render_template("api_shops.html", img=img, title=title)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        shop = db_sess.query(Shop).filter(
            Shop.user == current_user)
    else:
        shop = db_sess.query(Shop)
    return render_template("index.html", shop=shop)


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()
