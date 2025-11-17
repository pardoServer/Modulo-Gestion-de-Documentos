#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
#!/usr/bin/env python
"""
manage.py estándar del proyecto Django
"""

import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()