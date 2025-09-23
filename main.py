import time
import asyncio

import dotenv
# 環境変数の読み込み
dotenv.load_dotenv()

from module.speech_synthesis import SpeechSynthesis
from module.zunda_agent import ZundaAgent
from module.realtime_transcription import RealtimeTranscriptionStream


# TODO: 一定時間がたったら、セッションを初期化する処理を追加する
async def main(zunda_instance: ZundaAgent, transcript_instance: RealtimeTranscriptionStream, speech_instance: SpeechSynthesis):
    # メイン処理の実装箇所
    pre_user_input = ""
    user_input = ""
    while True:
        print("音声入力を待機中...")
        # TODO: 音声入力の取得間隔にコンマ秒だけ取得できない時間があるので調査
        pre_user_input = await transcript_instance.realtime_transcribe()
        if pre_user_input == "":
            continue
        print(f"✅ 音声入力: {pre_user_input}")
        if not pre_user_input or len(pre_user_input) < 3: # 入力なしの場合
            if user_input == "":
                # 何も入力がない場合は、デフォルトのプロンプトを送信
                pass# zunda_instance.send_query(default_prompt)
            else:
                # 前回、文章の終わりを検出できなかった場合の処理。ずんだもんエージェントにクエリを送信
                agent_output = await zunda_instance.run_conversation(user_input)
                speech_instance.play_speech(agent_output)
                user_input = ""  # クエリ送信後はインプットをリセット
        else:# 音声入力ありの場合、インプットを更新
            user_input += pre_user_input
        # 文章の終わりを検出したら、エージェントにクエリを送信
        if True:
            agent_output = await zunda_instance.run_conversation(user_input)
            speech_instance.play_speech(agent_output)
            user_input = ""
        time.sleep(0.01)


if __name__ == "__main__":
    # 各インスタンスを生成
    zunda_instance = ZundaAgent(user_id="test_user", session_id="test_session")
    transcript_instance = RealtimeTranscriptionStream()
    speech_instance = SpeechSynthesis()

    # メイン処理を実行
    try:
        asyncio.run(
            main(
                zunda_instance = zunda_instance,
                transcript_instance = transcript_instance,
                speech_instance = speech_instance
            )
        )
    except KeyboardInterrupt:
        print("\nプログラムを終了しました。")

