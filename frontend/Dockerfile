# Use a lightweight Node.js image
FROM node:18-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and install dependencies
# This layer is cached to speed up builds
COPY package.json .
RUN npm install

# Copy the rest of the application code
COPY . .

# Vite's default port
EXPOSE 5173

# The command to start the development server
CMD ["npm", "run", "dev"]
