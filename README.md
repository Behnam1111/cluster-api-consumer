# Cluster API Consumer: Reliable Object Creation and Deletion in a Cluster

Cluster API Consumer is a reliable client module for creating and deleting group_id in a cluster. It interacts with the cluster's nodes using the Cluster API endpoints and implements error handling and rollback mechanisms to ensure reliability. The module includes unit tests, a Docker image, and Kubernetes manifests.

This module designed to provide a single interface for the internal apis in each node to encapsulate the creation and deletion of group ids in the nodes and be like a central gateway to make proper actions based on failure or success of actions to ensure the consistency of nodes.

To explain this concept better, consider we have three nodes A,B and C. we want to create a group_id in all the nodes.

First Scenario: if A,B and C are all up and running, and the operation is successful, the module will create the group_id in all the nodes.

Second Scenario: if A,B are up and running and C id down, we start from node A and B and create the group_id in A and B. because C is down, we have to rollback the changes made in A and B by deleting the group_id in A and B.
in this scenario A,B are still up and the rollback operation is successful.

Third scenario: like the second scenario, but in this case when we want to rollback changes in node B, we will get an error because node B is down. now we have inconsistency problem because node A and C does not have the group_id and node B has the group_id. to address this problem, we leveraged RQ library to enqueue a job to delete the group_id in node B. a worker should be running to process the jobs, if the rollback operation fails, the job will be retried after a delay, by enqueuing it again. if the job succeeds, the job will be deleted from the queue. by using this approach we can be sure that the group_id will be deleted from all the nodes to achieve eventual consistency.

For using this module easier, An api is exposed which is written in FastAPI.

## Setup

1. Clone the repository

```bash
git clone https://github.com/Behnam1111/cluster-api-consumer

```

2. Run Docker-compose
```bash
docker-compose up -d
'''

3. Set up environment variables
    create an .env file in the root directory of the project and add your endpoints variables:
    example:
     HOSTS=node1.example.com,node2.example.com,node3.example.com

4. Access the API
    The documentation of the API is available at http://localhost:8000/docs
    you can use create and delete endpoints to create and delete group_id in the cluster.



