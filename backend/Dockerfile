# Built from the repository root, so it can also compile the React app.
#   docker compose -f backend/docker-compose.yml up --build
# (context: ..  /  dockerfile: backend/Dockerfile)

FROM node:22-alpine AS frontend
WORKDIR /app/notes-app
COPY notes-app/package.json notes-app/package-lock.json ./
RUN npm ci
COPY notes-app/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend /app/notes-app/dist ./static
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "app:app"]
