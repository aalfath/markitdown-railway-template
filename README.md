# Deploy and Host MarkItDown on Railway

MarkItDown is Microsoft's Python tool for converting documents to Markdown for LLMs and text pipelines. It handles PDF, Word, Excel, PowerPoint, HTML, CSV, JSON, XML, EPUB, ZIP archives and images with metadata, keeping headings, lists, tables and links, so documents can be indexed, embedded or passed to a model.

## About Hosting MarkItDown

This template runs MarkItDown 0.1.8 as a small web service from a public wrapper repository. It offers a REST endpoint for file uploads or URLs, and a Model Context Protocol endpoint with a `convert_to_markdown` tool for AI agents. Every request except the health check needs a generated bearer token. Only `http:`, `https:` and `data:` URIs are accepted, so the service never reads its own files. It keeps no state and fits the Hobby plan; large PDFs and spreadsheets need more memory. Send documents over HTTPS to the Railway domain, or call it privately from other services in the same project.

## Common Use Cases

- Converting uploaded documents to Markdown before embedding them for RAG
- Giving AI agents a document conversion tool over MCP
- Turning Office files and PDFs into text inside automation workflows

## Dependencies for MarkItDown Hosting

- `aalfath/markitdown-railway-template` (Python 3.13, `markitdown[all]==0.1.8`, `mcp==2.2.0`)

### Deployment Dependencies

- [MarkItDown on GitHub](https://github.com/microsoft/markitdown)
- [MarkItDown v0.1.8 release](https://github.com/microsoft/markitdown/releases/tag/v0.1.8)
- [Wrapper repository](https://github.com/aalfath/markitdown-railway-template)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Implementation Details

| Service | Source | Networking | Storage |
| --- | --- | --- | --- |
| markitdown | `aalfath/markitdown-railway-template` | public domain on 8080; private | none |

```bash
curl -H "Authorization: Bearer $MARKITDOWN_API_TOKEN" -F file=@report.docx "https://<domain>/convert?format=text"
curl -H "Authorization: Bearer $MARKITDOWN_API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"uri":"https://example.com/paper.pdf"}' https://<domain>/convert
```

MCP clients use `https://<domain>/mcp` with the same bearer token.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MARKITDOWN_API_TOKEN` | generated | Bearer token for REST and MCP |
| `MARKITDOWN_MAX_UPLOAD_MB` | `50` | Upload size limit |
| `MARKITDOWN_ENABLE_PLUGINS` | `false` | Enable installed MarkItDown plugins |

Notes:

- Audio transcription is not included (no ffmpeg in the image).
- The JSON response contains `title` and `markdown`; add `?format=text` for raw Markdown.

This is a community-maintained deployment package and does not imply affiliation with or endorsement by the MarkItDown project or its maintainers.

## Why Deploy MarkItDown on Railway?

Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying MarkItDown on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
