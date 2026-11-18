from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from mysql.connector import Error
from config import Config
from database import close_db

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    CSRFProtect(app)
    app.teardown_appcontext(close_db)
    from routes import bp
    app.register_blueprint(bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', title='Page not found', message='The requested record or page does not exist.'), 404

    @app.errorhandler(Error)
    def database_error(error):
        app.logger.exception('Database operation failed')
        return render_template('error.html', title='Database unavailable', message='Check your MySQL connection and database setup, then try again.'), 503

    @app.errorhandler(400)
    def bad_request(error):
        return render_template('error.html', title='Request could not be processed', message='Your form may have expired. Reload the page and try again.'), 400
    return app

if __name__ == '__main__':
    create_app().run()
