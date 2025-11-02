"""
Configuration management for FlexDeploy
Loads settings from config.ini and manages AWS credentials from ~/.aws/credentials
"""
import os
import configparser
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for FlexDeploy"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to config.ini file (defaults to ./config.ini)
        """
        if config_path is None:
            # Default to config.ini in the project root
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config.ini'
            )
        
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # Load configuration
        if os.path.exists(config_path):
            self.config.read(config_path)
        else:
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                "Please create config.ini in the project root."
            )
    
    # AWS Configuration
    @property
    def sso_start_url(self) -> str:
        """Get AWS SSO start URL"""
        return self.config.get('aws', 'sso_start_url', 
                              fallback='https://superopsglobalhackathon.awsapps.com/start/#')
    
    @property
    def sso_region(self) -> str:
        """Get AWS SSO region"""
        return self.config.get('aws', 'sso_region', fallback='us-east-2')
    
    @property
    def bedrock_region(self) -> str:
        """Get AWS Bedrock region"""
        return self.config.get('aws', 'bedrock_region', fallback='us-east-2')
    
    @property
    def bedrock_model_pro(self) -> str:
        """Get Amazon Nova Pro model ID"""
        return self.config.get('aws', 'bedrock_model_pro', 
                              fallback='us.amazon.nova-pro-v1:0')
    
    @property
    def bedrock_model_lite(self) -> str:
        """Get Amazon Nova Lite model ID"""
        return self.config.get('aws', 'bedrock_model_lite', 
                              fallback='us.amazon.nova-lite-v1:0')
    
    @property
    def default_max_tokens(self) -> int:
        """Get default max tokens for model generation"""
        return self.config.getint('aws', 'default_max_tokens', fallback=2000)
    
    @property
    def default_temperature(self) -> float:
        """Get default temperature for model generation"""
        return self.config.getfloat('aws', 'default_temperature', fallback=0.7)
    
    # Server Configuration
    @property
    def server_host(self) -> str:
        """Get server host"""
        return self.config.get('server', 'host', fallback='0.0.0.0')
    
    @property
    def server_port(self) -> int:
        """Get server port"""
        return self.config.getint('server', 'port', fallback=8000)
    
    # Database Configuration
    @property
    def db_name(self) -> str:
        """Get database name"""
        return self.config.get('database', 'db_name', fallback='flexdeploy.db')
    
    def get_aws_config(self) -> Dict[str, Any]:
        """
        Get all AWS configuration as a dictionary
        
        Returns:
            Dictionary with AWS configuration
        """
        return {
            'sso_start_url': self.sso_start_url,
            'sso_region': self.sso_region,
            'bedrock_region': self.bedrock_region,
            'bedrock_model_pro': self.bedrock_model_pro,
            'bedrock_model_lite': self.bedrock_model_lite,
            'default_max_tokens': self.default_max_tokens,
            'default_temperature': self.default_temperature,
        }
    
    def print_config(self):
        """Print current configuration (for debugging)"""
        print("FlexDeploy Configuration:")
        print("=" * 50)
        print("\n[AWS Configuration]")
        print(f"  SSO Start URL: {self.sso_start_url}")
        print(f"  SSO Region: {self.sso_region}")
        print(f"  Bedrock Region: {self.bedrock_region}")
        print(f"  Nova Pro Model: {self.bedrock_model_pro}")
        print(f"  Nova Lite Model: {self.bedrock_model_lite}")
        print(f"  Default Max Tokens: {self.default_max_tokens}")
        print(f"  Default Temperature: {self.default_temperature}")
        print("\n[Server Configuration]")
        print(f"  Host: {self.server_host}")
        print(f"  Port: {self.server_port}")
        print("\n[Database Configuration]")
        print(f"  Database: {self.db_name}")
        print("=" * 50)


# Global config instance
_config = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance
    
    Args:
        config_path: Path to config.ini file (optional)
        
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
