# Day 6 — AWS Deployment

Goal: ship the API to ECS Fargate using Bedrock for LLM. ~2 hours end-to-end.

## Prereqs

- AWS CLI configured (`aws configure`)
- Docker running locally
- An AWS account with permissions for ECR, ECS, IAM, Bedrock

## Step 1 — Push image to ECR

```bash
# Variables
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO=sentinel-api

# Create repo
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

# Login
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build + push
docker build -t $ECR_REPO .
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

## Step 2 — Bedrock model access

In the AWS Console → Bedrock → Model access → request access for **Claude 3.5 Sonnet**.
Approval is usually instant for Anthropic models in `us-east-1`.

## Step 3 — IAM task role

Create a role named `sentinel-task-role` with these inline policies:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-*"
    }
  ]
}
```

Trust policy: `ecs-tasks.amazonaws.com`.

## Step 4 — ECS cluster + task definition

```bash
aws ecs create-cluster --cluster-name sentinel-cluster
```

Save this as `task-def.json`, fill in your account ID:

```json
{
  "family": "sentinel-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/sentinel-task-role",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/sentinel-api:latest",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "essential": true,
      "environment": [
        {"name": "AWS_REGION", "value": "us-east-1"},
        {"name": "BEDROCK_MODEL_ID", "value": "anthropic.claude-3-5-sonnet-20241022-v2:0"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/sentinel-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
```

Register it:

```bash
aws ecs register-task-definition --cli-input-json file://task-def.json
```

## Step 5 — Service + ALB (public endpoint)

The fastest path: use the AWS Console wizard.

1. ECS → Clusters → `sentinel-cluster` → **Create service**
2. Launch type: **Fargate**, task: `sentinel-api`, desired count: 1
3. Networking: pick a default VPC + 2 public subnets, assign public IP: ENABLED
4. Load balancer: **Create Application Load Balancer**, target group → port 8000, health check `/health`
5. Click create.

After ~3 minutes, hit `http://<your-alb-dns>/health` and you should get `{"status":"ok"}`.

## Skipped (mention in README as "production architecture")

- **EKS + Helm** — overkill for a portfolio project
- **Kinesis** for streaming ingestion — Fargate + ALB handles burst traffic fine for a demo
- **DynamoDB** for state — SQLite is cheaper and works for `<50k` daily txns
- **WAF / API Gateway** — ALB is enough

## Cost estimate

~$15/month if left running:
- Fargate (0.5 vCPU, 1 GB, 1 task, 24/7): ~$10
- ALB: ~$5
- Bedrock: pay-per-token (~$0.003 per investigation)

To save: stop the service when not demoing.
