# Chilliwack

## **Overview**
This repository contains a Flask application that requires the Microsoft ODBC Driver 18 for SQL Server and other dependencies to run. The easiest way to get started is by using Docker.

### **1. Clone the Repository**
```bash
git clone https://github.com/gnguyen2/Chilliwack.git
cd Chilliwack
```

### **2. Prepare Environment Variables**
Create a file named .env.docker in the root of the project with the environment variables needed to connect to your database and configure the app.
Important: You’ll need to contact any of the following on discord for the environment details:
- @kjx172
- @yuelex
- @gia1103
- @d00mb0i

Once you have the details, place them in the .env.docker file.

### **3. Build the Docker Image**
From within the Chilliwack directory, run:
```bash
docker build -t chilliwack-app .
```

### **4. Run the Container**
Use the image you just built to start a container:
```
docker run --env-file .env.docker -p 5000:5000 --name chilliwack-container chilliwack-app
```

Once the container is running, open your browser and go to:
```
http://127.0.0.1:5000
```
If you encounter an ODBC timeout error, re-run the container again. Sometimes it may take multiple attempts.

### **5. Running Migrations**
You can run migrations inside the container. For example, once your container is up, open a new terminal and run:

```
docker exec -it chilliwack-container flask db init
docker exec -it chilliwack-container flask db migrate -m "Initial migration"
docker exec -it chilliwack-container flask db upgrade
```
