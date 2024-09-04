# Leader Election Demo

This project demonstrates a leader election process using ZooKeeper and Flask. It consists of a Flask application that runs multiple instances and elects a leader among them using ZooKeeper.

## Prerequisites

- Kubernetes cluster (e.g., EKS, minikube)
- Helm (for installing ZooKeeper)
- Docker (for building the application image)
- AWS CLI (for pushing the image to ECR)

## Step 1: Install ZooKeeper using Helm

1. Add the Bitnami Helm repository:
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

2. Install ZooKeeper in the default namespace:
helm install zookeeper bitnami/zookeeper \
  --namespace zookeeper \
  --set replicaCount=3 \
  --set auth.enabled=false \
  --set allowAnonymousLogin=true \
  --set persistence.storageClass=gp2 \
  --set persistence.size=10Gi

           
## Step 2: Build and Push the Docker Image

1. Build the Docker image for the Flask application:
docker build -t leader-election-demo .

2. Authenticate with Amazon ECR:
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com

3. Tag the Docker image with your ECR repository URI:
docker tag leader-election-demo:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/leader-election-demo:latest

4. Push the Docker image to ECR:
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/leader-election-demo:latest

## Step 3: Deploy the Application

Create a Kubernetes Statefulset for the Flask application:
kubectl apply -f deployment.yaml

After completing these steps, you should have ZooKeeper installed in the default namespace, the Flask application Docker image pushed to ECR, and the application deployed as a Kubernetes Deployment with a LoadBalancer Service exposing it. You will see only one pod among three replicas will be elected as the leader and when the leader pod fails, a new leader will be elected among the rest of the pods.
