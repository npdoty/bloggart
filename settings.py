import os
import config

BASE_DIR = os.path.dirname(__file__)

if isinstance(config.theme, (list, tuple)):
  TEMPLATE_DIRS = config.theme
else:
  TEMPLATE_DIRS = [os.path.abspath(os.path.join(BASE_DIR, 'themes/default'))]
  if config.theme and config.theme != 'default':
    TEMPLATE_DIRS.insert(0,
                         os.path.abspath(os.path.join(BASE_DIR, 'themes', config.theme)))