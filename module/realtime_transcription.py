# -*- coding: utf-8 -*-

import asyncio
import time
import sounddevice as sd
import numpy as np
from google.cloud import speech

# --- Google Cloud Speech-to-Text 設定 ---
# ※ 下記の値は環境に合わせて変更してください
# 例: "en-US" や "ja-JP" など
LANGUAGE_CODE = "ja-JP"
SAMPLE_RATE = 16000  # サンプリングレート（16kHz）
CHANNEL_NUMS = 1      # モノラル音声

class RealtimeTranscriptionStream:
    """Google Cloud Speech-to-Text を使用したリアルタイム文字起こし"""

    def __init__(self):
        """初期化"""
        # 音声検出のパラメータ
        self.SILENCE_THRESHOLD = 0.01  # 無音の閾値（調整可能）
        self.SILENCE_DURATION = 2.0    # 無音が続く時間（秒）
        self.MIN_RECORDING_TIME = 1.0  # 最小録音時間（秒）
        # 音声検出用の変数
        self.is_speaking = False
        self.last_speech_time = 0
        self.recording_start_time = 0
        self.should_stop_recording = False
        # 音声データを非同期にやり取りするためのキュー
        self.audio_queue = asyncio.Queue()

    def detect_speech(self, audio_data):
        """音声の有無を検出"""
        rms = np.sqrt(np.mean(audio_data ** 2))
        current_time = time.time()
        if rms > self.SILENCE_THRESHOLD:
            if not self.is_speaking:
                self.is_speaking = True
                self.recording_start_time = current_time
                print("🎤 音声検出開始...")
            self.last_speech_time = current_time
        else:
            if self.is_speaking:
                silence_duration = current_time - self.last_speech_time
                recording_duration = current_time - self.recording_start_time
                if (recording_duration >= self.MIN_RECORDING_TIME and
                        silence_duration >= self.SILENCE_DURATION):
                    self.is_speaking = False
                    self.should_stop_recording = True
                    print("🛑 音声検出終了...")

    async def write_chunks_to_queue(self):
        """マイクからの音声入力を取得し、キューに書き込む"""
        loop = asyncio.get_running_loop()
        def callback(indata, frames, time, status):
            if status:
                print(f"Sounddevice status: {status}")
            self.detect_speech(indata.flatten())
            
            # PCMデータに変換してキューに追加
            pcm_data = (indata * 32767).astype(np.int16).tobytes()
            # 別スレッドからイベントループのキューに安全に追加
            loop.call_soon_threadsafe(self.audio_queue.put_nowait, pcm_data)

        print("🎙️ 音声入力を開始します。話し始めてください...")
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNEL_NUMS,
            dtype='float32',
            callback=callback
        ):
            while not self.should_stop_recording:
                await asyncio.sleep(0.1)
        # 録音が完了したら、ストリームの終了を示すためにNoneをキューに入れる
        loop.call_soon_threadsafe(self.audio_queue.put_nowait, None)
        print("✅ 録音完了")

    async def stream_requests(self):
        """キューから音声データを読み込み、Google Cloud APIへのリクエストを生成する"""
        # 最初に設定情報を送信
        yield speech.StreamingRecognizeRequest(
            streaming_config=speech.StreamingRecognitionConfig(
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=SAMPLE_RATE,
                    language_code=LANGUAGE_CODE,
                ),
                interim_results=False, # 中間結果は表示しない
            )
        )
        while True:
            # キューから音声データを取得
            chunk = await self.audio_queue.get()
            if chunk is None:
                # 終了シグナルを受け取ったらジェネレータを終了
                break
            # 音声データをリクエストとしてyield
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def realtime_transcribe(self):
        """リアルタイム文字起こしのメイン処理"""
        # 状態をリセット
        self.is_speaking = False
        self.should_stop_recording = False
        self.last_speech_time = 0
        self.recording_start_time = 0
        # 古いデータが残らないようにキューをクリア
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

        client = speech.SpeechAsyncClient()
        requests = self.stream_requests()

        # マイクからの音声入力をバックグラウンドタスクとして開始
        mic_task = asyncio.create_task(self.write_chunks_to_queue())

        transcript_parts = []
        try:
            responses = await client.streaming_recognize(requests=requests)

            # レスポンスから文字起こし結果を抽出
            async for response in responses:
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue
                
                # interim_results=False のため、得られる結果は常に最終的なもの
                transcript_parts.append(result.alternatives[0].transcript)

        except Exception as e:
            # NOTE: 5分後にエラー（400 Exceeded maximum allowed stream duration of 305 seconds.）が発生して、この処理に入る。
            print(f"文字起こし中にエラーが発生しました: {e}")
            return "何か挨拶か雑談をしてください（自己紹介, しゃべりかけてほしいとお願いする, 最近のトレンド情報を紹介するなど）"
        
        # マイクのタスクが完了するのを待つ
        await mic_task

        # 常に文字列を返す（結果がない場合は空文字列）
        return "".join(transcript_parts)


# --- メイン処理（テスト用） ---
async def _test_transcription():
    """文字起こしのテスト"""
    transcriber = RealtimeTranscriptionStream()
    while True:
        print("-" * 20)
        transcript = await transcriber.realtime_transcribe()
        if transcript:
            print(f"✅ 認識結果: {transcript}")
        else:
            print("音声が認識されませんでした。")
        
        # '終了'と発話されたらテストを終了
        if transcript == "終了":
            print("テストを終了します。")
            break

if __name__ == '__main__':
    print("リアルタイム文字起こしのテストを開始します。'終了'と話すとプログラムが終了します。")
    try:
        asyncio.run(_test_transcription())
    except KeyboardInterrupt:
        print("\nプログラムを強制終了します。")
