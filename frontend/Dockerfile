# Stage 1: Build React static assets
FROM node:22-alpine AS builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve static files with unprivileged Nginx
FROM nginx:1.27-alpine AS runtime

# Remove default nginx configs and html
RUN rm -rf /etc/nginx/conf.d /usr/share/nginx/html/*

# Copy custom unprivileged nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy compiled SPA bundle from builder stage
COPY --from=builder /build/dist /usr/share/nginx/html

# Grant ownership for non-root execution
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx && \
    touch /tmp/nginx.pid && \
    chown nginx:nginx /tmp/nginx.pid

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
