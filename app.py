from datetime import date
import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


# Create the Flask application and point it to the requested project folders.
app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static",
)

# Keep the SQLite database inside the database/ folder for easy local cleanup.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "mandimitra.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Crop(db.Model):
    """Crop master table, for example Wheat, Rice, Peas, and Moong."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    prices = db.relationship("Price", back_populates="crop", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Crop {self.name}>"


class Mandi(db.Model):
    """Mandi master table with the market name and district."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(120), nullable=False)

    prices = db.relationship("Price", back_populates="mandi", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mandi {self.name}, {self.district}>"


class Price(db.Model):
    """Daily mandi price for one crop at one mandi."""

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crop.id"), nullable=False)
    mandi_id = db.Column(db.Integer, db.ForeignKey("mandi.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    crop = db.relationship("Crop", back_populates="prices")
    mandi = db.relationship("Mandi", back_populates="prices")

    def __repr__(self):
        return f"<Price {self.crop_id} {self.mandi_id} {self.price}>"


def init_db():
    """Create database tables and insert beginner-friendly sample data."""

    os.makedirs(DATABASE_DIR, exist_ok=True)

    with app.app_context():
        db.create_all()

        # If seed data already exists, do not insert duplicates on every restart.
        if Crop.query.first():
            return

        crops = {
            "Wheat": Crop(name="Wheat"),
            "Rice": Crop(name="Rice"),
            "Peas": Crop(name="Peas"),
            "Moong": Crop(name="Moong"),
        }

        mandis = {
            "Azadpur": Mandi(name="Azadpur Mandi", district="Delhi"),
            "Karnal": Mandi(name="Karnal Mandi", district="Karnal"),
            "Indore": Mandi(name="Indore Mandi", district="Indore"),
            "Jaipur": Mandi(name="Jaipur Mandi", district="Jaipur"),
        }

        db.session.add_all(list(crops.values()) + list(mandis.values()))
        db.session.flush()

        sample_prices = [
            Price(crop=crops["Wheat"], mandi=mandis["Karnal"], date=date(2026, 6, 13), price=2320),
            Price(crop=crops["Rice"], mandi=mandis["Azadpur"], date=date(2026, 6, 13), price=3180),
            Price(crop=crops["Peas"], mandi=mandis["Jaipur"], date=date(2026, 6, 13), price=4550),
            Price(crop=crops["Moong"], mandi=mandis["Indore"], date=date(2026, 6, 13), price=7820),
        ]

        db.session.add_all(sample_prices)
        db.session.commit()


@app.route("/")
def index():
    """Homepage route showing the core MandiMitra crop cards."""

    crops = Crop.query.order_by(Crop.name).all()
    return render_template("index.html", crops=crops)


@app.route("/prices")
def prices():
    """Display sample mandi prices in a clean table."""

    mandi_prices = (
        Price.query.join(Crop)
        .join(Mandi)
        .order_by(Price.date.desc(), Crop.name.asc())
        .all()
    )
    return render_template("prices.html", mandi_prices=mandi_prices)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
