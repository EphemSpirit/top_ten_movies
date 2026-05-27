from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os

load_dotenv()

MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
bootstrap = Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()


class EditMovieForm(FlaskForm):
    rating = StringField(label="Your rating out of 10", name="rating", validators=[DataRequired()])
    review = StringField(label="Your Review", name="review", validators=[DataRequired()])
    submit = SubmitField("Submit")

class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", name="title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()

    for i in range(len(movies)):
        movies[i].rating = len(movies) - i
    db.session.commit()

    return render_template("index.html", movies=movies)


@app.route("/movies/search", methods=["GET", "POST"])
def search():
    form = AddMovieForm()
    if request.method == "POST":
        url = f"https://api.themoviedb.org/3/search/movie?query={form.title.data}&include_adult=true"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {os.getenv("MOVIE_DB_READ_ACCESS_TOKEN")}"
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()

        movies = res.json()["results"]
        return render_template("select.html", options=movies)
    else:
        return render_template("add.html", form=form)


@app.route("/movies/add/<int:movie_id>")
def create(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv("MOVIE_DB_READ_ACCESS_TOKEN")}"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()

    data = res.json()

    new_movie = Movie(
        title=data["title"],
        year=int(data["release_date"].split("-")[0]),
        description=data["overview"],
        img_url=f"{MOVIE_DB_IMAGE_URL}/{data["poster_path"]}"
    )

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


@app.route("/movies/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    form = EditMovieForm()
    movie = db.get_or_404(Movie, id)

    if request.method == "POST":
        if form.validate_on_submit():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for("home"))
        else:
            return render_template("edit.html", form=form, movie=movie)
    else:
        return render_template("edit.html", form=form, movie=movie)


@app.route("/movies/<int:id>/delete")
def delete(id):
    movie = db.get_or_404(Movie, id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))



if __name__ == '__main__':
    app.run(debug=True)
