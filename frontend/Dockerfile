FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# API URL is baked into the static build (Vite reads it at build time)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run expects the container to listen on $PORT (default 8080)
CMD ["sh", "-c", "sed -i \"s/listen 8080/listen ${PORT:-8080}/\" /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
