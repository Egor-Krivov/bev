from .fetch import app
from .init import app
from .blame import app
from .pull import app
from .update import app
from .add import app


def entrypoint():
    app()
