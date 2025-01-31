from flask import Blueprint

home_bp = Blueprint('home', __name__)

@home_bp.route("/")
def home():
    return "<h1>Flask is running!</h1>"