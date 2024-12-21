FROM node:18-alpine

WORKDIR /app

# Install dependencies required for development
RUN apk add --no-cache netcat-openbsd

# Copying package files
COPY frontend/package*.json ./

# Installing dependencies
RUN npm install

# Expose port
EXPOSE 3000

# Running the app in development mode with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 