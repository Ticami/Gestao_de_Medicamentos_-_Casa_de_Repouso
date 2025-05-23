import sys
from streamlit.web import cli as stcli

sys.argv = ["streamlit", "run", "appe.py"]
sys.exit(stcli.main())