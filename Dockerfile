# Dockerfile

# Pull the Python Docker image
FROM python:3.9

# Set work directory
WORKDIR /code

# Set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/code/app"

# Install dependencies
COPY kaggle.json /root/.kaggle/kaggle.json
COPY ./requirements.txt /code/requirements.txt
RUN pip install -U pip setuptools wheel
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN python -m spacy download en_core_web_sm
# RUN python -m nltk.downloader popular

# Copy project
COPY ./app /code/app
