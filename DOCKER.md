# Running paprika-mcp in Docker

A prebuilt image is published to the GitHub Container Registry:

```
ghcr.io/glitchcrab/paprika-mcp:latest
```

The image exposes the `paprika-mcp` stdio server as its entrypoint and runs as
a non-root user (`app`, UID 1000).

## Pull

```bash
docker pull ghcr.io/glitchcrab/paprika-mcp:latest
```

## Run

The server speaks MCP over stdio, so it must be run with stdin attached
(`-i`) and without a TTY. Credentials are supplied via environment variables:

```bash
docker run -i --rm \
  -e PAPRIKA_EMAIL="your@email.com" \
  -e PAPRIKA_PASSWORD="yourpassword" \
  ghcr.io/glitchcrab/paprika-mcp:latest
```

### Using a config file instead of env vars

Mount a `config.json` (see the README for its format) to
`/home/app/.paprika-mcp`:

```bash
docker run -i --rm \
  -v "$HOME/.paprika-mcp:/home/app/.paprika-mcp" \
  ghcr.io/glitchcrab/paprika-mcp:latest
```

The mount is read-write because the server caches recipe data under
`.paprika-mcp/cache`. The host directory must be readable and writable by
UID 1000 (the container's `app` user). An optional `prompt.md` in that same
directory is loaded automatically.

## MCP client configuration

Point your MCP client at `docker` instead of a local binary:

```json
{
  "mcpServers": {
    "paprika": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
        "-e", "PAPRIKA_EMAIL",
        "-e", "PAPRIKA_PASSWORD",
        "ghcr.io/glitchcrab/paprika-mcp:latest"],
      "env": {
        "PAPRIKA_EMAIL": "your@email.com",
        "PAPRIKA_PASSWORD": "yourpassword"
      }
    }
  }
}
```

The client spawns a fresh container per session and tears it down on exit
(`--rm`).

## Building locally

To build the image yourself instead of pulling:

```bash
docker build -t paprika-mcp .
```

Then substitute `paprika-mcp` for the `ghcr.io/...` reference in any of the
commands above.
