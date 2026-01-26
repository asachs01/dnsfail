---
title: Web Interface
description: Access and control the DNS Incident Timer from a web browser.
---

# Web Interface

The DNS Incident Timer includes a web interface for remote monitoring and control.

## Features

- **Live timer display** - Same time format as the LED matrix
- **Remote reset** - Trigger the counter reset from any device
- **Audio playback** - Reset plays the same audio as the physical button
- **Mobile-friendly** - Responsive design works on phones and tablets

## Enabling the Web Interface

The web interface is enabled by default when `web_port` is set in the configuration.

```yaml
# config.yaml
web_port: 5000  # Web interface port (0 to disable)
```

## Accessing the Interface

Once running, access the web interface at:

```
http://<pi-hostname>:5000
```

Or using the IP address:

```
http://192.168.1.100:5000
```

## Interface Overview

The web interface displays:

| Section | Description |
|---------|-------------|
| Header | "Days Since DNS Incident" |
| Timer | Years, months, days / hours, minutes, seconds |
| Reset Button | Triggers counter reset and audio |
| Status | Connection status indicator |

## Security Considerations

:::caution[No Authentication]
The web interface has **no authentication**. It's designed for local network use only.
:::

**Recommendations:**
- Only expose on trusted networks
- Use firewall rules to restrict access
- Consider a reverse proxy with authentication for external access

## Running Standalone

The web server can run independently of the main display application:

```bash
# Native installation
python web_server.py --config /etc/dnsfail/config.yaml

# With custom port
python web_server.py --port 8080

# Debug mode
python web_server.py --debug
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--config` | /usr/local/share/dnsfail/config.yaml | Config file path |
| `--host` | 0.0.0.0 | Interface to bind to |
| `--port` | (from config) | Override web port |
| `--debug` | false | Enable Flask debug mode |

## API Endpoints

The web interface exposes a simple REST API:

### GET /api/state

Returns the current timer state.

**Response:**
```json
{
  "last_reset": "2024-01-25T12:00:00.000000",
  "success": true
}
```

### POST /api/reset

Resets the counter and plays audio.

**Response:**
```json
{
  "success": true,
  "last_reset": "2024-01-25T14:30:00.000000",
  "message": "Timer reset successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Error description"
}
```

## Docker Configuration

The web interface is automatically available when using Docker with `network_mode: host`:

```yaml
# docker-compose.prod.yml
services:
  dns-counter:
    network_mode: host
    volumes:
      - ./web_server.py:/app/web_server.py
      - ./templates:/app/templates
```

With host networking, the web interface is accessible on port 5000 (or configured port).

## Customization

### Custom Templates

The web interface uses a single HTML template at `templates/index.html`. To customize:

1. Copy the template:
   ```bash
   cp templates/index.html templates/index.custom.html
   ```

2. Modify the custom template

3. Update `web_server.py` to use your template

### Styling

The interface uses CSS custom properties for theming:

```css
:root {
    --bg-primary: #0a0a0b;       /* Background */
    --accent: #ef4444;           /* Red accent */
    --text-primary: #fafafa;     /* Primary text */
    --text-secondary: rgba(250, 250, 250, 0.7);
}
```

Edit `templates/index.html` to customize colors.

## Troubleshooting

### Port Already in Use

```
OSError: [Errno 98] Address already in use
```

**Solution:** Change the port in config or stop the conflicting service:
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Use different port
web_port: 8080
```

### Connection Refused

If you can't connect to the web interface:

1. **Check the service is running:**
   ```bash
   # Native
   sudo systemctl status dns_counter

   # Docker
   docker compose -f docker-compose.prod.yml logs | grep -i web
   ```

2. **Check firewall:**
   ```bash
   sudo ufw status
   # Allow the port if needed
   sudo ufw allow 5000/tcp
   ```

3. **Verify network mode in Docker:**
   ```yaml
   network_mode: host  # Required for host port access
   ```

### Reset Works But No Audio

The web interface triggers audio on the Pi, not the browser. Verify:

1. Audio device is configured correctly
2. Docker has access to `/dev/snd`
3. Check logs for audio errors
