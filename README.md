# MadURL Shortener

MadURL Shortener is a full-stack URL shortener with additional features like bulk shortening, image-to-PDF conversion, and URL metadata preview.

## Features

- **URL Shortening**: Convert long URLs into short, shareable links.
- **Bulk URL Shortening**: Upload a CSV file and generate shortened links for multiple URLs at once.
- **Image to PDF Converter**: Upload images and get a downloadable PDF.
- **URL Metadata Preview**: Fetch title, description, and thumbnail for a given URL before shortening.
- **FastAPI Backend**: Built with Python and FastAPI.
- **Frontend with Nginx**: A static site served using Nginx.

## Project Structure

```
/your-project
│── /backend
│   ├── Dockerfile        # Backend Dockerfile (FastAPI)
│   ├── main.py           # FastAPI application
│   ├── requirements.txt  # Dependencies
│
│── /frontend
│   ├── Dockerfile        # Frontend Dockerfile (Nginx)
│   ├── index.html        # Main page
│   ├── style.css         # Styling
│   ├── script.js         # JavaScript functionality
│
│── docker-compose.yml    # Docker Compose file to run backend and frontend
```

## Setup & Deployment

### **1️⃣ Run with Docker Compose**
```sh
docker-compose up --build -d
```
This will start both **FastAPI (backend)** and **Nginx (frontend)** services.

### **2️⃣ Run Backend Manually**
```sh
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### **3️⃣ Run Frontend Manually**
```sh
cd frontend
npx http-server -p 3000
```

## Environment Variables
For backend configuration, you may need to set environment variables in `.env` file.

## Domain Configuration
The frontend is configured to serve on **`https://urlshort.themadhvi.com/`**.
Ensure your domain is properly pointed to your server and Nginx is configured to serve requests.

## Contributing
Feel free to open issues and submit pull requests.

