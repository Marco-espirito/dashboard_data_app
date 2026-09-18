"""Explicit WSGI entrypoint for Vercel's Python runtime."""

from dashboard_data_project.wsgi import application

app = application
