import asyncio
import functools
import logging
import os

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
load_dotenv()
from agent import root_agent as yatai_agent
from agent_executor import ADKAgentExecutor
from starlette.applications import Starlette


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""


def make_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)
@make_sync
async def main(host, port):
    agent_card = AgentCard(
        name=yatai_agent.name,
        description=yatai_agent.description,
        version='1.0.0',
        url=os.environ['APP_URL'],
        default_input_modes=['text', 'text/plain'],
        default_output_modes=['text', 'text/plain'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id='get_yatai_info',
                name='Get Fukuoka Yatai Info',
                description='福岡の屋台に関する質問に答えます。',
                tags=['fukuoka', 'yatai', 'get'],
                examples=[
                    '福岡のおすすめのラーメン屋台を教えて',
                ],
            )
        ],
    )

    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=yatai_agent,
        ),
        task_store=task_store,
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )
    routes = a2a_app.routes()
    app = Starlette(
        routes=routes,
        middleware=[],
    )

    config = uvicorn.Config(app, host=host, port=port, log_level='info')
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    main()