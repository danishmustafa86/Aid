# AidLinkAI - Vercel Deployment Guide

This guide explains how to deploy the AidLinkAI emergency response system to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Set up required environment variables

## Required Environment Variables

Set these in your Vercel project dashboard under Settings > Environment Variables:

### Database Configuration
```
POSTGRESQL_URL=postgresql://username:password@host:port/database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### API Keys
```
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### JWT Configuration
```
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
```

### Email Configuration
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=your_email@gmail.com
```

### Data Files
```
SOURCE_FILENAME_MEDICAL=medical_data.txt
SOURCE_FILENAME_POLICE=police_data.txt
SOURCE_FILENAME_ELECTRICITY=electricity_data.txt
SOURCE_FILENAME_FIRE=fire_data.txt
```

## Deployment Steps

### Method 1: Deploy from GitHub

1. **Connect Repository**:
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Project**:
   - Framework Preset: `Other`
   - Root Directory: `./` (leave as default)
   - Build Command: Leave empty (Vercel will auto-detect)
   - Output Directory: Leave empty

3. **Set Environment Variables**:
   - Add all required environment variables listed above
   - Make sure to set them for Production, Preview, and Development

4. **Deploy**:
   - Click "Deploy"
   - Wait for deployment to complete

### Method 2: Deploy with Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Set Environment Variables**:
   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add POSTGRESQL_URL
   # ... add all other environment variables
   ```

5. **Redeploy**:
   ```bash
   vercel --prod
   ```

## Important Notes

### Vercel Limitations
- **Function Timeout**: 30 seconds maximum (configurable up to 5 minutes for Pro plans)
- **Memory**: 1024MB maximum
- **File System**: Read-only (except `/tmp` directory)
- **Cold Starts**: Functions may have cold start delays

### Adaptations Made for Vercel
1. **Static Files**: Audio file serving is disabled in Vercel environment
2. **File Uploads**: Audio files are processed in memory and cleaned up
3. **Database**: Uses external PostgreSQL and MongoDB (not local files)
4. **Logging**: Reduced logging to avoid hitting limits

### API Endpoints
After deployment, your API will be available at:
```
https://your-project-name.vercel.app/api/triage/chat
https://your-project-name.vercel.app/api/medical-emergency/chat
https://your-project-name.vercel.app/api/police-emergency/chat
https://your-project-name.vercel.app/api/electricity-emergency/chat
https://your-project-name.vercel.app/api/fire-emergency/chat
https://your-project-name.vercel.app/authority/medical/emergencies
https://your-project-name.vercel.app/notifications/user/{user_id}
```

### Health Check
Test your deployment:
```bash
curl https://your-project-name.vercel.app/health
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Database Connection**: Verify your database URLs are correct
3. **Environment Variables**: Double-check all required variables are set
4. **Function Timeout**: Consider breaking long operations into smaller chunks
5. **Memory Issues**: Monitor function memory usage in Vercel dashboard

### Debugging
- Check Vercel function logs in the dashboard
- Use `print()` statements for debugging (they appear in logs)
- Test locally with `vercel dev` before deploying

## Production Considerations

1. **Database**: Use production-grade databases (not free tiers for production)
2. **API Keys**: Use strong, unique API keys
3. **Rate Limiting**: Consider implementing rate limiting
4. **Monitoring**: Set up monitoring and alerting
5. **Backup**: Regular database backups
6. **Security**: Review security settings and access controls

## Support

For Vercel-specific issues:
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Community](https://github.com/vercel/vercel/discussions)

For AidLinkAI-specific issues:
- Check the main README.md
- Review the project documentation
