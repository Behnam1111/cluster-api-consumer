# Cluster API Consumer: Reliable Object Creation and Deletion in a Cluster

Cluster API Consumer is a reliable client module for creating and deleting group_id in a cluster. It interacts with the cluster's nodes using the Cluster API endpoints and implements error handling and rollback mechanisms to ensure reliability. The module includes unit tests, a Docker image, and Kubernetes manifests.

## Purpose
The primary purpose of the Cluster API Consumer is to act as a central gateway, encapsulating the creation and deletion of group_ids in each node of the cluster. By providing a single interface, it simplifies the process and ensures consistent actions based on the success or failure of operations.

To illustrate this concept further, let's consider a scenario where we have three nodes: A, B, and C. Our objective is to create a group_id across all the nodes.

First Scenario: In an ideal situation where all nodes (A, B, and C) are up and running, the module will successfully create the group_id in all the nodes.

Second Scenario: If nodes A and B are up and running, but node C is down, the module will create the group_id in nodes A and B. However, due to the failure of node C, a rollback mechanism is triggered, and the group_id is deleted from nodes A and B. This ensures consistency even in the event of a failure.

Third Scenario: Similar to the second scenario, but when attempting to rollback changes in node B, an error occurs because node B is down. To address this inconsistency problem, we utilize the RQ library. We enqueue a job to delete the group_id in node B, and a worker is responsible for processing the jobs. If the rollback operation fails, the job will be retried after a delay. Conversely, if the job succeeds, it will be deleted from the queue. This approach guarantees that the group_id will eventually be deleted from all nodes, achieving eventual consistency.

## Setup
Follow these steps to set up the Cluster API Consumer:

Clone the repository:

```bash
git clone https://github.com/Behnam1111/cluster-api-consumer
```
Run Docker Compose:
You can easily use Docker Compose to run the project:

```bash
docker-compose up -d
```
Set up environment variables:
Create an .env file in the root directory of the project and add your endpoint variables. For example:

HOSTS=node1.example.com,node2.example.com,node3.example.com

## Usage
To access the API, visit the documentation available at http://localhost:8000/docs. The API provides endpoints for creating and deleting group_ids in the cluster.

## RQ
After running the docker-compose command, you can access rq dashboard at http://localhost:9181/


## Kubernetes manifests (Optional)
you can also apply kubernetes manifests in manifests folder by running the following commands:

```bash
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml
kubectl apply -f app-deployment.yaml
kubectl apply -f app-service.yaml
kubectl apply -f rq-worker-deployment.yaml
kubectl apply -f rq-dashboard-deployment.yaml

```