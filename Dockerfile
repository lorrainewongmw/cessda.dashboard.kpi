FROM python:3.11-slim AS builder

# Install Quarto
RUN apt-get update && apt-get install -y curl && \
    curl -LO https://github.com/quarto-dev/quarto-cli/releases/download/v1.6.42/quarto-1.6.42-linux-amd64.deb && \
    dpkg -i quarto-1.6.42-linux-amd64.deb && \
    rm quarto-1.6.42-linux-amd64.deb && \
    apt-get clean

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Register the Jupyter kernel as 'sp-analysis'
RUN python -m ipykernel install --name sp-analysis --display-name "sp-analysis"

# Render the dashboard
RUN quarto render dashboard.qmd

# Serve with Nginx
FROM nginx:alpine
COPY --from=builder /app/dashboard.html /usr/share/nginx/html/index.html
COPY --from=builder /app/dashboard_files/ /usr/share/nginx/html/dashboard_files/
EXPOSE 80
