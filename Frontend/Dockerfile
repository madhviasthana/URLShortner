# Frontend Dockerfile
FROM nginx:alpine

WORKDIR /usr/share/nginx/html

COPY frontend/ .

CMD ["nginx", "-g", "daemon off;"]

EXPOSE 80
