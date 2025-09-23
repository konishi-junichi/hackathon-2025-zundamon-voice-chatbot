import os

from google.api_core.client_options import ClientOptions
from google.adk.plugins.base_plugin import BasePlugin
from google.cloud import modelarmor_v1


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
        self.template_name = os.environ["MODELARMOR_TEMPLATE_NAME"]

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