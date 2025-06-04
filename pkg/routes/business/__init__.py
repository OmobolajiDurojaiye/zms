from flask import Blueprint

business_bp = Blueprint('business', __name__, url_prefix='/business')

from . import routes
from . import inventory_routes
from . import bookings_routes
from . import customers_routes
from . import analytics_routes
from . import payments_routes
from . import settings_routes