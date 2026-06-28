FROM python:3.14-alpine
WORKDIR /app

# Install git, needed for some python packages
RUN apk add --no-cache git

# Install dependencies
COPY requirements/requirements.txt requirements/requirements.txt
RUN pip install --no-cache-dir -r requirements/requirements.txt

# Download binaries
COPY download_binaries.py .
RUN pip install requests --no-cache-dir && python download_binaries.py

# Copy the jimmy module
COPY jimmy ./jimmy

# Install jimmy
COPY pyproject.toml readme.md  .
RUN pip install --no-cache-dir -e .

# better readable output
ENV COLUMNS=300

# Set the entrypoint
ENTRYPOINT ["python", "./jimmy/jimmy_cli.py"]
