# 🔧 Jenkins Pipeline Guide for BeatWake

Complete guide to connecting and using Jenkins CI/CD pipeline for your BeatWake project.

---

## 📋 Prerequisites

Make sure Jenkins is installed and running:

```bash
# Check if Jenkins is running
sudo systemctl status jenkins

# If not installed, run:
./install_jenkins.sh
```

---

## 🚀 Quick Start - Connect to Jenkins

### Step 1: Start Jenkins (if not running)

```bash
sudo systemctl start jenkins
```

### Step 2: Forward Port 8080

If you're in a dev container (GitHub Codespaces, VS Code Dev Containers):

1. **VS Code**: Look for the "PORTS" tab at the bottom
2. Click "Forward a Port"
3. Enter `8080`
4. Set visibility to "Public" or "Private"

**Or use CLI:**
```bash
# In VS Code, this command opens the port forwarding
# The port will be automatically detected
```

### Step 3: Access Jenkins

Open your browser and navigate to:
```
http://localhost:8080
```

Or if in Codespaces, use the forwarded URL (looks like):
```
https://username-repo-xxxxx.preview.app.github.dev
```

### Step 4: Unlock Jenkins

Get the initial admin password:
```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Copy the password and paste it into Jenkins web UI.

### Step 5: Install Plugins

1. Click "Install suggested plugins"
2. Wait for installation to complete
3. Or select these essential plugins:
   - Git plugin
   - Pipeline plugin
   - GitHub plugin
   - Blue Ocean (optional, for better UI)
   - Credentials Binding

### Step 6: Create Admin User

Fill in the form:
- Username: `admin` (or your choice)
- Password: (choose a secure password)
- Full name: Your name
- Email: your@email.com

Click "Save and Continue"

---

## 🔗 Connecting Your BeatWake Project

### Method 1: Automatic Setup (Recommended)

Run the setup script:
```bash
./jenkins_setup.sh
```

This creates a pipeline job named "BeatWake-Pipeline" automatically.

### Method 2: Manual Setup

#### Option A: Create Pipeline Job from Web UI

1. **Go to Jenkins Dashboard**: http://localhost:8080

2. **Click "New Item"**

3. **Configure Job**:
   - Name: `BeatWake-Pipeline`
   - Type: Select "Pipeline"
   - Click "OK"

4. **Configure Pipeline**:
   - Scroll to "Pipeline" section
   - Definition: "Pipeline script from SCM"
   - SCM: "Git"
   - Repository URL: 
     - Local: `file:///workspaces/BeatWake`
     - Or your GitHub URL: `https://github.com/yourusername/BeatWake.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`

5. **Add GitHub Webhook (Optional)**:
   - Go to Build Triggers
   - Check "GitHub hook trigger for GITScm polling"

6. **Click "Save"**

#### Option B: Blue Ocean UI (Modern Interface)

1. **Install Blue Ocean** (if not installed):
   - Dashboard → Manage Jenkins → Plugins
   - Search "Blue Ocean"
   - Install and restart

2. **Create Pipeline**:
   - Click "Open Blue Ocean"
   - Click "New Pipeline"
   - Select Git or GitHub
   - Enter repository URL
   - Select branch
   - Jenkins will auto-detect the Jenkinsfile

---

## 🎯 Running Your Pipeline

### Option 1: Manual Trigger

1. Go to http://localhost:8080/job/BeatWake-Pipeline
2. Click "Build Now"
3. Watch the progress in the build history
4. Click on the build number to see logs

### Option 2: Command Line Trigger

```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar -s http://localhost:8080/ build BeatWake-Pipeline

# Or use curl
curl -X POST http://localhost:8080/job/BeatWake-Pipeline/build \
  --user admin:your-api-token
```

### Option 3: Automatic Triggers

The pipeline runs automatically when:
- You push to GitHub (if webhook configured)
- Every 5 minutes if changes detected (SCM polling configured)

---

## 📊 Understanding the Pipeline Stages

Your BeatWake pipeline has these stages:

1. **Checkout** 📥
   - Pulls latest code from repository

2. **Setup Python Environment** 🐍
   - Creates virtual environment
   - Installs dependencies from requirements.txt

3. **Lint Code** 🔍
   - Runs pylint and flake8
   - Checks code quality

4. **Run Tests** 🧪
   - Executes test suite
   - (Currently placeholder - add tests later)

5. **Security Scan** 🔒
   - Checks for vulnerabilities with safety
   - Scans code with bandit

6. **Build Documentation** 📚
   - Verifies README exists

7. **Package** 📦
   - Creates distribution package
   - Archives as .tar.gz

---

## 🔐 Setting Up Credentials

### For GitHub Private Repository:

1. **Generate GitHub Token**:
   ```bash
   gh auth token
   ```

2. **Add to Jenkins**:
   - Dashboard → Manage Jenkins → Credentials
   - Click "System" → "Global credentials"
   - Click "Add Credentials"
   - Kind: "Username with password"
   - Username: your-github-username
   - Password: (paste token)
   - ID: `github-credentials`
   - Click "Create"

3. **Update Jenkinsfile** to use credentials:
   ```groovy
   checkout([
       $class: 'GitSCM',
       branches: [[name: '*/main']],
       userRemoteConfigs: [[
           url: 'https://github.com/yourusername/BeatWake.git',
           credentialsId: 'github-credentials'
       ]]
   ])
   ```

### For Spotify API:

1. **Add Spotify Credentials**:
   - Dashboard → Manage Jenkins → Credentials
   - Add Credentials
   - Kind: "Secret text"
   - Secret: (your Spotify Client ID)
   - ID: `spotify-client-id`
   - Repeat for Client Secret

2. **Use in Jenkinsfile**:
   ```groovy
   environment {
       SPOTIFY_CLIENT_ID = credentials('spotify-client-id')
       SPOTIFY_CLIENT_SECRET = credentials('spotify-client-secret')
   }
   ```

---

## 📱 Viewing Build Results

### Web UI:

1. **Dashboard View**:
   - http://localhost:8080/job/BeatWake-Pipeline

2. **Build History**:
   - Click on build number (e.g., #1, #2)
   - View "Console Output" for logs

3. **Blue Ocean View** (if installed):
   - http://localhost:8080/blue/organizations/jenkins/BeatWake-Pipeline

### Command Line:

```bash
# Get build status
curl http://localhost:8080/job/BeatWake-Pipeline/lastBuild/api/json

# View console output
curl http://localhost:8080/job/BeatWake-Pipeline/lastBuild/consoleText

# Download artifacts
curl -O http://localhost:8080/job/BeatWake-Pipeline/lastBuild/artifact/dist/BeatWake-*.tar.gz
```

---

## 🔄 Integrating with GitHub

### Setup GitHub Webhook:

1. **Get Jenkins URL**:
   - If using Codespaces, note your forwarded port URL
   - Make sure it's publicly accessible

2. **Add Webhook in GitHub**:
   - Go to your repo: Settings → Webhooks
   - Click "Add webhook"
   - Payload URL: `http://your-jenkins-url:8080/github-webhook/`
   - Content type: `application/json`
   - Events: "Just the push event"
   - Click "Add webhook"

3. **Configure Job**:
   - Job → Configure
   - Build Triggers → Check "GitHub hook trigger"
   - Save

Now every push triggers a build automatically!

---

## 🐛 Troubleshooting

### Jenkins Won't Start

```bash
# Check status
sudo systemctl status jenkins

# View logs
sudo journalctl -u jenkins -f

# Check Java
java -version

# Restart Jenkins
sudo systemctl restart jenkins
```

### Can't Access Jenkins Web UI

```bash
# Check if port 8080 is listening
sudo netstat -tlnp | grep 8080

# Check Jenkins is running
ps aux | grep jenkins

# Check firewall (if applicable)
sudo ufw status
```

### Pipeline Fails at Checkout

```bash
# Make sure Git is configured
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Check repository exists
ls -la /workspaces/BeatWake/.git
```

### Python Dependencies Fail

```bash
# Manually test installation
cd /workspaces/BeatWake
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Permission Errors

```bash
# Fix Jenkins permissions
sudo chown -R jenkins:jenkins /var/lib/jenkins

# Add Jenkins user to docker group (if using Docker)
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

---

## 🎓 Advanced Configuration

### Parameterized Builds

Add parameters to your pipeline:

```groovy
parameters {
    choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'], description: 'Target environment')
    string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Git branch to build')
}
```

### Parallel Stages

Run tests in parallel:

```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') {
            steps { sh 'pytest tests/unit' }
        }
        stage('Integration Tests') {
            steps { sh 'pytest tests/integration' }
        }
    }
}
```

### Notifications

Add Slack/Email notifications:

```groovy
post {
    success {
        mail to: 'team@example.com',
             subject: "Build Succeeded: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
             body: "Good news! The build succeeded."
    }
    failure {
        mail to: 'team@example.com',
             subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
             body: "Build failed. Check logs."
    }
}
```

---

## 📚 Useful Jenkins Commands

```bash
# Start Jenkins
sudo systemctl start jenkins

# Stop Jenkins
sudo systemctl stop jenkins

# Restart Jenkins
sudo systemctl restart jenkins

# View logs
sudo journalctl -u jenkins -f

# Get initial password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword

# Backup Jenkins
sudo tar -czf jenkins-backup.tar.gz /var/lib/jenkins

# Restore Jenkins
sudo tar -xzf jenkins-backup.tar.gz -C /
```

---

## 🌐 Useful URLs

- **Dashboard**: http://localhost:8080
- **Pipeline Job**: http://localhost:8080/job/BeatWake-Pipeline
- **Blue Ocean**: http://localhost:8080/blue
- **Credentials**: http://localhost:8080/credentials
- **System Log**: http://localhost:8080/log
- **Plugin Manager**: http://localhost:8080/pluginManager

---

## 📞 Need Help?

- Jenkins Documentation: https://www.jenkins.io/doc/
- Pipeline Syntax: https://www.jenkins.io/doc/book/pipeline/syntax/
- Blue Ocean: https://www.jenkins.io/doc/book/blueocean/

---

**Happy Building! 🚀**
