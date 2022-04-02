#bash

# Initialize env file
cp .env.template .env

# Setup the API by creating the environment and installing the requirements.
docker-compose up --build

# Seed database and data lake with initial required data to use the API.
python seed_database.py