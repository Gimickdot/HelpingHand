# ASL Learning App - Free Render Deployment Guide (2026)

A step-by-step guide to deploy the ASL Sign Language Recognition Django app on Render's free tier.

---

## Prerequisites

- [GitHub](https://github.com) account
- [Render](https://render.com) account (free tier available)
- Your project pushed to a GitHub repository

---

## Step 1: Prepare Your Repository

### 1.1 Add Required Files to Your Project

Ensure these files are in your project root:

```
ASL-main/
├── render.yaml          # Render configuration
├── build.sh             # Build script
├── requirements.txt     # Python dependencies
├── manage.py
├── asl_project/         # Django project
├── asl_recognition/     # Django app
└── ...
```

### 1.2 Update requirements.txt

Add these deployment dependencies to your `requirements.txt`:

```txt
Django>=5.0,<6.0
gunicorn>=21.0.0
whitenoise>=6.6.0
dj-database-url>=2.1.0
psycopg2-binary>=2.9.9
mediapipe>=0.10.0
numpy>=1.24.0
opencv-python>=4.8.0
scikit-learn>=1.3.0
scipy>=1.11.0
joblib>=1.3.0
Pillow>=10.0.0
requests>=2.31.0
boto3>=1.34.0
django-storages>=1.14.0
django-allauth>=0.57.0
django-cors-headers>=4.3.0
```

---

## Step 2: Configure Render.yaml

The `render.yaml` file has been created with the following services:

- **Web Service**: Django application with Gunicorn
- **PostgreSQL Database**: Free tier managed database
- **Static Files**: CDN-optimized static file serving

Key configurations:
- Python 3.11 runtime
- Auto-deploys on git push
- Health check endpoint at `/health/`
- Free PostgreSQL database included

---

## Step 3: Push to GitHub

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/asl-learning-app.git

# Push
git push -u origin main
```

---

## Step 4: Deploy on Render

### 4.1 Create Blueprint Instance

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"Blueprints"** in the left sidebar
3. Click **"New Blueprint Instance"**
4. Connect your GitHub repository
5. Select the repository with your ASL app
6. Click **"Approve"** to create resources

### 4.2 What Render Creates Automatically

- **Web Service**: `asl-learning-app` (Python 3.11)
- **PostgreSQL Database**: `asl-db` (Free tier)
- **Static Files**: CDN-enabled static hosting
- **Environment Variables**: Auto-generated SECRET_KEY and admin password

---

## Step 5: Configure Environment Variables

After the initial deployment, update these environment variables in the Render Dashboard:

### Required: AWS S3 (for static/media files)

| Key | Value | Description |
|-----|-------|-------------|
| `AWS_ACCESS_KEY_ID` | your_key | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | your_secret | AWS IAM secret key |
| `AWS_STORAGE_BUCKET_NAME` | your_bucket | S3 bucket name |
| `AWS_S3_REGION_NAME` | ap-southeast-1 | Bucket region |

### Required: Email SMTP (optional but recommended)

| Key | Value | Description |
|-----|-------|-------------|
| `EMAIL_HOST_USER` | your_email@gmail.com | SMTP email |
| `EMAIL_HOST_PASSWORD` | your_app_password | Gmail app password |

### Optional: Custom Admin Credentials

| Key | Value | Description |
|-----|-------|-------------|
| `DJANGO_SUPERUSER_USERNAME` | admin | Admin username |
| `DJANGO_SUPERUSER_EMAIL` | admin@yourdomain.com | Admin email |
| `DJANGO_SUPERUSER_PASSWORD` | your_secure_password | Admin password |

---

## Step 6: Database Migration (First Deploy)

### Option A: Auto-migration (Recommended)
The `build.sh` script automatically runs migrations on each deploy.

### Option B: Manual Migration via Shell

1. In Render Dashboard, go to your Web Service
2. Click **"Shell"** tab
3. Run:
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Step 7: Verify Deployment

### 7.1 Check Health Endpoint

Visit: `https://your-app-name.onrender.com/health/`

Should return:
```json
{
  "status": "healthy",
  "service": "asl-learning-app"
}
```

### 7.2 Access Admin Panel

- URL: `https://your-app-name.onrender.com/admin/`
- Username: `admin` (or your custom value)
- Password: Check Render environment variables or your custom setting

### 7.3 Test Main Application

- Home: `https://your-app-name.onrender.com/`
- Dashboard: `https://your-app-name.onrender.com/dashboard/`
- Game: `https://your-app-name.onrender.com/game/`

---

## Step 8: Post-Deployment Configuration

### 8.1 Update ALLOWED_HOSTS (Optional but Recommended)

Add your Render domain to `ALLOWED_HOSTS` in environment variables:

```
ALLOWED_HOSTS=your-app-name.onrender.com,localhost,127.0.0.1
```

### 8.2 Set DEBUG to False

In Render Dashboard environment variables:
```
DEBUG=False
```

This enables:
- AWS S3 for static files
- Production security settings

---

## Step 9: SSL/HTTPS (Auto-Enabled)

Render automatically provides:
- Free SSL certificate
- HTTPS redirection
- Secure headers

No manual configuration needed!

---

## Troubleshooting

### Issue: Build fails with "Module not found"

**Solution**: Ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### Issue: Static files not loading

**Solution**: 
1. Check `DEBUG=False` is set
2. Verify AWS S3 credentials are correct
3. Ensure S3 bucket has proper CORS configuration

### Issue: Database connection failed

**Solution**:
1. Check `DATABASE_URL` is set correctly
2. Verify Render PostgreSQL instance is "Available"
3. Restart the web service

### Issue: ASL model not loading

**Solution**:
The model files (`asl_model.pkl`, `asl_scaler.pkl`) should be in your repository. Verify:
```bash
git lfs track "*.pkl"
git add .gitattributes
git push
```

---

## Free Tier Limits (2026)

| Resource | Free Tier Limit |
|----------|-----------------|
| Web Service | 512 MB RAM, sleeps after 15 min idle |
| PostgreSQL | 1 GB storage, 10 connections |
| Bandwidth | 100 GB/month |
| Build Minutes | 500 min/month |
| Static Sites | 100 GB/month bandwidth |

---

## Useful Render Dashboard URLs

- **Dashboard**: https://dashboard.render.com
- **Web Service Logs**: https://dashboard.render.com/web/your-service-id/logs
- **Database**: https://dashboard.render.com/databases/your-db-id
- **Shell Access**: Click "Shell" tab in your web service

---

## GitHub Actions Auto-Deploy (Optional)

Add `.github/workflows/render-deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Render
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
```

---

## Need Help?

- [Render Documentation](https://render.com/docs)
- [Django on Render](https://render.com/docs/deploy-django)
- [Render Discord Community](https://render.com/discord)

---

**Last Updated**: April 2026
