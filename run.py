from app import create_app
from app.decorators import check_authorization

app = create_app()


@app.before_request
def before_request():
    return check_authorization(lambda: None)()


if __name__ == '__main__':
    app.run()