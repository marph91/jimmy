## first stage - build dependencies
FROM python:3.14-alpine AS builder
WORKDIR /app

# Install git, needed for some python packages
RUN apk add --no-cache git

RUN python -m venv /opt/venv
# enable venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements/requirements.txt /jimmy/requirements/requirements.txt
RUN pip install --no-cache-dir -r /jimmy/requirements/requirements.txt

# Download binaries
COPY download_binaries.py /jimmy
RUN pip install requests --no-cache-dir && python /jimmy/download_binaries.py

# Copy the jimmy module
COPY jimmy /jimmy/jimmy

# Install jimmy
COPY pyproject.toml readme.md /jimmy
RUN pip install --no-cache-dir -e /jimmy

## second stage - only necessary files
FROM python:3.14-alpine AS runner
# enable venv
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /jimmy/jimmy /jimmy/jimmy
COPY --from=builder /jimmy/bin /jimmy/bin

# better readable output, but not too much, since the TUI seems to be fixed to this width
ENV COLUMNS=160

# Set the entrypoint
ENTRYPOINT ["python", "/jimmy/jimmy/jimmy_cli.py"]
