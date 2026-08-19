FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host expoe o servidor de dev para fora do container (por padrao o Vite
# so escuta em localhost, o que ficaria inacessivel de fora do container).
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
