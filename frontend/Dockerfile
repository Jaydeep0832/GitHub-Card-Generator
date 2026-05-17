FROM nginx:alpine

# Default backend URL (can be overridden)
ENV BACKEND_URL=http://localhost:8080

# Copy the index.html into the nginx directory
COPY index.html /usr/share/nginx/html/index.html

# Use envsubst to replace localhost:8080 with the environment variable at runtime
# We create a template and use a script to replace and start nginx
CMD ["/bin/sh", "-c", "sed -i 's|http://localhost:8080|'\"$BACKEND_URL\"'|g' /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]

# Expose port 80
EXPOSE 80
