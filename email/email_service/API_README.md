# Email Service FastAPI

一个完整的邮件服务FastAPI应用，提供邮件读取、发送和草稿箱管理功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd email_service
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python start_server.py
```

或者使用uvicorn直接启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API状态: http://localhost:8000/api/v1/status

## 📚 API接口文档

### 邮件读取 (Emails)

#### 获取邮件列表
```http
GET /api/v1/emails/{user_id}/{account_id}
```

参数：
- `limit`: 最大邮件数量 (默认: 50)
- `offset`: 跳过的邮件数量 (默认: 0)
- `unread_only`: 只返回未读邮件 (默认: false)
- `since_date`: 只返回此日期之后的邮件 (ISO格式)

#### 获取特定邮件
```http
GET /api/v1/emails/{user_id}/{account_id}/{message_id}
```

#### 搜索邮件
```http
GET /api/v1/emails/{user_id}/{account_id}/search?query=关键词&limit=10
```

#### 标记邮件为已读/未读
```http
POST /api/v1/emails/{user_id}/{account_id}/mark-read
POST /api/v1/emails/{user_id}/{account_id}/mark-unread
```

请求体：
```json
{
  "message_id": "邮件ID"
}
```

### 邮件发送 (Send)

#### 发送单个邮件
```http
POST /api/v1/send/{user_id}/{account_id}
```

请求体：
```json
{
  "to_emails": ["recipient@example.com"],
  "subject": "邮件主题",
  "body": "邮件内容",
  "is_html": false,
  "cc_emails": ["cc@example.com"],
  "bcc_emails": ["bcc@example.com"]
}
```

#### 批量发送邮件
```http
POST /api/v1/send/{user_id}/{account_id}/bulk
```

请求体：
```json
{
  "emails": [
    {
      "to_emails": ["user1@example.com"],
      "subject": "邮件1",
      "body": "内容1"
    },
    {
      "to_emails": ["user2@example.com"],
      "subject": "邮件2",
      "body": "内容2"
    }
  ],
  "batch_size": 10
}
```

#### 获取发送历史
```http
GET /api/v1/send/{user_id}/history
GET /api/v1/send/{user_id}/{account_id}/history
```

### 草稿箱管理 (Drafts)

#### 创建草稿
```http
POST /api/v1/drafts/{user_id}/{account_id}
```

请求体：
```json
{
  "to_emails": ["recipient@example.com"],
  "subject": "草稿主题",
  "body": "草稿内容",
  "is_html": false
}
```

#### 更新草稿
```http
PUT /api/v1/drafts/{user_id}/{draft_id}
```

请求体：
```json
{
  "subject": "更新的主题",
  "body": "更新的内容"
}
```

#### 获取草稿
```http
GET /api/v1/drafts/{user_id}/{draft_id}
```

#### 获取用户所有草稿
```http
GET /api/v1/drafts/{user_id}?limit=50&offset=0
```

#### 删除草稿
```http
DELETE /api/v1/drafts/{user_id}/{draft_id}
```

#### 发送草稿
```http
POST /api/v1/drafts/{user_id}/{draft_id}/send
```

#### 复制草稿
```http
POST /api/v1/drafts/{user_id}/{draft_id}/duplicate
```

#### 搜索草稿
```http
GET /api/v1/drafts/{user_id}/search?query=关键词&limit=10
```

### 账户管理 (Accounts)

#### 获取用户账户
```http
GET /api/v1/accounts/{user_id}
```

#### 获取OAuth授权URL
```http
GET /api/v1/accounts/{user_id}/auth-url/{provider}
```

支持的provider: `google`, `outlook`, `yahoo`

#### OAuth回调处理
```http
POST /api/v1/accounts/{user_id}/oauth-callback/{provider}
```

请求体：
```json
{
  "code": "授权码",
  "state": "状态参数"
}
```

#### 获取统计信息
```http
GET /api/v1/accounts/{user_id}/statistics
```

#### 获取支持的提供商
```http
GET /api/v1/accounts/providers
```

## 🔧 使用示例

### Python客户端示例

```python
import requests

# 基础URL
BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "user_123"
ACCOUNT_ID = "account_456"

# 获取邮件
response = requests.get(f"{BASE_URL}/emails/{USER_ID}/{ACCOUNT_ID}?limit=10")
emails = response.json()

# 发送邮件
email_data = {
    "to_emails": ["recipient@example.com"],
    "subject": "测试邮件",
    "body": "这是一封测试邮件"
}
response = requests.post(f"{BASE_URL}/send/{USER_ID}/{ACCOUNT_ID}", json=email_data)
result = response.json()

# 创建草稿
draft_data = {
    "to_emails": ["recipient@example.com"],
    "subject": "草稿邮件",
    "body": "这是草稿内容"
}
response = requests.post(f"{BASE_URL}/drafts/{USER_ID}/{ACCOUNT_ID}", json=draft_data)
draft = response.json()
```

### cURL示例

```bash
# 获取邮件
curl -X GET "http://localhost:8000/api/v1/emails/user_123/account_456?limit=10"

# 发送邮件
curl -X POST "http://localhost:8000/api/v1/send/user_123/account_456" \
  -H "Content-Type: application/json" \
  -d '{
    "to_emails": ["recipient@example.com"],
    "subject": "测试邮件",
    "body": "这是一封测试邮件"
  }'

# 创建草稿
curl -X POST "http://localhost:8000/api/v1/drafts/user_123/account_456" \
  -H "Content-Type: application/json" \
  -d '{
    "to_emails": ["recipient@example.com"],
    "subject": "草稿邮件",
    "body": "这是草稿内容"
  }'
```

## 🛠️ 运行示例

运行API使用示例：

```bash
python api_examples.py
```

## 🔒 安全配置

在生产环境中，请配置以下环境变量：

```bash
# CORS设置
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# 信任的主机
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# 日志级别
LOG_LEVEL=warning
```

## 📊 监控和日志

API提供以下监控端点：

- `/health` - 健康检查
- `/api/v1/status` - API状态
- 所有请求都会记录到日志中

## 🚨 错误处理

API使用标准的HTTP状态码：

- `200` - 成功
- `400` - 请求错误
- `404` - 资源未找到
- `500` - 服务器错误

错误响应格式：
```json
{
  "error": "错误类型",
  "message": "错误描述",
  "status_code": 400,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## �� 自动Token刷新

API自动处理OAuth token的刷新，无需手动干预。当Google token过期时，系统会自动使用refresh token获取新的access token。

## 📈 性能优化

- 批量操作支持速率限制
- 分页支持大量数据
- 异步处理提高并发性能
- 自动数据清理功能

## 🧪 测试

启动服务器后，可以访问 http://localhost:8000/docs 进行交互式API测试。
