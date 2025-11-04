FROM node:18-alpine

WORKDIR /app

# Copy package files (sem o prefixo frontend/ pois o contexto já é ./frontend)
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code (copiar tudo do contexto atual)
COPY . .

# Build the application
RUN npm run build

# Install serve to run the built app
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"]