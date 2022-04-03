## Section 1

### 1.1 TF-IDF Calculation
In order to calculate the TF-IDF of the terms in a given web page, the following formula has been used:
```
TF-IDF(t) = TF(t) * IDF(t) = TF(t) * ln((n+1)/(DF(t)+1)) + 1
```
Where,

- TF(t): Number of occurrences of the term t in the given page (article).
- DF(t): Number of documents (articles) in which the term t has occurred.
- n: Total number of documents (articles) in the dataset.

Two different approaches have been implemented to calculate the TF-IDFs:    
### Static Calculation    
In this approach, the document frequency (DF) of each available term in the given corpus is calculated and stored in a (local) data lake.   
Per each request, the TF-IDFs are calculated using the already processed DFs in the data lake.      
Alternatively, IDFs could be used too, but since we have to calculate the IDF for the terms missing in the corpus anyway, it wouldn't make a difference in terms of performance.   

In this project, the statistics (i.e., DFs) are stored in a local directory as our data lake for development.   
In production, the statistics should be stored in a cloud data lake (e.g., S3), or a data warehouse.
A data warehouse (e.g., AWS redshift) could offer a faster read performance, because for a typical data lake, we may have to load the whole data and then preform a query.

### Dynamic Calculation
In this approach, all the calculations (i.e., TF-IDFs, TFs, and DFs) are done per request (on demand) by performing searches 
in a fast NoSQL document-oriented database, called Elasticsearch.    

This is a better solution, practically when the database of documents grows constantly.     

### 1.2 How to run the API
Initially, you need to set up the API application by running the following script.      
```shell
sh setup_api.sh
```

Alternatively, you can follow the following steps.
1. Download the corpus from Kaggle into our local data lake. 
```shell
kaggle datasets download -d snapcrack/all-the-news -p data_lake/corpus/
```
Alternatively, you can download it manually into the relative `data_lake/corpus` directory.


2. Install docker-compose.
```shell
# Install docker-compose on Linux.
sudo apt-get install docker-compose
```

3. Initialize .env file. You can change the variables or leave it as it is.
```shell
cp .env.template .env
```
4. Setup dockerized environment.
```shell
docker-compose up --build -d
```

5. Seed database and data lake with initial required data to use the API.
```shell
# We have to enter the API container shell to run the python commands, unless we install the requirements locally.
docker exec -it $(docker ps -aqf "name=text_relevancy_api_web") python seed_database.py
```

After the setup, the API endpoint should be accessible at: http://127.0.0.1:8000/   
FastAPI also has a nice UI for testing which is accessible at: http://127.0.0.1:8000/docs   

### 1.3 How to test the API.
At first, I did some unit testings to verify the functionality of important statistics and dynamic services.    
Then, I tested the `tf-idf` API call for both static (dynamic=false) and dynamic calculation.    
Tests were first done on a small sample of articles in the corpus to make the debugging faster.

I also wrote a few API tests to verify the result for both dynamic and static calculations.
You can run the following commands to run the tests:
```shell
docker exec -it $(docker ps -aqf "name=text_relevancy_api_web") pytest
```

***Important Note***:     
The results for TF-IDFs in dynamic and static calculation could be different.   
This is because different algorithms and methods are used to tokenize and prune the terms.
For example, in static calculation, lemmatization by spaCy has been used,
but in dynamic calculation, [KStem-based stemming](https://ciir.cs.umass.edu/pubfiles/ir-35.pdf) has been used.

## Section 2

### 2.1 How to design a system to update statistics per request.
#### Database design:    
We have to store/update the page URL and content per request, otherwise the statistics will not be accurate (e.g. duplicate article) and can not be tracked.     
This leads to a constantly growing dataset that need a distributed data storage solution to provide horizontal scaling.

Hence, we have two main design choices:   
1) A distributed data warehouse with a transactional layer (e.g., AWS Redshift, Google BigQuery).   
   In the simplest form, we need a table of articles and a table for the statistics (e.g., IDF or DF).      
   Inserting a new article should update both of these tables in an atomic transaction to ensure the consistency of data.   
   If we want to define relationships between articles and other potential entities on top of which aggregation can be done, this design is a better choice.     
   ***AWS Redshift*** is a good choice for this scenario. It also has columnar storage format that can speed up the transactions.         

2) A distributed NoSQL database (e.g, Elasticsearch, Cassandra):   
   In this case, we can store the articles per request, and do the calculations on demand.  
   Since we don't have to worry about the data integrity between multiple tables, we can use a NoSQL database.    
   The advantage of a document-oriented database over a key-value database is that we still can define a schema for the articles to validate and structure their values.    
   ***Elasticsearch*** seems to be the best choice for this case. It's fast and distributed, also has many built-in features for natural language processing, making it a great match for calculating other text-related statistics.    

#### API Design
For API side, we can still use FastAPI framework because of its high performance.  
But we should use asynchronous API calls so that the TF-IDF results can be returned, 
without having to wait for storing a new article and/or updating the statistics. 

### 2.2 How to deploy the system on AWS.
First, we need to setup an Elastic Cloud cluster on AWS to host our data.    
The advantage of using Elastic Cloud is that it can manage the shards and nodes automatically.   
Our code in another instance can connect to this service via Elasticsearch REST API.     

Second, we need to deploy our API code in EC2 instance(s). 
Another serverless alternative for API deployment would be deploying the API into the Amazon API Gateway by adding a Lambda function that runs the API code.

We also need to integrate our API with an Application Load Balancer to distribute the traffic across multiple targets (e.g., EC2 instances).
