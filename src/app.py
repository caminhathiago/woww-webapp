import dash
from pages.home import home_layout
from callbacks import register_callbacks

def create_app():
    app = dash.Dash(__name__)
    app.title = "Workable Weather Windows Dashboard"
    with open("src/assets/html/index.html", "r") as f:
        app.index_string = f.read()
    app.layout = home_layout
    register_callbacks(app)

    return app

if __name__ == "__main__":
    # app.run(host='0.0.0.0' ,debug=True)
    app = create_app()
    app.run(debug=True)