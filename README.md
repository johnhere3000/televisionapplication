# Television Application
> Returns HLS stream links for any site using the very specific distribution structure that this is written for.

## Usage
### Docker
```
version: "3"
services:
  televisionapplication:
    image: placeholder
    container_name: televisionapplication
    restart: 'unless-stopped'
    ports:
      - "8000:8000"
    volumes:
      - /data/televisionapplication:/data
```
### Linux