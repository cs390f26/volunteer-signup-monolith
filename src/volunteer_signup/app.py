from flask import Flask, jsonify


def create_app() -> Flask:
    """Create the Flask application and register its routes."""
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


def launch() -> Flask:
    """Create the application for local development and deployment."""
    return create_app()


if __name__ == "__main__":
    app = launch()
    app.run(debug=True, port=5000)