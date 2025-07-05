# Multi-stage Dockerfile for frontend service
# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files for better caching
COPY package.json package-lock.json* ./

# Install dependencies with npm ci for faster, reliable builds
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Set proper permissions
RUN chown -R nextjs:nodejs /usr/share/nginx/html
RUN chown -R nextjs:nodejs /var/cache/nginx
RUN chown -R nextjs:nodejs /var/log/nginx
RUN chown -R nextjs:nodejs /etc/nginx/conf.d
RUN touch /var/run/nginx.pid
RUN chown -R nextjs:nodejs /var/run/nginx.pid

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Development stage (for docker-compose development)
FROM node:18-alpine AS development

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev dependencies)
RUN npm install

# Expose port for development server
EXPOSE 3000

# Start development server
CMD ["npm", "start"]