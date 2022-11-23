"""docstring"""
import os
from PIL import Image
import requests
from io import BytesIO
from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
)
from flask_sqlalchemy import SQLAlchemy

load_dotenv(find_dotenv())
GCS_DEVELOPER_KEY=os.getenv("GCS_DEVELOPER_KEY")
GCS_CX=os.getenv("GCS_CX")
app = Flask(__name__)
image_search_results = ["", "", ""] # placeholders
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY")
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# ascii characters used to build the output text
ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", ".", " "]

GOOGLE_CUSTOM_SEARCH_URL="https://www.googleapis.com/customsearch/v1"
search_params = {
    'key': GCS_DEVELOPER_KEY,
    'cx': GCS_CX,
    'q': '...', # place holder
    'searchType': 'image',
    'num': 3
}


class Person(UserMixin, db.Model):
    """Person object is what is stored in the table that holds user data"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    def __init__(self, name):
        self.username = name


class Picture(db.Model):
    """Picture object is what is stored in the table that holds picture data"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    picture = db.Column(db.String(10000), nullable=False)
    width = db.Column(db.Integer, nullable=False)

    def __init__(self, username, picture, width):
        self.username = username
        self.picture = picture
        self.width = width


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    """returns user object with user_id as their id"""
    return Person.query.get(int(user_id))


@app.route("/", methods=["GET", "POST"])
@app.route("/login_page", methods=["GET", "POST"])
def login_page():
    """loads login page"""
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:  # logging in
        print("valid")
        name = request.form["username"]
        user = Person.query.filter_by(username=name).first()
        if user:
            login_user(user)
            return redirect(url_for("index"))
        else:
            return redirect(url_for("signup_page"))
    else:
        return redirect(url_for("signup_page"))


@app.route("/signup_page", methods=["GET", "POST"])
def signup_page():
    """loads signup page"""
    return render_template("signup.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST" and "username" in request.form:  # signing up
        print("trying to sign up.")
        name = request.form["username"]
        user = Person.query.filter_by(username=name).first()
        if user:
            print("already have an account")
            return redirect(url_for("login_page"))
        else:
            print("trying to insert new person")
            new_entry = Person(name)
            db.session.add(new_entry)
            db.session.commit()
            return redirect(url_for("login_page"))
    else:
        print("something went wrong with signup.")
        return redirect(url_for("signup_page"))



@app.route("/home", methods=["GET", "POST"])
@login_required
def index(show_searched_images =False):
    pictures = Picture.query.filter_by(username=current_user.username)

    for pic in pictures:
        pic.picture.replace("\n", "<br>")

    if show_searched_images:
        return render_template('index.html', image_search_results=image_search_results, pictures=pictures)
    else:
        return render_template('index.html', image_search_results=[], pictures=pictures)


@app.route("/imageSearch", methods=["GET", "POST"])
def imageSearch():
    if (
        request.method == "POST"
        and "searchWord" in request.form
    ):
        search_params['q'] = str(request.form['searchWord'])
        response = requests.get(
            GOOGLE_CUSTOM_SEARCH_URL,
            params = search_params
        ).json()
        image_search_results[0] = response["items"][0]['link']
        image_search_results[1] = response["items"][1]['link']
        image_search_results[2] = response["items"][2]['link']
        return index(True)
    else:
        # flash("We could not process your comment.")
        return index(False)
    

@app.route('/ascifySearchedImage', methods=["GET", "POST"])
@login_required
def ChooseSearchedImage():
    if request.method == "POST":
        url = image_search_results[0] if request.form["image"] == "image1" else \
              image_search_results[1] if request.form["image"] == "image2" else \
              image_search_results[2]
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        new_width = image.width
        while (image.height * image.width > 10000):
            new_width = int(new_width * 0.9)
            image = resize_image(image, new_width)

        new_image_data = pixels_to_ascii(grayify(image))
        pixel_count = len(new_image_data)
        ascii_image = "\n".join([new_image_data[index:(index+new_width)] \
            for index in range(0, pixel_count, new_width)])
        print(ascii_image)

        new_picture = Picture(current_user.username, ascii_image, new_width)
        db.session.add(new_picture)
        db.session.commit()

        # save result to "ascii_image.txt"
        with open("ascii_image.txt", "w") as f:
            f.write(ascii_image)
    else:
        print("it failed")
    print("got here 2!!!!!!!!!!!!!!!!!!")
    return redirect(url_for("index"))


@app.route('/fileUpload', methods=["GET", "POST"])
def fileUpload():
    print(request.method)
    print("file" in request.form)
    print(request.files)
    if request.method == "POST" \
    and request.files:
        print("valid")
        try:
            image = Image.open(request.files["file"])
        except:
            print("is not a valid pathname to an image.")
            return index(False)

        new_width = image.width
        while (image.height * image.width > 10000):
            new_width = int(new_width * 0.9)
            image = resize_image(image, new_width)

        new_image_data = pixels_to_ascii(grayify(image))
        pixel_count = len(new_image_data)
        ascii_image = "\n".join([new_image_data[index:(index+new_width)] \
            for index in range(0, pixel_count, new_width)])
        print(ascii_image)

        new_picture = Picture(current_user.username, ascii_image, new_width)
        db.session.add(new_picture)
        db.session.commit()

        # save result to "ascii_image.txt"
        with open("ascii_image.txt", "w") as f:
            f.write(ascii_image)
    else:
        print("not valid")
    return index(False)


# resize image according to a new width
def resize_image(image, new_width):
    """resize image to desired width"""
    width, height = image.size
    ratio = height/width
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

# convert each pixel to grayscale
def grayify(image):
    """convert image to grayscale (remove colors)"""
    grayscale_image = image.convert("L")
    return grayscale_image


# convert pixels to a string of ascii characters
def pixels_to_ascii(image):
    """converts pixels of image to ascii format"""
    pixels = image.getdata()
    characters = "".join([ASCII_CHARS[pixel//22] for pixel in pixels])
    return characters


if __name__ == "__main__":
    app.run()
