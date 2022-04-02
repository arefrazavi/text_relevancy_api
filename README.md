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

One could store IDFs too, but since we have to calculate the IDF for the requested terms not available in the corpus anyway,    
it wouldn't make a difference in terms of performance.   

I stored IDFs on a local directory as our data lake for development.   
In production, they should be stored in a cloud data lake (e.g. S3), or a data warehouse.
A data warehouse (e.g., AWS redshift) offers a better performance usually.

### Dynamic Calculation
In this approach, all the calculations (i.e., TF-IDFs, TFs, and DFs) are done per request by performing searches 
in a fast NoSQL document-oriented database called Elasticsearch.    

This is a much better solution when the database of documents grows constantly.     

### 1.2 How to run the API
The API can be accessible by running the following script which setups the application in a dockerized environment.     
```shell
# Docker and Docker-compose is required to be installed before running the script.
sh setup_api.sh
```     

After the setup, the API endpoint should be accessible at: http://127.0.0.1:8000/   
FastAPI also has a nice UI for testing which is accessible at: http://127.0.0.1:8000/docs   

### 1.2 How to test the API
At first, I did some unit testings to verify the functionality of important statistics and dynamic services.    
Then, I tested the `tf-idf` API call for both static (dynamic=false) and dynamic calculation.    
Tests were first done on a small sample of articles in the corpus to make the debugging faster.

I also wrote a few API tests to verify the result for both dynamic and static calculations.
You can run the following commands to run the tests:
```shell
# Go to the API docker container. 
docker exec -it $(docker ps -aqf "name=text_relevancy_api_web") /bin/bash

# Run the tests
pytest
```

***Important Note***:     
The results for TF-IDFs in dynamic and static calculation could be different.   
This is because different algorithms and libraries were used to tokenize and clean the terms.
For example, in static calculation, lemmatization by spaCy has been used,
but in dynamic calculation, [KStem-based stemming](https://ciir.cs.umass.edu/pubfiles/ir-35.pdf) has been used.

## Section 2

### 2.1 How to design a system to update statistics per request.
- Database Design
First, we have to store/update the page URL and content per request, otherwise the statistics will not be accurate (e.g. duplicate article) and can not be tracked.     
This leads to a constantly growing dataset that need a distributed data storage to provide horizontal scaling.

Hence, we have two main design choices:   
1) A distributed data warehouse with a transactional layer (e.g., AWS Redshift, Google BigQuery).   
In the simplest form, we need a table of articles and a table for the statistics (e.g., IDF or DF). 
Inserting a new article should update both of these tables in an atomic transaction to ensure the consistency of data.  

This design is a better choice, if we want to define some solid relations between articles and other potential entities on top of which aggregation can be done.     

***AWS Redshift*** is distributed data warehouse that is a good choice for this scenario.       
It also has columnar storage format can speed up the transactions.      

2) A distributed document-oriented database (e.g, Elasticsearch):   
In this case, we can store the articles per request, and do the calculations on demand.     
Since we don't have to worry about the constituency of data between multiple tables, we can use a NoSQL database.       
The advantage of a document-oriented database over a key-value database is that we still can define a schema for the articles 
to validate and structure their values.


***Elasticsearch*** is the best choice for this case.   
It's fast and distributed. It also has many built-in features for natural language processing, 
making it a great match for calculating other text-related statistics.

- API Design
For API side, we can still use FastAPI framework because of its high performance.  
But we should use asynchronous API calls so that the TF-IDF results can be returned, 
without having to wait for storing new article and/or updating the statistics. 

### 2.1 How to deploy the system on AWS.
First, we need to setup an Elastic Cloud cluster on AWS to host our data.    
The advantage of Elastic Cloud is that it can manage the shards and nodes easily.   
Our code in another instance can connect to this service via Elasticsearch REST API.     

Second, we need to deploy our API code in EC2 instance(s). 
Another serverless alternative for API deployment would be deploying the API into the Amazon API Gateway by adding a Lambda function that runs the API code.

We also need to integrate our API with an Application Load Balancer to distribute the traffic across multiple targets (e.g., EC2 instances).


