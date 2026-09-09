import logging

from agent.server import create_app

logging.basicConfig(level=logging.INFO)

app = create_app()

