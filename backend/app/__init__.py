from flask import Flask, jsonify
from mongoengine.errors import NotUniqueError
from mongoengine.errors import ValidationError as MongoValidationError

from .config import Config
from .blueprints.auth import auth_bp
from .blueprints.diner import diner_bp
from .blueprints.vendor import vendor_bp
from .extensions import cors, db
from .models.errors import SkipQError


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    cors.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(diner_bp)
    app.register_blueprint(vendor_bp)

    @app.errorhandler(SkipQError)
    def handle_refusal(err):
        """Every rule refusal returns the message and a code that distinguishes
        it from a server fault (TMA Q3d)."""
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(MongoValidationError)
    def handle_invalid(err):
        return jsonify({'error': 'Invalid data: %s' % err}), 400

    @app.errorhandler(NotUniqueError)
    def handle_duplicate(err):
        return jsonify({'error': 'That value is already in use'}), 409

    @app.errorhandler(404)
    def handle_missing(err):
        return jsonify({'error': 'No such endpoint'}), 404

    @app.errorhandler(405)
    def handle_method(err):
        return jsonify({'error': 'That method is not allowed here'}), 405

    return app
