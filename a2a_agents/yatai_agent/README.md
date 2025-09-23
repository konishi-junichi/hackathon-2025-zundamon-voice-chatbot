# A2A Agents

屋台情報をもとに質問に回答するAIエージェント。

## 起動方法

1. （Optional）Dockerイメージのビルド

   ```bash
   docker build -t a2a-agent .
   ```

2. （Optional）コンテナの起動

   ```bash
   docker run -p 8080:8080 a2a-agent
   ```

3. デプロイする
　マネージドのサービスアカウント（XXXXXX@cloudbuild.gserviceaccount.com, XXXXX-compute@developer.gserviceaccount.com）に「Artifact Registry 書き込み」の権限を付与しておくこと。
```shell
gcloud auth configure-docker asia-docker.pkg.dev
gcloud run deploy fukuoka-yatai-a2a-agent \
    --port=8080 \
    --source=. \
    --no-allow-unauthenticated \
    --memory "4Gi" \
    --region="asia-northeast1" \
    --project="YOUR_PROJECT_ID" \
    --service-account a2a-service-account \
    --set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,\
GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID",\
GOOGLE_CLOUD_LOCATION="asia-northeast1",\
APP_URL="https://fukuoka-yatai-a2a-agent-PROJECT_NUMBER.REGION.run.app",\
DATASTORE_ID_FUKUOKA_YATAI="projects/YOUR_PROJECT_ID/locations/global/collections/default_collection/dataStores/DATASTORE_ID"
```

## 参考サイト
https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/adk_cloud_run

https://cloud.google.com/run/docs/deploy-a2a-agents?hl=ja#cloud-run-deployment-in-memory
