#bash
# 0. (Optional) Setup virtually locally.
# python -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt

# 1. Download the corpus from Kaggle into our local data lake.
# The Kaggle credentials must be available in .kaggle/kaggle.json.
kaggle datasets download -d snapcrack/all-the-news -p data_lake/corpus/

# 2. Install docker-compose on Linux.
# sudo apt-get install docker-compose

# 3. Initialize env file
cp .env.template .env

# 4. Setup the API by creating the environment and installing the requirements.
docker-compose up --build -d

# 5. Go to the API docker container. You don't necessarily have to do that if you did the step 0.
docker exec -it $(docker ps -aqf "name=text_relevancy_api_web") /bin/bash

# 6. Seed database and data lake with initial required data to use the API.
python seed_database.py