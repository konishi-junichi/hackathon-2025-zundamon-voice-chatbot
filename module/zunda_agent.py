import os
import asyncio
import traceback

import google.auth
import vertexai
import google.generativeai as genai
from google.adk.agents import Agent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from module.model_armor_plugin import ModelArmorPlugin
from module.main_agent.zunda_agent.agent import root_agent as zundamon_root_agent


class ZundaAgent():
    """ずんだもんのエージェントクラス"""
    def __init__(self, user_id: str, session_id: str):
        # 初期値設定
        self.__APP_NAME = "zundamon_app"
        self.__USER_ID = user_id
        self.__SESSION_ID = session_id
        # セッション生成
        self.__session_service = InMemorySessionService()
        # モデルアーマー
        self.__model_armor_ins = ModelArmorPlugin()

        # Vertex AIのリージョンを設定
        self.__LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "asia-northeast1")

        try:
            # デフォルトの認証情報とプロジェクトIDを取得
            credentials, project_id = google.auth.default()
            if not project_id:
                project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
                if not project_id:
                    raise ValueError(
                        "Google CloudのプロジェクトIDを特定できませんでした。"
                        "環境変数 `GOOGLE_CLOUD_PROJECT` を設定するか、"
                        "gcloud CLIで `gcloud config set project YOUR_PROJECT_ID` を実行してください。"
                    )

            # 1. vertexaiライブラリを初期化し、プロジェクトとロケーションのコンテキストを設定します。
            vertexai.init(project=project_id, location=self.__LOCATION, credentials=credentials)

            # 2. genaiライブラリに、通信バックエンドとしてVertex AIを使用するよう明示的に指示します。
            # これにより、ADKが内部でgenaiを呼び出す際に、自動的にVertex AIが使われるようになります。
            genai.configure(transport="vertex_ai")

            # 上記の設定により、ADKは正しいバックエンドを自動的に見つけます。
            self.__root_agent = zundamon_root_agent
            
            # Runner（エージェント実行クラス）の生成
            self.__runner = Runner(
                agent=self.__root_agent,
                app_name=self.__APP_NAME,
                session_service=self.__session_service,
                # plugins=[ModelArmorPlugin()]
            )
        except google.auth.exceptions.DefaultCredentialsError:
            print("!!! ERROR: 認証に失敗しました。")
            raise
        except Exception as e:
            print(f"!!! 初期化中に予期せぬエラーが発生しました: {e}")
            raise

    def send_query(self, query: str):
        """Agent実行"""
        try:
            asyncio.run(self.run_conversation(query=query))
        except Exception:
            print(traceback.format_exc())

    async def call_agent_async(self, query: str):
        """エージェントにクエリを送信して、最終結果を取得する非同期メソッド"""
        content = types.Content(role='user', parts=[types.Part(text=query)])
        final_response_text = "Agent did not produce a final response."
        async for event in self.__runner.run_async(user_id=self.__USER_ID, session_id=self.__SESSION_ID, new_message=content):
            print(event.actions)
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    break
        # Model Armorでの応答内容チェック
        if self.__model_armor_ins.call_model_armor_api(final_response_text):
            print(f"<<< Zundamon Agent: {final_response_text}")
        else:
            final_response_text = "申し訳ないのだが、その内容にはお答えできないのだ。別の質問をお願いするのだ〜。"
            print(f"<<< Zundamon Agent: {final_response_text}")
        return final_response_text

    async def run_conversation(self, query: str = ""):
        """エージェントで会話実行"""
        existing_session = await self.__session_service.get_session(
            app_name=self.__APP_NAME,
            user_id=self.__USER_ID,
            session_id=self.__SESSION_ID
        )
        if existing_session is None:
            await self.__session_service.create_session(
                app_name=self.__APP_NAME,
                user_id=self.__USER_ID,
                session_id=self.__SESSION_ID
            )
        return await self.call_agent_async(
            query=query,
        )
