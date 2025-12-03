#!/bin/bash

echo "⚙️  Setting up Jenkins for BeatWake project..."
echo ""

# Check if Jenkins is running
if ! sudo systemctl is-active --quiet jenkins; then
    echo "❌ Jenkins is not running. Please start it first:"
    echo "   sudo systemctl start jenkins"
    exit 1
fi

echo "✅ Jenkins is running"
echo ""

# Create Jenkins job directory structure
JENKINS_HOME="/var/lib/jenkins"
JOB_NAME="BeatWake-Pipeline"
JOB_DIR="$JENKINS_HOME/jobs/$JOB_NAME"

echo "📁 Creating Jenkins job: $JOB_NAME"

# Create job configuration
sudo mkdir -p "$JOB_DIR"

# Create config.xml for the job
sudo tee "$JOB_DIR/config.xml" > /dev/null << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <description>BeatWake - Spotify Alarm Clock CI/CD Pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>GIT_BRANCH</name>
          <description>Git branch to build</description>
          <defaultValue>main</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps@2.90">
    <scm class="hudson.plugins.git.GitSCM" plugin="git@4.10.0">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>file:///workspaces/BeatWake</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers>
    <hudson.triggers.SCMTrigger>
      <spec>H/5 * * * *</spec>
      <ignorePostCommitHooks>false</ignorePostCommitHooks>
    </hudson.triggers.SCMTrigger>
  </triggers>
</flow-definition>
EOF

# Set proper permissions
sudo chown -R jenkins:jenkins "$JOB_DIR"

# Reload Jenkins configuration
echo "🔄 Reloading Jenkins configuration..."
sudo systemctl restart jenkins

echo ""
echo "✅ Jenkins setup complete!"
echo ""
echo "📋 Job Details:"
echo "   Job Name: $JOB_NAME"
echo "   Job URL: http://localhost:8080/job/$JOB_NAME"
echo ""
echo "💡 Next steps:"
echo "   1. Open Jenkins at http://localhost:8080"
echo "   2. Navigate to '$JOB_NAME' job"
echo "   3. Click 'Build Now' to run the pipeline"
echo ""
