Install Uv, if you use Linux please use command below to install Uv: 
curl -LsSf https://astral.sh/uv/install.sh | sh

Đây là phiên bản update đầu tiên của MCP Server:
Idea: Ý tưởng là sử dụng MCP server như một API Backend cho LLM Agent có thể query dữ liệu xuống database.
Case ý tưởng tại project: Database chứa thông tin của các mặt hàng (thông tin mặt hàng này được lưu từ một hệ thống E-commerce) , LLM-Agent có thể dựa theo prompt đầu vào của user để query xuống database
Ví dụ: Promt đầu vào là: Hãy cho tôi biết mặt hàng nào bán chạy ngày hôm nay, LLM Agent sẽ query dữ liệu dưới database lấy ra mặt hàng bán chạy. 
Triển khai sơ bộ phần server : 
├── server
│   ├── pyproject.toml
│   ├── server.py
│   └── Dockerfile

- File server.py dùng để định nghĩa API @tool.mcp để query thông tin database.
- Dockerfile dùng để build cấu hình deploy MCP server lên GKE
- File pyproject.toml có thể hiểu như requirement.txt

Step 1: cấu hình project GKE
```
gcloud auth login
export PROJECT_ID=<your-project-id>
gcloud config set project $PROJECT_ID
```

Install FastMCP: uv add fastmcp==2.6.1 --no-sync

Step 2: Deploy lên GKE
ta build cấu hình Dockerfile lên sau đó đẩy lên Artifact Registry - nơi chứa Image của app

- Tạo artifact chứa container registry
```
gcloud artifacts repositories create remote-mcp-servers \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repository for remote MCP servers" \
  --project=$PROJECT_ID
``

- Sau đó build image và push lên cloud build

```
gcloud run deploy mcp-server \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/remote-mcp-servers/mcp-server:latest \
  --region=us-central1 \
  --no-allow-unauthenticated
```

- Vì mình dùng cái cờ --no-allow-unauthenticated nên mình phải chạy proxy:

```
gcloud run services proxy mcp-server --region=us-central1
```


Ta sẽ thấy 1 thông báo dạng:

```
Proxying to Cloud Run service [mcp-server] in project [<YOUR_PROJECT_ID>] region [us-central1]
http://127.0.0.1:8080 proxies to https://mcp-server-abcdefgh-uc.a.run.app
```





