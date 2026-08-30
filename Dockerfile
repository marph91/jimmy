## first stage - build dependencies
FROM python:3.14-alpine AS builder
WORKDIR /app

# Install git, needed for some python packages
# Install binutils and upx for reducing the size of the pandoc binary
RUN apk add --no-cache git binutils upx

RUN python -m venv /opt/venv
# enable venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements/requirements.txt /jimmy/requirements/requirements.txt
RUN pip install --no-cache-dir -r /jimmy/requirements/requirements.txt

# Download binaries
COPY download_binaries.py /jimmy
RUN pip install requests --no-cache-dir && python /jimmy/download_binaries.py
# stripping doesn't have any effect - done in pandoc build already
# RUN strip /jimmy/bin/pandoc
# Don't use upx. It can reduce the binary size, but it slows down the execution (~60 s for a smoke test).
# It seems like it is unpacked at every single call.
# RUN upx --best --lzma /jimmy/bin/pandoc

# Copy the jimmy module
COPY jimmy /jimmy/jimmy

# Install jimmy
COPY pyproject.toml readme.md /jimmy
RUN pip install --no-cache-dir -e /jimmy

# remove unnecessary files from the venv
RUN find /opt/venv -name "*.so" -exec strip --strip-unneeded {}; \
    find /opt/venv -type d -name "__pycache__" -prune -exec rm -rf {} +; \
    find /opt/venv -type d -name "tests" -prune -exec rm -rf {} +
RUN pip uninstall -y pip setuptools wheel

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
