# Demo Agents ADK Web

ずんだもんエージェントを使用するためのデモ用Webアプリ

## 起動方法

1. （Optional）Dockerイメージのビルド

   ```bash
   docker build -t a2a-agent .
   ```

2. （Optional）コンテナの起動

   以下の環境変数を設定してコンテナを起動。最下部の環境変数の設定必要。
      ```bash
      docker run -p 8080:8080 a2a-agent
      ```

3. デプロイする

    マネージドのサービスアカウント（XXXXXX@cloudbuild.gserviceaccount.com, XXXXX-compute@developer.gserviceaccount.com）に「Artifact Registry 書き込み」の権限を付与しておくこと。
    ※最下部の環境変数を設定必要

   ```shell
   gcloud auth configure-docker asia-docker.pkg.dev
   gcloud run deploy zundamon-adk-web-demo \
      --port=8080 \
      --source=. \
      --no-allow-unauthenticated \
      --memory "4Gi" \
      --region="asia-northeast1" \
      --project="YOUR_PROJECT_ID" \
      --service-account YOUR_SERVICE_ACCOUNT_NAME \
      --set-env-vars=APP_URL="https://zundamon-adk-web-demo-PROJECT_NUMBER.REGION.run.app"
   ```

   ※環境変数は以下を設定

      ```
      GOOGLE_APPLICATION_CREDENTIALS="/app/service_account.json"
      GOOGLE_CLOUD_PROJECT="プロジェクトID"
      GOOGLE_GENAI_USE_VERTEXAI=true
      GOOGLE_CLOUD_LOCATION="global"
      REMOTE_YATAI_AGENT_CARD="XXX"
      REMOTE_DAYORI_AGENT_CARD="XXX"
      ```