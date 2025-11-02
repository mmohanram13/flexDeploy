#!/bin/bash
# deploy_bedrock.sh - Deploy FlexDeploy with AWS Bedrock AI Agents

set -e

echo "🚀 FlexDeploy - AWS Bedrock AI Agents Deployment"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on macOS (for credential path validation)
if [[ "$OSTYPE" == "darwin"* ]]; then
    CREDENTIALS_PATH="$HOME/.aws/credentials"
else
    CREDENTIALS_PATH="$HOME/.aws/credentials"
fi

echo "Step 1: Checking AWS Credentials..."
if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo -e "${RED}❌ AWS credentials not found at $CREDENTIALS_PATH${NC}"
    echo ""
    echo "Please configure AWS credentials:"
    echo "  1. Create file: mkdir -p ~/.aws && touch ~/.aws/credentials"
    echo "  2. Add credentials:"
    echo ""
    echo "     [default]"
    echo "     aws_access_key_id = YOUR_ACCESS_KEY"
    echo "     aws_secret_access_key = YOUR_SECRET_KEY"
    echo "     region = us-east-1"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ AWS credentials file found${NC}"
echo ""

# Test AWS credentials
echo "Step 2: Verifying AWS Access..."
if command -v aws &> /dev/null; then
    if aws sts get-caller-identity --region us-east-1 &>/dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        echo -e "${GREEN}✓ AWS credentials verified (Account: $ACCOUNT_ID)${NC}"
    else
        echo -e "${YELLOW}⚠ Could not verify AWS credentials with AWS CLI${NC}"
        echo "Continuing anyway - will test with Python..."
    fi
else
    echo -e "${YELLOW}⚠ AWS CLI not installed (optional)${NC}"
fi
echo ""

# Test Bedrock access with Python
echo "Step 3: Testing AWS Bedrock Access..."
python3 << 'EOF'
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

try:
    # Create session with the correct profile
    session = boto3.Session(profile_name='942237908630_AdministratorAccess')
    client = session.client('bedrock-runtime', region_name='us-east-1')
    
    # Try a minimal API call
    response = client.converse(
        modelId='us.amazon.nova-lite-v1:0',
        messages=[{
            'role': 'user',
            'content': [{'text': 'test'}]
        }],
        inferenceConfig={'maxTokens': 5}
    )
    
    print("\033[0;32m✓ AWS Bedrock access verified\033[0m")
    print("\033[0;32m✓ Amazon Nova models accessible\033[0m")
    sys.exit(0)
    
except NoCredentialsError:
    print("\033[0;31m❌ AWS credentials not found\033[0m")
    print("Please configure credentials in ~/.aws/credentials")
    sys.exit(1)
    
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDeniedException':
        print("\033[0;31m❌ Access denied to AWS Bedrock\033[0m")
        print("\nPlease:")
        print("1. Go to AWS Console → Bedrock → Model access")
        print("2. Request access to Amazon Nova models")
        print("3. Ensure IAM user has bedrock:InvokeModel permission")
    elif error_code == 'ResourceNotFoundException':
        print("\033[0;31m❌ Amazon Nova models not available in your region\033[0m")
        print("Please ensure you're using us-east-1 region")
    else:
        print(f"\033[0;31m❌ AWS Bedrock error: {error_code}\033[0m")
        print(f"Message: {e.response['Error']['Message']}")
    sys.exit(1)
    
except Exception as e:
    print(f"\033[0;31m❌ Error testing Bedrock: {str(e)}\033[0m")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}Bedrock verification failed. Cannot proceed.${NC}"
    exit 1
fi

echo ""

# Check for uv package manager
echo "Step 4: Installing Dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv package manager..."
    uv pip install -e . --quiet
    echo -e "${GREEN}✓ Dependencies installed with uv${NC}"
else
    echo "Using pip..."
    pip install -e . --quiet
    echo -e "${GREEN}✓ Dependencies installed with pip${NC}"
fi
echo ""

# Verify Python packages
echo "Step 5: Verifying Python Packages..."
python3 << 'EOF'
import sys

packages = {
    'boto3': '1.35.0',
    'fastapi': '0.115.0',
    'strands_agents': '1.12.0',
}

all_ok = True
for package, min_version in packages.items():
    try:
        if package == 'strands_agents':
            import strands_agents
            pkg_name = 'strands-agents'
        else:
            __import__(package)
            pkg_name = package
        print(f"\033[0;32m✓ {pkg_name} installed\033[0m")
    except ImportError:
        print(f"\033[0;31m❌ {pkg_name} not installed\033[0m")
        all_ok = False

if not all_ok:
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}Some dependencies are missing. Run: pip install -e .${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✓ All checks passed!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "FlexDeploy is ready to run with AWS Bedrock AI Agents:"
echo ""
echo -e "  ${GREEN}✓${NC} AWS Bedrock configured"
echo -e "  ${GREEN}✓${NC} Amazon Nova models accessible"
echo -e "  ${GREEN}✓${NC} Dependencies installed"
echo ""
echo "AI Features Available:"
echo "  1. Ring Categorization (SQL + Reasoning pipeline)"
echo "  2. Deployment Failure Analysis"
echo "  3. Gating Factor Natural Language Parsing"
echo ""
echo "To start the server:"
echo -e "  ${YELLOW}python -m server.main${NC}"
echo ""
echo "Or run with auto-start:"
read -p "Start server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting FlexDeploy server..."
    echo ""
    python -m server.main
fi
