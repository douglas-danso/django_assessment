# django_assessment
# Social Media Application

Welcome to the Social Media Application project! This project is an implementation of a social media platform that allows users to share text, images, and videos, interact with each other's content, join groups, and more.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Setting up Celery and RabbitMQ](#setting-up-celery-and-rabbitmq)
- [API Documentation](#api-documentation)


## Features

- User authentication and authorization using JWT tokens.
- Create, edit, and delete user profiles.
- Share posts with text, images, and videos.
- Like and comment on posts.
- Join and leave groups.
- Search for users, posts, and groups.
<!-- - Personalized content recommendations. -->
- Privacy settings for posts and profiles.
- Follow and unfollow system.
- Trending Posts



## Prerequisites

Before you start setting up Celery with RabbitMQ, make sure you have the following prerequisites:

1. Python 3.x installed on your system.
2. A running instance of RabbitMQ message broker. You can download and install RabbitMQ from its official website: https://www.rabbitmq.com/

## Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/douglas-danso/django_assessment.git
   change the django_assessment directory by running cd django_assessment in terminal
## Setting up Environment
create and activate your virtual environment by running the following commands in your terminal
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

install all project dependencies by running pip install -r requrirements.txt
Create a .env file in the root directory of your project and add the following configurations:

SECRET_KEY=your_secret_key
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port

DJANGO_ENVIRONMENT=development
EMAIL_HOST=your_email_host
EMAIL_PORT=your_email_port
EMAIL_HOST_USER=your_email_host_user
EMAIL_HOST_PASSWORD=your_email_host_password
DJANGO_SETTINGS_MODULE=django_assessment.settings

cloud_name=your_cloud_name
api_key=your_api_key
api_secret=your_api_secret
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

ALGORITHM=HS256
SECRET=your_secret



## Setting up Celery and RabbitMQ

This project uses Celery for handling background tasks such as sending notifications, processing uploads, and more. The Celery tasks are executed asynchronously using a message broker. In this project, we use RabbitMQ as the message broker.

1. Install RabbitMQ on your system. You can follow the official installation guide for your platform: [RabbitMQ Installation Guide](https://www.rabbitmq.com/download.html)

2. Configure Celery in your project's settings (`settings.py`) based on your .env variables

### database setup
There are two options here with regards to database. You can either use django's dbsqlite or postgresql
1. To use dbsqlite, set DJANGO_ENVIRONMENT in your .env to development
2. To use postgresql, you can comment the DJANGO_ENVIRONMENT in your .env and set the values for DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT with your postgres variables .

## getting-started
1. To get get started run python manage.py migrate to create your tables in database
2. Run python manage.py runserver to start the server
3. open another terminal and run celery -A django_assessment worker -l info --pool=solo to start the celery server

## API Documentation
below is the link to api documentation in postman
https://documenter.getpostman.com/view/26879414/2s9Y5YT3Cs