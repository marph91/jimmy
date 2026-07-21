
```
docker build -t marph91/jimmy .

# Mount your input and output directories
docker run -v /path/to/your/notes:/data/input -v /path/to/output:/data/output jimmy jimmy cli --format joplin /data/input/your-notes.jex --output-folder /data/output

# TUI
docker run -it jimmy tui

# CLI
docker run jimmy cli

docker run \
    -v ./test/data/test_data/colornote/test_1_frontmatter/:/data/input \
    -v ./tmp/output/:/data/output \
    --user $(id -u):$(id -g) \
    jimmy cli --format colornote /data/input/colornote-20241014.backup --password 1234 --output-folder /data/output --stdout-log-level DEBUG


docker push YOUR_DOCKER_USERNAME/concepts-build-image-demo
```
