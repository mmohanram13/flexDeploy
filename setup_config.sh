#!/bin/bash
# setup_config.sh - Setup FlexDeploy configuration files

set -e

echo "🔧 FlexDeploy Configuration Setup"
echo "=================================="
echo ""

# Check if config.ini already exists
if [ -f "config.ini" ]; then
    echo "⚠️  config.ini already exists!"
    read -p "Do you want to overwrite it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing config.ini"
        exit 0
    fi
fi

# Copy example config
echo "📝 Creating config.ini from template..."
cp config.ini.example config.ini
echo "✓ config.ini created"
echo ""

# Prompt for SSO configuration
echo "AWS SSO Configuration"
echo "---------------------"
read -p "SSO Start URL [https://superopsglobalhackathon.awsapps.com/start/#]: " sso_url
sso_url=${sso_url:-https://superopsglobalhackathon.awsapps.com/start/#}

read -p "SSO Region [us-east-2]: " sso_region
sso_region=${sso_region:-us-east-2}

# Update config.ini
sed -i.bak "s|sso_start_url = .*|sso_start_url = $sso_url|" config.ini
sed -i.bak "s|sso_region = .*|sso_region = $sso_region|" config.ini
rm config.ini.bak

echo "✓ SSO configuration saved to config.ini"
echo ""

# Check for AWS credentials
echo "AWS Credentials Check"
echo "---------------------"
if [ -f "$HOME/.aws/credentials" ]; then
    echo "✓ ~/.aws/credentials file exists"
    
    if grep -q "aws_access_key_id" "$HOME/.aws/credentials"; then
        echo "✓ Credentials appear to be configured"
    else
        echo "⚠️  ~/.aws/credentials exists but may be empty"
    fi
else
    echo "❌ ~/.aws/credentials not found"
    echo ""
    echo "You need to create ~/.aws/credentials with:"
    echo ""
    echo "  [default]"
    echo "  aws_access_key_id = YOUR_KEY"
    echo "  aws_secret_access_key = YOUR_SECRET"
    echo "  aws_session_token = YOUR_TOKEN"
    echo ""
    read -p "Create ~/.aws/credentials now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$HOME/.aws"
        cat > "$HOME/.aws/credentials" << 'EOF'
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
aws_session_token = YOUR_SESSION_TOKEN
EOF
        echo "✓ Created ~/.aws/credentials template"
        echo "⚠️  You MUST edit this file with your actual credentials!"
        echo ""
        read -p "Open in editor now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} "$HOME/.aws/credentials"
        fi
    fi
fi

echo ""
echo "=================================="
echo "✓ Configuration Setup Complete!"
echo "=================================="
echo ""
echo "Configuration files:"
echo "  ✓ config.ini - FlexDeploy settings (SSO, regions, models)"
echo "  ✓ ~/.aws/credentials - AWS credentials (keys, tokens)"
echo ""
echo "Next steps:"
echo "  1. Verify config.ini has correct SSO settings"
echo "  2. Update ~/.aws/credentials with valid AWS credentials"
echo "  3. Run: ./deploy_bedrock.sh"
echo ""
