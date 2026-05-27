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

# first_movie = Movie(
#     title="Dumb & Dumber",
#     year=1994,
#     description="Two lovable goofballs go on a cross-country adventure to return a woman's briefcase, and find trouble along the way",
#     rating=10.0,
#     ranking=1,
#     review="One of the funniest movies I've ever seen!",
#     img_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fstatic1.srcdn.com%2Fwordpress%2Fwp-content%2Fuploads%2F2023%2F05%2Fdumb-and-dumber-movie-poster.jpg&f=1&nofb=1&ipt=5f23cc34433d929a0a1df783eddcfadc3cb8b6df8f7d6e3c4641fcb628eda9e3"
# )
#
# with app.app_context():
#     db.session.add(first_movie)
#     db.session.commit()

class EditMovieForm(FlaskForm):
    rating = StringField(label="Your rating out of 10", name="rating", validators=[DataRequired()])
    review = StringField(label="Your Review", name="review", validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.ranking)).scalars()
    return render_template("index.html", movies=movies)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    form = EditMovieForm()
    movie = db.get_or_404(Movie, id)

    if request.method == "POST":
        if form.validate_on_submit():
            movie.rating = float(request.form["rating"])
            movie.review = request.form["review"]
            db.session.commit()
            return redirect(url_for("home"))
        else:
            return render_template("edit.html", form=form, movie=movie)
    else:
        return render_template("edit.html", form=form, movie=movie)



if __name__ == '__main__':
    app.run(debug=True)
