from flask import Blueprint

users_bp = Blueprint('users', __name__, url_prefix='/users')

from . import routes
from . import search_result
from . import booking