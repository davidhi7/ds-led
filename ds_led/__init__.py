import os
import logging

DEBUG = bool(os.environ.get('DEBUG', False))

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO, format='%(levelname)s %(module)s: %(message)s')
