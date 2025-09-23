import requests
import json
import tempfile
import os

import sounddevice as sd
from scipy.io import wavfile
from google.oauth2 import id_token
from google.auth.transport import requests as grequests


class SpeechSynthesis:
    """音声合成クラス"""
    def __init__(self, speaker=3):
        """
        speaker: VoiceVox のスピーカー番号（ここではずんだもんの例として 3 を指定）
        """
        self.speaker = speaker
        self.audio_query_url = os.getenv("AUDIO_QUERY_URL")
        self.synthesis_url = os.getenv("SYNTHESIS_URL")
        self.CLOUDRUN_URL = os.getenv("CLOUDRUN_URL")
        self.__TOKEN = self.__get_id_token(self.CLOUDRUN_URL)

    def __get_id_token(self, audience_url):
        """
        サービスアカウントキーを使用してIDトークンを取得します。
        環境変数 GOOGLE_APPLICATION_CREDENTIALS が設定されている必要があります。
        """
        print("IDトークンを取得しています...")
        auth_req = grequests.Request()
        token = id_token.fetch_id_token(auth_req, audience_url)
        print("IDトークンを取得しました。")
        return token

    def play_speech(self, text: str):
        """音声合成を行い、音声を再生する
        text: 合成するテキスト
        """
        audio_data = self.__get_voicevox_audio(text)
        if audio_data:
            self.__play_audio(audio_data)
        else:
            print("音声合成に失敗しました。")
        return

    def __get_voicevox_audio(self, text : str):
        """VoiceVox の音声合成を行う
        test: 合成するテキスト
        """
        # 1. audio_query エンドポイントで合成用パラメータを取得
        params = {"text": text, "speaker": self.speaker}
        headers = {"CustomAuthorization": os.getenv("VOICEVOX_BASIC_PASSWORD"), 'Authorization': f'Bearer {self.__TOKEN}',}
        r = requests.post(
                self.audio_query_url,
                params=params,
                headers=headers,
                # verify=False,
            )
        if r.status_code != 200:
            print("audio_query に失敗しました:", r.text)
            return None
        query = r.json()
        # 2. synthesis エンドポイントで音声合成
        headers = {"Content-Type": "application/json", "CustomAuthorization": os.getenv("VOICEVOX_BASIC_PASSWORD"), 'Authorization': f'Bearer {self.__TOKEN}',}
        r2 = requests.post(
                self.synthesis_url,
                params={"speaker": self.speaker},
                data=json.dumps(query),
                headers=headers,
                # verify=False
            )
        if r2.status_code != 200:
            print("synthesis に失敗しました:", r2.text)
            return None
        return r2.content  # WAV バイナリデータ


    def __play_audio(self, audio_data):
        """WAV 音声を再生する
        audio_data: WAV データのバイナリ
        """
        # 一時ファイルに書き出して再生（simpleaudio を利用）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data)
            filename = f.name
        try:
            samplerate, data = wavfile.read(filename)
            sd.play(data, samplerate)
            sd.wait()# 再生が終わるまで待機
        except Exception as e:
            print("音声再生に失敗しました:", e)
        finally:
            os.remove(filename)
