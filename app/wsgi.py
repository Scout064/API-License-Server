import sys
import site  # <--- This is required

# add project directory to sys.path
sys.path.insert(0, "/var/www/license-server")

# activate virtualenv
# Add virtual environment site-packages
site.addsitedir('/var/www/license-server/lic/lib/python3.11/site-packages')

# Import your Flask app
from app import app as application
