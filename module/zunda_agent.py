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
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.api_core.client_options import ClientOptions
from google.adk.plugins.base_plugin import BasePlugin
from google.cloud import modelarmor_v1


remote_yatai_agent = RemoteA2aAgent(
    name="屋台エージェント", agent_card="https://fukuoka-yatai-a2a-agent-96292749133.asia-northeast1.run.app/.well-known/agent.json"
)

remote_dayori_agent = RemoteA2aAgent(
    name="福岡市エージェント", agent_card="https://fukuoka-dayori-a2a-agent-96292749133.asia-northeast1.run.app/.well-known/agent.json"
)

class ModelArmorPlugin(BasePlugin):
    """A custom plugin that counts agent and tool invocations."""

    def __init__(self) -> None:
        """Initialize the plugin with counters."""
        super().__init__(name="model armor plugin")
        self._model_armor_client = modelarmor_v1.ModelArmorClient(
            client_options=ClientOptions(
                api_endpoint = "modelarmor.asia-southeast1.rep.googleapis.com"
            )
        )
        self.template_name = "projects/my-project-20250906/locations/asia-southeast1/templates/zundamon-model-armor"

    # async def after_run_callback(
    #     self, *, invocation_context
    # ) -> None:
    #     data_item = modelarmor_v1.DataItem(text=invocation_context.parts[0].text)
    #     request = modelarmor_v1.SanitizeModelResponseRequest(
    #         name=self.template_name,
    #         model_response_data=data_item,
    #     )
    #     try:
    #         response = self._model_armor_client.sanitize(request=request)
    #         if response.detection.blocked:
    #             print("AIエージェントの実行はブロックされました。")
    #             print(f"理由: {response.detection.reasons}")
    #         else:
    #             print("clear")
    #     except Exception as e:
    #         print(f"エラーが発生しました: {e}")

    def call_model_armor_api(self, text: str):
        """Model Armor APIを呼び出す"""
        data_item = modelarmor_v1.DataItem(text=text)
        request = modelarmor_v1.SanitizeModelResponseRequest(
            name=self.template_name,
            model_response_data=data_item,
        )
        try:
            # Model Armor APIを呼び出し
            response = self._model_armor_client.sanitize_model_response(request=request)
            # 結果の処理
            if response.sanitization_result.invocation_result != True:
                print(f"AIエージェントの実行はブロックされました。\n理由: {response.sanitization_result}")
                return False
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return False
        return True


class ZundaAgent():
    """ずんだもんのエージェントクラス"""
    def __init__(self, user_id: str, session_id: str):
        # 初期値設定
        self.__APP_NAME = "zundamon_app"
        AGENT_NAME = "zundamon_agent"
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
            self.__root_agent = Agent(
                name=AGENT_NAME,
                model="gemini-2.5-flash", # モデル名を文字列で渡すだけでOK
                description=(
                    "ユーザーからの質問に対して回答するずんだもんエージェント"
                ),
                instruction=(
                    """
                    【概要】
                    あなたは「ずんだもん」というキャラクターになりきって会話をします。
                    【重要事項】
                    以下の点を必ず守り回答してください。
                    - ★返答の文字数は、必ず100文字以内に収めてください★
                    - キャラクターの一貫性を保ち、ずんだもんらしい言葉遣いと雰囲気を忘れずに会話してください。
                    - 屋台エージェントや福岡市エージェントに質問が関連している場合は、適切に情報を引き出して回答に活用してください。
                    【キャラ設定】
                    ずんだもんは東北地方の方言を交えた、かわいらしくて元気な性格のキャラクターです。語尾には「〜なのだ」「〜なのだよ」「〜なのだ〜」など、ずんだもん特有の言い回しを使ってください。語調は親しみやすく、少し幼い感じで、ユーザーに優しく接します。
                    質問には丁寧に答え、時にはユーモアを交えて楽しく会話を続けます。ユーザーが悲しんでいたり困っていたら、励ましたり元気づけたりするようにしてください。
                    例：
                    - 「こんにちはなのだ〜！今日はどんなことを話すのだ？」
                    - 「それはすごいのだ！ずんだもんもびっくりなのだよ〜」
                    - 「うーん、それはちょっと難しいのだ…でも一緒に考えるのだ！」
                    """
                ),
                sub_agents=[
                    remote_dayori_agent,
                    remote_yatai_agent
                ],
                tools=[
                ],
            )
            
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
