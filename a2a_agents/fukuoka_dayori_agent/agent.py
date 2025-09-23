import os

from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool

root_agent = Agent(
    name='fukuoka_dayori_agent',
    model="gemini-2.5-flash",
    description=('福岡市の市政だよりのデータを基に質問に答えるエージェントです。'),
    instruction=('あなたはVertex AIのデータストアに保存された福岡市の市政だよりの情報を基に、ユーザーからの質問に答えるエージェントです。質問には正確かつ簡潔に必ず100文字以内で答えてください。'),
    tools=[
        VertexAiSearchTool(data_store_id=os.environ['DATASTORE_ID_FUKUOKA_DAYORI']),
    ],
)
