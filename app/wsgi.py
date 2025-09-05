import sys
import site  # <--- This is required
import logging
logging.basicConfig(stream=sys.stderr)

# add project directory to sys.path
sys.path.insert(0, "/var/www/license-server")

# activate virtualenv
# Add virtual environment site-packages
site.addsitedir('/var/www/license-server/lic/lib/python3.11/site-packages')
