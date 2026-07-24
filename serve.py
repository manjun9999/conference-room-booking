"""Production entrypoint: serve the app with waitress (a WSGI server).

The Flask dev server (`python app.py`) is fine for local development but is
single-threaded and not robust under load. For anything beyond dev, run:

    python serve.py

Configure host/port via HOST and PORT environment variables.
"""

import os

from waitress import serve

from app import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Serving ARTIZENT Conference Room Booking on http://{host}:{port}")
    serve(app, host=host, port=port)
