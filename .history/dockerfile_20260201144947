# STAGE 1: Build layer (De 'keuken')
FROM node:lts-alpine AS build-stage
WORKDIR /app
# Hier zou je normaal gesproken je dependencies installeren
# COPY package*.json ./
# RUN npm install
COPY . .

# STAGE 2: Production layer (Het 'bord' dat de klant ziet)
FROM nginx:stable-alpine AS production-stage
# Kopieer alleen de nodige bestanden uit de build-stage naar Nginx
COPY --from=build-stage /app /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]