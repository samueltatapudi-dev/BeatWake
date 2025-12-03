#!/bin/bash

echo "🔧 Installing Jenkins in Dev Container..."
echo ""

# Update package list
echo "📦 Updating package list..."
sudo apt-get update

# Install Java (Jenkins requirement)
echo "☕ Installing Java..."
sudo apt-get install -y openjdk-17-jdk

# Verify Java installation
java -version
echo ""

# Add Jenkins repository key
echo "🔑 Adding Jenkins repository..."
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key

# Add Jenkins repository
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

# Update package list with Jenkins repo
echo "📦 Updating package list with Jenkins repository..."
sudo apt-get update

# Install Jenkins
echo "🚀 Installing Jenkins..."
sudo apt-get install -y jenkins

# Start Jenkins service
echo "▶️  Starting Jenkins service..."
sudo systemctl enable jenkins
sudo systemctl start jenkins

# Wait for Jenkins to start
echo "⏳ Waiting for Jenkins to initialize (30 seconds)..."
sleep 30

# Get initial admin password
echo ""
echo "✅ Jenkins installed successfully!"
echo ""
echo "📋 Jenkins Information:"
echo "   URL: http://localhost:8080"
echo "   Initial Admin Password:"
echo ""
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
echo ""
echo "💡 Next steps:"
echo "   1. Forward port 8080 in your dev container"
echo "   2. Open http://localhost:8080 in your browser"
echo "   3. Use the password above to unlock Jenkins"
echo "   4. Install suggested plugins"
echo "   5. Create your first admin user"
echo ""
echo "🔧 Useful commands:"
echo "   sudo systemctl status jenkins   - Check Jenkins status"
echo "   sudo systemctl stop jenkins     - Stop Jenkins"
echo "   sudo systemctl start jenkins    - Start Jenkins"
echo "   sudo systemctl restart jenkins  - Restart Jenkins"
