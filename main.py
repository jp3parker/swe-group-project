"""docstring"""
import os
from PIL import Image
from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from google_images_search import GoogleImagesSearch
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
gis = GoogleImagesSearch(GCS_DEVELOPER_KEY, GCS_CX)
app = Flask(__name__)
image_search_results = ["", "", ""] # placeholders
# app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
# app.secret_key = os.getenv("SECRET_KEY")
# db = SQLAlchemy(app)
# login_manager = LoginManager()
# login_manager.init_app(app)
# ascii characters used to build the output text
ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", ".", " "]


# class Person(UserMixin, db.Model):
#     """Person object is what is stored in the table that holds user data"""

#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)

#     def __init__(self, name):
#         self.username = name


# class Picture(db.Model):
#     """Picture object is what is stored in the table that holds picture data"""

#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), nullable=False)
#     picture = db.Column(db.String(10000), nullable=False)
#     width = db.Column(db.Integer, nullable=False)

#     def __init__(self, id, username, picture, width):
#         self.id = id
#         self.username = username
#         self.picture = picture
#         self.width = width


# with app.app_context():
#     db.create_all()


# @login_manager.user_loader
# def load_user(user_id):
#     """returns user object with user_id as their id"""
#     return Person.query.get(int(user_id))


@app.route("/login_page", methods=["GET", "POST"])
def login_page():
    """loads login page"""
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """nothing yet - just calls login_page"""
    return "redirect(login_page())"


@app.route("/signup_page", methods=["GET", "POST"])
def signup_page():
    """loads signup page"""
    return render_template("signup.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """nothing yet - just calls login_page"""
    return "redirect(signup_page())"


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
def index(show_searched_images =False):
    print("show_searched_images = ", show_searched_images)
    if show_searched_images:
        print("trying to print images")
        print(image_search_results[0])
        return render_template('index.html', image_search_results=image_search_results)
    else:
        print('nothing here - no images')
        return render_template('index.html', image_search_results=[])


@app.route("/imageSearch", methods=["GET", "POST"])
def imageSearch():
    print("THIS IS THE METHOD USED ==== ", request.method)
    if (
        request.method == "POST"
        and "searchWord" in request.form
    ):
        gis.search({'q': str(request.form['searchWord']), 'num': 3})
        results = gis.results()
        print(image_search_results[0])
        print(image_search_results[1])
        print(image_search_results[2])
        image_search_results[0] = results[0].url
        image_search_results[1] = results[1].url
        image_search_results[2] = results[2].url
        print(image_search_results[0])
        print(image_search_results[1])
        print(image_search_results[2])
        return index(True)
    else:
        # flash("We could not process your comment.")
        print("fuck no")
        return index(False)

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
        print("width = ", image.width)
        print("height = ", image.height)
        while (image.height * image.width > 10000):
            new_width = int(new_width * 0.9)
            image = resize_image(image, new_width)
            print("width = ", image.width)
            print("height = ", image.height)

        new_image_data = pixels_to_ascii(grayify(image))
        pixel_count = len(new_image_data)
        ascii_image = "\n".join([new_image_data[index:(index+new_width)] \
            for index in range(0, pixel_count, new_width)])
        print(ascii_image)

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
    for pixel in range(len(pixels)):
        print(pixels[pixel])
    characters = "".join([ASCII_CHARS[pixel//22] for pixel in pixels])
    return characters


if __name__ == "__main__":
    app.run()
