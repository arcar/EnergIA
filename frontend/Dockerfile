<<<<<<< HEAD
FROM node:24
=======
FROM node:24-alpine
>>>>>>> yassine

WORKDIR /app

COPY package*.json ./

<<<<<<< HEAD
RUN npm install
=======
RUN npm ci
>>>>>>> yassine

COPY . .

EXPOSE 4200

CMD ["npm", "start", "--", "--host", "0.0.0.0"]