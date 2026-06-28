FROM python:3.14-slim
WORKDIR /app

# Install git, needed for some python packages
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements/requirements.txt requirements/requirements.txt
RUN pip install --no-cache-dir -r requirements/requirements.txt

# Download binaries
COPY download_binaries.py .
RUN pip install requests
RUN python download_binaries.py

# Copy the jimmy module
COPY jimmy ./jimmy

# Install jimmy
COPY pyproject.toml .
COPY readme.md .
RUN pip install --no-cache-dir .

# Create a default output directory
RUN mkdir -p /data/output

# Set the entrypoint
ENTRYPOINT ["jimmy"]
