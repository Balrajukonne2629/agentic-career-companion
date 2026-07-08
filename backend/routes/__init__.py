"""
routes/__init__.py
==================
Routes package marker.

Each blueprint is registered in app.py:
    from routes.pipeline import pipeline_bp
    from routes.stt      import stt_bp
    from routes.health   import health_bp
    app.register_blueprint(pipeline_bp, url_prefix="/api")
    app.register_blueprint(stt_bp,      url_prefix="/api")
    app.register_blueprint(health_bp,   url_prefix="/api")
"""
