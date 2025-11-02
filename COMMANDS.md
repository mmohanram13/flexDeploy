# FlexDeploy - Quick Command Reference

## 🚀 First Time Setup

```bash
# 1. Install all dependencies (Python + npm)
./install.sh

# 2. Configure AWS credentials
nano ~/.aws/credentials

# 3. Test AWS Bedrock connection
python test_bedrock_agents.py

# 4. Start the application
./run_app.sh
```

## 🎮 Running the Application

### Start Everything
```bash
./run_app.sh
```
- Starts backend on http://localhost:8000
- Starts frontend on http://localhost:5173
- Press Ctrl+C to stop both

### Start Services Separately
```bash
# Backend only
python -m server.main

# Frontend only (in another terminal)
cd ui && npm run dev
```

## 🧪 Testing

```bash
# Test AI agents
python test_bedrock_agents.py

# Test API endpoints
curl http://localhost:8000/api/devices

# Check database
sqlite3 server/flexdeploy.db "SELECT COUNT(*) FROM devices;"
```

## ⚙️ Configuration

```bash
# Setup configuration
./setup_config.sh

# View current configuration
python -c "from server.config import get_config; get_config().print_config()"

# Edit app settings
nano config.ini

# Edit AWS credentials
nano ~/.aws/credentials
```

## 📦 Package Management

```bash
# Install Python packages
uv pip install -e .
# or
pip install -e .

# Install npm packages
cd ui && npm install

# Update packages
uv pip install --upgrade -e .
cd ui && npm update
```

## 🔧 Maintenance

```bash
# View server logs
tail -f server.log

# View UI logs
tail -f ui.log

# Check running processes
ps aux | grep python
ps aux | grep node

# Clear logs
rm server.log ui.log

# Restart services
# Press Ctrl+C to stop, then run:
./run_app.sh
```

## 🐛 Troubleshooting

```bash
# Check AWS credentials
aws sts get-caller-identity --profile <profile_id>

# Test AWS Bedrock access
aws bedrock list-foundation-models --region us-east-1 --profile <profile_id>

# Verify config files
ls -la config.ini ~/.aws/credentials

# Check Python version
python3 --version  # Should be 3.11+

# Check Node version
node --version  # Should be 18+

# Reinstall packages
uv pip install --force-reinstall -e .
cd ui && rm -rf node_modules && npm install
```

## 🌐 URLs

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## 📝 Common Tasks

### Create a Deployment
```bash
curl -X POST http://localhost:8000/api/deployments \
  -H "Content-Type: application/json" \
  -d '{"deploymentName": "Test Deploy", "status": "Not Started"}'
```

### Run AI Categorization
```bash
curl -X POST http://localhost:8000/api/ai/categorize-devices \
  -H "Content-Type: application/json" \
  -d '{"deviceIds": null}'  # null = all devices
```

### Analyze Deployment Failure
```bash
curl -X POST http://localhost:8000/api/ai/analyze-failure \
  -H "Content-Type: application/json" \
  -d '{"deploymentId": "DEP-001", "ringName": "Ring 1 - Low Risk Devices"}'
```

### Parse Natural Language Gating
```bash
curl -X POST http://localhost:8000/api/ai/gating-factors \
  -H "Content-Type: application/json" \
  -d '{"naturalLanguageInput": "Deploy to stable devices only"}'
```

## 📚 Documentation

All documentation is consolidated in **README.md**

Key sections:
- Architecture
- Installation
- Configuration
- AI Agents
- API Documentation
- Troubleshooting

## 🔑 File Locations

```
config.ini                    # App configuration
~/.aws/credentials           # AWS credentials
server/flexdeploy.db         # Database
server.log                   # Backend logs
ui.log                       # Frontend logs
```

## ⚡ Quick Fixes

**Server won't start:**
```bash
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
python -m server.main
```

**UI won't start:**
```bash
lsof -ti:5173 | xargs kill -9  # Kill process on port 5173
cd ui && npm run dev
```

**Database locked:**
```bash
fuser server/flexdeploy.db  # Find process using DB
# Kill the process, then restart
```

**AWS credentials expired:**
```bash
aws sso login
# Or get new credentials from SSO portal
```

## 📞 Getting Help

1. Check **README.md** for comprehensive documentation
2. Review logs: `tail -f server.log ui.log`
3. Test components: `python test_bedrock_agents.py`
4. Verify setup: `./install.sh` (safe to re-run)

---

**For full documentation, see README.md**
