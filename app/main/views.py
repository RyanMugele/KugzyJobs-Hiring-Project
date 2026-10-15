import flask

from . import main


@main.route("/")
def index():
    return flask.render_template("main/index.html")
