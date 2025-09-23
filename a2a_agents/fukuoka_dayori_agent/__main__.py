import asyncio
import functools
import logging
import os

import click
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import DatabaseTaskStore, InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
load_dotenv()
from agent import root_agent as fukuoka_dayori_agent
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
        name=fukuoka_dayori_agent.name,
        description=fukuoka_dayori_agent.description,
        version='1.0.0',
        url=os.environ['APP_URL'],
        default_input_modes=['text', 'text/plain'],
        default_output_modes=['text', 'text/plain'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id='get_fukuoka_dayori_info',
                name='福岡市の市政だより情報の取得',
                description='福岡市の市政だよりに関する質問に答えます。',
                tags=['fukuoka', 'dayori', '福岡', '市政だより', '行政', '生活', 'ゴミ', '子育て', '防災', '観光', 'イベント', '交通', '健康', '地域'],
                examples=[
                    '福岡市のゴミの出し方を教えて', '子育て支援の情報は？', '防災に関する最新情報を教えて', '福岡市で開催されるイベントは？', '公共交通機関の利用方法を教えて',
                ],
            )
        ],
    )

    task_store = InMemoryTaskStore()

    request_handler = DefaultRequestHandler(
        agent_executor=ADKAgentExecutor(
            agent=fukuoka_dayori_agent,
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