# 🧠 LifeOps AI v2

**AI-Powered Life Management Platform** — Health, Finance, Study & Productivity in one place.

## 🚀 Quick Deploy to Streamlit Cloud

### Step 1 — GitHub Setup
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/lifeops-ai.git
git push -u origin main
```

### Step 2 — Get Google Gemini API Key
1. Go to → https://aistudio.google.com/app/apikey
2. Click **"Create API Key"** (free, no credit card)
3. Copy the key

### Step 3 — Deploy on Streamlit Cloud
1. Go to → https://share.streamlit.io
2. Click **"New app"**
3. Select your GitHub repo
4. Set **Main file path**: `app.py`
5. Click **"Advanced settings"** → **"Secrets"**
6. Paste this:
```toml
GOOGLE_API_KEY = "your-gemini-api-key-here"
```
7. Click **"Deploy!"**

---

## 💻 Local Development

```bash
# 1. Clone & setup
git clone https://github.com/YOUR_USERNAME/lifeops-ai.git
cd lifeops-ai

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Create local secrets
mkdir .streamlit
# Create .streamlit/secrets.toml with your API key

# 5. Run
streamlit run app.py
```

## 🏗 Project Structure

```
lifeops-ai/
├── app.py              ← Main application (UI + routing)
├── database.py         ← SQLite database layer
├── crew_setup.py       ← AI analysis engine (Gemini)
├── agents.py           ← CrewAI agent definitions
├── tasks.py            ← CrewAI task definitions
├── requirements.txt    ← Python dependencies
├── .gitignore          ← Excludes secrets & DB from git
└── .streamlit/
    ├── config.toml     ← Streamlit theme config
    └── secrets.toml    ← API keys (LOCAL ONLY, not in git)
```

## ⚠️ Important Notes

- **NEVER** commit `.streamlit/secrets.toml` to GitHub (it's in .gitignore)
- The SQLite database (`*.db`) is also gitignored — on Streamlit Cloud, data resets on redeploy
- For persistent production data, use PostgreSQL (Supabase free tier works well)

## ✨ Features

- 🤖 **AI Analysis** — Gemini-powered health, finance, study recommendations
- 💊 **Health Vault** — Medicine tracker, daily health logs, trend charts
- 💰 **Finance Hub** — Bill tracking, budget planner, savings projections
- 📚 **Study Center** — Pomodoro timer, session history, focus analytics
- ⚡ **Productivity** — Task manager with priorities, smart notes
- 👤 **Profile** — Account settings, password change, activity analytics
- 🔒 **Multi-user** — Secure auth with hashed passwords

## 📦 Python Version
Requires Python **3.9+**. Tested with 3.11.
