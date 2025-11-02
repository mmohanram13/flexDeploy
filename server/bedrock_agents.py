"""
AWS Bedrock Agents using Amazon Nova Models
Implements AI agents for FlexDeploy using AWS Bedrock Runtime API
Credentials are loaded from ~/.aws/credentials (aws_access_key_id, aws_secret_access_key, aws_session_token)
Configuration is loaded from config.ini (SSO URLs, regions, model IDs)
"""
import os
import json
import boto3
from typing import Dict, Any, List, Optional, Tuple
from botocore.exceptions import ClientError

from server.config import get_config


class BedrockAgentService:
    """Service for managing AWS Bedrock agents with Amazon Nova models"""
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize Bedrock agent service
        
        Args:
            region_name: AWS region for Bedrock service (defaults to config.ini setting)
        
        Note:
            AWS credentials are automatically loaded from ~/.aws/credentials
            Configuration (SSO, regions, models) loaded from config.ini
        """
        # Load configuration
        config = get_config()
        
        # Use region from config if not specified
        if region_name is None:
            region_name = config.bedrock_region
        
        self.region_name = region_name
        self.sso_start_url = config.sso_start_url
        self.sso_region = config.sso_region
        
        # Initialize boto3 client with correct profile - credentials from ~/.aws/credentials
        # Create session with the correct profile
        session = boto3.Session(profile_name='942237908630_AdministratorAccess')
        self.bedrock_runtime = session.client(
            service_name='bedrock-runtime',
            region_name=region_name
            # Credentials automatically loaded from ~/.aws/credentials profile:
            # - aws_access_key_id
            # - aws_secret_access_key
            # - aws_session_token (if using SSO)
        )
        
        # Amazon Nova model IDs from config
        self.nova_pro_model = config.bedrock_model_pro
        self.nova_lite_model = config.bedrock_model_lite
        self.default_max_tokens = config.default_max_tokens
        self.default_temperature = config.default_temperature
        
    def invoke_model(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Invoke Amazon Nova model with a prompt
        
        Args:
            prompt: The prompt to send to the model
            model_id: Model ID (defaults to Nova Pro from config)
            max_tokens: Maximum tokens to generate (defaults to config setting)
            temperature: Temperature for generation (defaults to config setting)
            
        Returns:
            Generated text response
        """
        if model_id is None:
            model_id = self.nova_pro_model
        if max_tokens is None:
            max_tokens = self.default_max_tokens
        if temperature is None:
            temperature = self.default_temperature
        
        import time
        start_time = time.time()
        
        try:
            # Prepare the request body for Nova models
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            print(f"\n{'='*80}")
            print(f"🚀 BEDROCK API REQUEST")
            print(f"{'='*80}")
            print(f"Model: {model_id}")
            print(f"Max Tokens: {max_tokens}")
            print(f"Temperature: {temperature}")
            print(f"Prompt Length: {len(prompt)} characters")
            print(f"Prompt Preview: {prompt[:200]}...")
            
            # Invoke the model
            response = self.bedrock_runtime.converse(
                modelId=model_id,
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"]
            )
            
            # Extract the generated text
            output_message = response['output']['message']
            generated_text = output_message['content'][0]['text']
            
            elapsed_time = time.time() - start_time
            
            print(f"\n✅ BEDROCK API RESPONSE")
            print(f"{'='*80}")
            print(f"Response Length: {len(generated_text)} characters")
            print(f"Time Taken: {elapsed_time:.2f}s")
            print(f"Response Preview: {generated_text[:200]}...")
            print(f"{'='*80}\n")
            
            return generated_text
            
        except ClientError as e:
            elapsed_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"\n❌ BEDROCK API ERROR (after {elapsed_time:.2f}s)")
            print(f"{'='*80}")
            print(f"Error Code: {error_code}")
            print(f"Error Message: {error_message}")
            print(f"{'='*80}\n")
            raise Exception(f"Bedrock API error ({error_code}): {error_message}")
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\n❌ BEDROCK ERROR (after {elapsed_time:.2f}s)")
            print(f"{'='*80}")
            print(f"Error: {str(e)}")
            print(f"{'='*80}\n")
            raise Exception(f"Error invoking Bedrock model: {str(e)}")


class RingCategorizationAgent:
    """
    Agent for ring categorization using SQL + Reasoning pipeline
    Pipeline: prompt -> SQL agent -> reasoning agent -> result
    """
    
    def __init__(self, bedrock_service: BedrockAgentService, db_connection):
        self.bedrock = bedrock_service
        self.db = db_connection
        
    def categorize_device(
        self,
        device_data: Dict[str, Any],
        ring_prompts: List[Dict[str, Any]]
    ) -> Tuple[int, str]:
        """
        Categorize a device into a ring based on ring prompts
        
        Args:
            device_data: Device information including metrics
            ring_prompts: List of ring configurations with categorization prompts
            
        Returns:
            Tuple of (ring_id, reasoning)
        """
        # Step 1: SQL Agent - Get device metrics query
        sql_prompt = f"""
        You are a SQL expert. Given this device data:
        {json.dumps(device_data, indent=2)}
        
        Extract the key metrics that would be relevant for deployment ring categorization:
        - CPU Usage: {device_data.get('avgCpuUsage', 'N/A')}%
        - Memory Usage: {device_data.get('avgMemoryUsage', 'N/A')}%
        - Disk Space Free: {device_data.get('avgDiskSpace', 'N/A')}%
        - Risk Score: {device_data.get('riskScore', 'N/A')}
        - Department: {device_data.get('department', 'N/A')}
        - Site: {device_data.get('site', 'N/A')}
        
        Provide a summary of these metrics in a structured format.
        """
        
        metrics_summary = self.bedrock.invoke_model(
            prompt=sql_prompt,
            temperature=0.3
        )
        
        # Step 2: Reasoning Agent - Match device to appropriate ring
        # Sort rings by priority (highest ring number first)
        sorted_rings = sorted(ring_prompts, key=lambda r: r['ringId'], reverse=True)
        
        ring_descriptions = "\n\n".join([
            f"Ring {r['ringId']}: {r['ringName']}\n"
            f"Criteria: {r['categorizationPrompt']}"
            for r in sorted_rings
        ])
        
        reasoning_prompt = f"""
        You are a deployment strategy expert. Evaluate this device against ring criteria in priority order.
        
        Device Metrics Summary:
        {metrics_summary}
        
        Available Rings (in priority order - highest ring has most priority):
        {ring_descriptions}
        
        IMPORTANT: Evaluate the rings in order from Ring 3 down to Ring 0. Assign the device to the FIRST ring whose criteria it matches.
        Higher ring numbers have priority - if a device matches multiple rings, it should be assigned to the highest matching ring.
        
        Evaluation Process:
        1. Check if device matches Ring 3 criteria - if yes, assign to Ring 3
        2. If not, check Ring 2 criteria - if yes, assign to Ring 2
        3. If not, check Ring 1 criteria - if yes, assign to Ring 1
        4. If none match, assign to Ring 0 (default/catch-all)
        
        Respond in this JSON format:
        {{
            "ring_id": <selected ring number>,
            "reasoning": "<brief explanation of why this ring was chosen based on matching criteria>"
        }}
        """
        
        reasoning_response = self.bedrock.invoke_model(
            prompt=reasoning_prompt,
            temperature=0.5
        )
        
        # Parse the response
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_text = reasoning_response.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                
            result = json.loads(response_text)
            ring_id = int(result["ring_id"])
            reasoning = result["reasoning"]
            
            return ring_id, reasoning
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback: Default to Ring 1 (Low Risk)
            return 1, f"Default categorization due to parsing error: {str(e)}"
    
    def batch_categorize_devices(
        self,
        devices: List[Dict[str, Any]],
        ring_prompts: List[Dict[str, Any]]
    ) -> List[Tuple[str, int, str]]:
        """
        Categorize multiple devices in batch using a single API call
        
        Args:
            devices: List of device data dictionaries
            ring_prompts: Ring configurations
            
        Returns:
            List of tuples: (device_id, ring_id, reasoning)
        """
        print(f"\n🔄 Batch categorizing {len(devices)} devices...")
        
        # Sort rings by priority (highest ring number first)
        sorted_rings = sorted(ring_prompts, key=lambda r: r['ringId'], reverse=True)
        
        # Build ring descriptions
        ring_descriptions = "\n\n".join([
            f"Ring {r['ringId']}: {r['ringName']}\n"
            f"Criteria: {r['categorizationPrompt']}"
            for r in sorted_rings
        ])
        
        # Build device summaries
        device_summaries = []
        for device in devices:
            summary = {
                "device_id": device['deviceId'],
                "device_name": device.get('deviceName', 'N/A'),
                "cpu_usage": device.get('avgCpuUsage', 0),
                "memory_usage": device.get('avgMemoryUsage', 0),
                "disk_free": device.get('avgDiskSpace', 0),
                "risk_score": device.get('riskScore', 0),
                "department": device.get('department', 'N/A'),
                "site": device.get('site', 'N/A'),
            }
            device_summaries.append(summary)
        
        # Single prompt for all devices
        batch_prompt = f"""
        You are a deployment strategy expert. Categorize ALL devices into appropriate rings based on their metrics and ring criteria.
        
        Available Rings (in priority order - highest ring has most priority):
        {ring_descriptions}
        
        IMPORTANT EVALUATION RULES:
        1. Evaluate rings from Ring 3 down to Ring 0
        2. Assign each device to the FIRST ring whose criteria it matches
        3. Higher ring numbers have priority - if a device matches multiple rings, assign to the highest matching ring
        4. If a device doesn't match any ring criteria, assign to Ring 0 (default/catch-all)
        
        Devices to Categorize:
        {json.dumps(device_summaries, indent=2)}
        
        Respond with a JSON array containing one object per device in this EXACT format:
        [
            {{
                "device_id": "<device_id>",
                "ring_id": <number>,
                "reasoning": "<brief explanation>"
            }},
            ...
        ]
        
        IMPORTANT: Return ONLY the JSON array, no additional text or markdown formatting.
        """
        
        try:
            response = self.bedrock.invoke_model(
                prompt=batch_prompt,
                temperature=0.3,
                max_tokens=4000  # Increased for batch response
            )
            
            # Parse the response
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Find JSON array in response
            if "[" in response_text:
                json_start = response_text.find("[")
                json_end = response_text.rfind("]") + 1
                response_text = response_text[json_start:json_end]
            
            categorizations = json.loads(response_text)
            
            # Convert to expected format
            results = []
            for cat in categorizations:
                device_id = cat.get("device_id")
                ring_id = int(cat.get("ring_id", 0))
                reasoning = cat.get("reasoning", "No reasoning provided")
                results.append((device_id, ring_id, reasoning))
            
            print(f"✅ Successfully categorized {len(results)} devices in single batch")
            return results
            
        except Exception as e:
            print(f"⚠️  Batch categorization failed: {str(e)}")
            print(f"   Falling back to individual categorization...")
            # Fallback to individual categorization
            results = []
            for device in devices:
                ring_id, reasoning = self.categorize_device(device, ring_prompts)
                results.append((device['deviceId'], ring_id, reasoning))
            return results


class DeploymentFailureAgent:
    """
    Agent for analyzing deployment failures
    Pipeline: gating factor -> prompt -> result
    """
    
    def __init__(self, bedrock_service: BedrockAgentService):
        self.bedrock = bedrock_service
        
    def analyze_failure(
        self,
        ring_name: str,
        device_metrics: List[Dict[str, Any]],
        gating_factors: Dict[str, Any],
        deployment_name: str
    ) -> str:
        """
        Analyze why a deployment failed for a specific ring
        
        Args:
            ring_name: Name of the ring that failed
            device_metrics: Metrics of devices in the ring
            gating_factors: Gating factor thresholds
            deployment_name: Name of the deployment
            
        Returns:
            Detailed failure analysis
        """
        # Calculate violation statistics
        violations = {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'risk_score': 0
        }
        
        for device in device_metrics:
            if gating_factors.get('avgCpuUsageMax') and \
               device.get('avgCpuUsage', 0) > gating_factors['avgCpuUsageMax']:
                violations['cpu'] += 1
                
            if gating_factors.get('avgMemoryUsageMax') and \
               device.get('avgMemoryUsage', 0) > gating_factors['avgMemoryUsageMax']:
                violations['memory'] += 1
                
            if gating_factors.get('avgDiskFreeSpaceMin') and \
               device.get('avgDiskSpace', 100) < gating_factors['avgDiskFreeSpaceMin']:
                violations['disk'] += 1
                
            risk_score = device.get('riskScore', 50)
            if gating_factors.get('riskScoreMin') and risk_score < gating_factors['riskScoreMin']:
                violations['risk_score'] += 1
            if gating_factors.get('riskScoreMax') and risk_score > gating_factors['riskScoreMax']:
                violations['risk_score'] += 1
        
        total_devices = len(device_metrics)
        
        analysis_prompt = f"""
        You are a deployment failure analysis expert. Analyze why this deployment failed.
        
        Deployment: {deployment_name}
        Ring: {ring_name}
        Total Devices: {total_devices}
        
        Gating Factors (Thresholds):
        - Max CPU Usage: {gating_factors.get('avgCpuUsageMax', 'N/A')}%
        - Max Memory Usage: {gating_factors.get('avgMemoryUsageMax', 'N/A')}%
        - Min Disk Free Space: {gating_factors.get('avgDiskFreeSpaceMin', 'N/A')}%
        - Risk Score Range: {gating_factors.get('riskScoreMin', 0)}-{gating_factors.get('riskScoreMax', 100)}
        
        Violations Detected:
        - CPU violations: {violations['cpu']} devices ({violations['cpu']/total_devices*100:.1f}%)
        - Memory violations: {violations['memory']} devices ({violations['memory']/total_devices*100:.1f}%)
        - Disk space violations: {violations['disk']} devices ({violations['disk']/total_devices*100:.1f}%)
        - Risk score violations: {violations['risk_score']} devices ({violations['risk_score']/total_devices*100:.1f}%)
        
        Provide a concise, actionable failure analysis explaining:
        1. The primary reason for failure
        2. Which devices are affected
        3. Recommended next steps
        
        Keep the response under 200 words.
        """
        
        analysis = self.bedrock.invoke_model(
            prompt=analysis_prompt,
            temperature=0.4
        )
        
        return analysis.strip()


class GatingFactorAgent:
    """
    Agent for converting natural language to gating factors
    Pipeline: user text -> prompt -> gating factor -> result
    """
    
    def __init__(self, bedrock_service: BedrockAgentService):
        self.bedrock = bedrock_service
        
    def parse_natural_language(self, user_input: str) -> Dict[str, Any]:
        """
        Convert natural language gating requirements to numeric factors
        
        Args:
            user_input: User's natural language description
            
        Returns:
            Dictionary of gating factors
        """
        prompt = f"""
        You are a deployment gating expert. Convert the user's natural language requirements 
        into specific numeric gating factor thresholds.
        
        User Requirements:
        "{user_input}"
        
        Gating Factors to set:
        - avgCpuUsageMax: Maximum allowed CPU usage percentage (0-100)
        - avgMemoryUsageMax: Maximum allowed memory usage percentage (0-100)
        - avgDiskFreeSpaceMin: Minimum required free disk space percentage (0-100)
        - riskScoreMin: Minimum risk score (0-100, where higher is safer)
        - riskScoreMax: Maximum risk score (0-100, where higher is safer)
        
        Guidelines:
        - Conservative/Safe: CPU<60%, Memory<70%, Disk>30%, RiskScore 70-100
        - Moderate: CPU<80%, Memory<85%, Disk>20%, RiskScore 40-100
        - Aggressive: CPU<95%, Memory<95%, Disk>10%, RiskScore 0-100
        
        Respond ONLY with a JSON object in this exact format:
        {{
            "avgCpuUsageMax": <number>,
            "avgMemoryUsageMax": <number>,
            "avgDiskFreeSpaceMin": <number>,
            "riskScoreMin": <number>,
            "riskScoreMax": <number>,
            "explanation": "<brief explanation of the chosen values>"
        }}
        """
        
        response = self.bedrock.invoke_model(
            prompt=prompt,
            temperature=0.3
        )
        
        try:
            # Extract JSON from response
            response_text = response.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                
            result = json.loads(response_text)
            
            # Validate and constrain values
            gating_factors = {
                "avgCpuUsageMax": max(0, min(100, float(result.get("avgCpuUsageMax", 80)))),
                "avgMemoryUsageMax": max(0, min(100, float(result.get("avgMemoryUsageMax", 80)))),
                "avgDiskFreeSpaceMin": max(0, min(100, float(result.get("avgDiskFreeSpaceMin", 20)))),
                "riskScoreMin": max(0, min(100, int(result.get("riskScoreMin", 0)))),
                "riskScoreMax": max(0, min(100, int(result.get("riskScoreMax", 100)))),
                "explanation": result.get("explanation", "AI-generated gating factors")
            }
            
            return gating_factors
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback to safe defaults
            return {
                "avgCpuUsageMax": 80.0,
                "avgMemoryUsageMax": 80.0,
                "avgDiskFreeSpaceMin": 20.0,
                "riskScoreMin": 0,
                "riskScoreMax": 100,
                "explanation": f"Using safe defaults due to parsing error: {str(e)}"
            }
    
    def validate_and_suggest(
        self,
        gating_factors: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate gating factors and suggest improvements
        
        Args:
            gating_factors: Current gating factors
            historical_data: Optional historical deployment data
            
        Returns:
            Validation result with suggestions
        """
        validation_prompt = f"""
        You are a deployment safety expert. Review these gating factors for potential issues.
        
        Current Gating Factors:
        {json.dumps(gating_factors, indent=2)}
        
        {f"Historical Deployment Data: {json.dumps(historical_data, indent=2)}" if historical_data else ""}
        
        Evaluate:
        1. Are these thresholds too strict (might block valid deployments)?
        2. Are they too lenient (might allow risky deployments)?
        3. Are they well-balanced?
        4. Any specific concerns?
        
        Respond in JSON format:
        {{
            "is_valid": <true/false>,
            "risk_level": "<low/medium/high>",
            "suggestions": ["<suggestion 1>", "<suggestion 2>"],
            "recommended_adjustments": {{
                "field_name": <new_value>
            }}
        }}
        """
        
        response = self.bedrock.invoke_model(
            prompt=validation_prompt,
            temperature=0.4
        )
        
        try:
            response_text = response.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
                
            return json.loads(response_text)
        except:
            return {
                "is_valid": True,
                "risk_level": "medium",
                "suggestions": ["Unable to validate - proceeding with current factors"],
                "recommended_adjustments": {}
            }
    
    def evaluate_gating_decision(
        self,
        gating_prompt: str,
        device_metrics: List[Dict[str, Any]],
        ring_name: str
    ) -> Dict[str, Any]:
        """
        Evaluate whether deployment should proceed to next ring based on gating prompt
        
        Args:
            gating_prompt: Natural language gating criteria
            device_metrics: List of device metrics from current ring
            ring_name: Name of the current ring
            
        Returns:
            Decision with reasoning
        """
        print(f"\n🔍 Evaluating gating decision for {ring_name}...")
        
        # Summarize device metrics
        metrics_summary = {
            "total_devices": len(device_metrics),
            "avg_cpu_usage": sum(d.get('avgCpuUsage', 0) for d in device_metrics) / len(device_metrics) if device_metrics else 0,
            "avg_memory_usage": sum(d.get('avgMemoryUsage', 0) for d in device_metrics) / len(device_metrics) if device_metrics else 0,
            "avg_disk_free": sum(d.get('avgDiskSpace', 0) for d in device_metrics) / len(device_metrics) if device_metrics else 0,
            "avg_risk_score": sum(d.get('riskScore', 50) for d in device_metrics) / len(device_metrics) if device_metrics else 50,
            "max_cpu_usage": max(d.get('avgCpuUsage', 0) for d in device_metrics) if device_metrics else 0,
            "max_memory_usage": max(d.get('avgMemoryUsage', 0) for d in device_metrics) if device_metrics else 0,
            "min_disk_free": min(d.get('avgDiskSpace', 100) for d in device_metrics) if device_metrics else 100,
        }
        
        decision_prompt = f"""
        You are a deployment gating decision expert. Determine whether deployment should proceed to the next ring.
        
        Current Ring: {ring_name}
        
        Gating Criteria (from user):
        "{gating_prompt}"
        
        Device Metrics Summary:
        {json.dumps(metrics_summary, indent=2)}
        
        Based on the gating criteria and device metrics, decide whether the deployment should:
        - PROCEED to the next ring (metrics meet the criteria)
        - STOP (metrics don't meet the criteria)
        
        Respond ONLY with a JSON object in this exact format:
        {{
            "should_proceed": <true/false>,
            "decision": "<PROCEED or STOP>",
            "confidence": <0.0 to 1.0>,
            "reasoning": "<detailed explanation of why this decision was made>",
            "key_factors": ["<factor 1>", "<factor 2>"]
        }}
        """
        
        try:
            response = self.bedrock.invoke_model(
                prompt=decision_prompt,
                temperature=0.2  # Lower temperature for more consistent decisions
            )
            
            # Parse response
            response_text = response.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Find JSON object in response
            if "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                response_text = response_text[json_start:json_end]
            
            result = json.loads(response_text)
            
            print(f"{'✅' if result.get('should_proceed') else '🛑'} Gating Decision: {result.get('decision')} (confidence: {result.get('confidence', 0):.2f})")
            
            return result
            
        except Exception as e:
            print(f"⚠️  Gating evaluation failed: {str(e)}")
            # Conservative fallback: stop deployment if evaluation fails
            return {
                "should_proceed": False,
                "decision": "STOP",
                "confidence": 0.5,
                "reasoning": f"Unable to evaluate gating criteria due to error: {str(e)}. Defaulting to safe stop.",
                "key_factors": ["evaluation_error"]
            }


# Singleton instance
_bedrock_service = None

def get_bedrock_service(region_name: Optional[str] = None) -> BedrockAgentService:
    """
    Get or create the Bedrock service singleton
    
    Args:
        region_name: AWS region for Bedrock (defaults to config.ini setting)
    
    Returns:
        BedrockAgentService instance
    
    Note:
        Credentials loaded from ~/.aws/credentials (aws_access_key_id, aws_secret_access_key, aws_session_token)
        Configuration loaded from config.ini (SSO URLs, regions, model IDs)
    """
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockAgentService(region_name=region_name)
    return _bedrock_service
