FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Command will be overridden by docker-compose
CMD ["yarn", "dev"]
