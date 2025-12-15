# Deployment Guide

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- MongoDB 6+ (or MongoDB Atlas)
- Python 3.11+
- Node.js 18+
- Nginx (for reverse proxy)
- Domain name (optional)

## Database Setup

### MongoDB

```bash
sudo apt update
sudo apt install mongodb
sudo systemctl enable --now mongod
```

## Backend Deployment

### 1. Clone Repository

```bash
cd /opt
git clone https://github.com/yourusername/dealbro.git
cd dealbro/backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Update:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=dealbro
API_HOST=127.0.0.1
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com
```

DealBro creates required indexes and seeds default sources on startup.

### 5. Create Systemd Service

Create `/etc/systemd/system/dealbro-api.service`:

```ini
[Unit]
Description=DealBro API
After=network.target mongod.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/dealbro/backend
Environment="PATH=/opt/dealbro/backend/venv/bin"
ExecStart=/opt/dealbro/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/dealbro-ingestion.service`:

```ini
[Unit]
Description=DealBro Ingestion Service
After=network.target mongod.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/dealbro/backend
Environment="PATH=/opt/dealbro/backend/venv/bin"
ExecStart=/opt/dealbro/backend/venv/bin/python -m app.ingestion.scheduler
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dealbro-api
sudo systemctl enable dealbro-ingestion
sudo systemctl start dealbro-api
sudo systemctl start dealbro-ingestion
```

### 6. Check Status

```bash
sudo systemctl status dealbro-api
sudo systemctl status dealbro-ingestion
```

View logs:

```bash
sudo journalctl -u dealbro-api -f
sudo journalctl -u dealbro-ingestion -f
```

## Frontend Deployment

### 1. Build Frontend

```bash
cd /opt/dealbro/frontend
npm install
npm run build
```

### 2. Serve with Nginx

Create `/etc/nginx/sites-available/dealbro`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /opt/dealbro/frontend/.next/standalone;
        try_files $uri $uri/ @nextjs;
    }

    location @nextjs {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/dealbro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Start Next.js Server

Create `/etc/systemd/system/dealbro-frontend.service`:

```ini
[Unit]
Description=DealBro Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/dealbro/frontend
Environment="NODE_ENV=production"
Environment="NEXT_PUBLIC_API_URL=https://yourdomain.com/api"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dealbro-frontend
sudo systemctl start dealbro-frontend
```

## SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot will automatically update Nginx config for HTTPS.

## Monitoring

### Health Checks

Add to crontab:

```bash
crontab -e
```

Add:

```
*/5 * * * * /opt/dealbro/backend/venv/bin/python /opt/dealbro/backend/scripts/health_check.py >> /var/log/dealbro/health.log 2>&1
```

### Log Rotation

Create `/etc/logrotate.d/dealbro`:

```
/var/log/dealbro/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Backup

### Database Backup

Create backup script `/opt/dealbro/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/dealbro"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

mongodump --uri="mongodb://localhost:27017" --db dealbro --archive="$BACKUP_DIR/dealbro_$DATE.archive.gz" --gzip

# Keep only last 7 days
find $BACKUP_DIR -name "dealbro_*.archive.gz" -mtime +7 -delete
```

Add to crontab:

```
0 2 * * * /opt/dealbro/scripts/backup.sh
```

## Updates

### Update Backend

```bash
cd /opt/dealbro
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart dealbro-api
sudo systemctl restart dealbro-ingestion
```

### Update Frontend

```bash
cd /opt/dealbro/frontend
npm install
npm run build
sudo systemctl restart dealbro-frontend
```

## Troubleshooting

### API Not Starting

Check logs:
```bash
sudo journalctl -u dealbro-api -n 50
```

Common issues:
- Database connection failed: Check MONGODB_URL in .env
- Port already in use: Change API_PORT
- Permission denied: Check file ownership

### Ingestion Not Working

Check logs:
```bash
sudo journalctl -u dealbro-ingestion -n 50
```

Common issues:
- Rate limited by source: Increase INGESTION_INTERVAL_MINUTES
- Connection timeout: Check network/firewall
- Parser failed: Update adapter for HTML changes

### Frontend Not Loading

Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

Check Next.js logs:
```bash
sudo journalctl -u dealbro-frontend -n 50
```

## Security

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Database

Restrict MongoDB to localhost in `/etc/mongod.conf`:

```
net:
  bindIp: 127.0.0.1
```

### API

- Use strong passwords
- Enable CORS only for your domain
- Consider adding rate limiting
- Keep dependencies updated

## Performance Tuning

### MongoDB

Ensure indexes exist for common queries. DealBro creates indexes in `backend/app/core/database.py`.

### Nginx

Add to nginx config:

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
client_max_body_size 10M;
```

### Database Indexing

Monitor slow queries:

```bash
mongosh "mongodb://localhost:27017/dealbro" --eval "db.setProfilingLevel(1, { slowms: 100 })"
```

Add indexes as needed for common queries.
