# Railway Deployment

## Files used by Railway

- `railway.json`: start command and deployment settings.
- `requirements.txt`: Python dependencies.
- `.python-version`: Python version for the deployment image.
- `.streamlit/config.toml`: Streamlit runtime config.
- `.env.example`: variables to copy into Railway.

## Railway variables

In Railway, add these variables in the service environment:

```env
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
```

Do not upload `.env` to GitHub. Use Railway Variables instead.

## Start command

Railway uses this command from `railway.json`:

```bash
streamlit run app/app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

## Deploy with Railway CLI

```bash
railway login
railway link
railway up
```

After deployment, create or open the Railway public domain from the service Networking settings.

## Local check before deploy

```bash
streamlit run app/app.py
```
