import yaml
from .paths import PROMPTS_CONFIG_PATH


def build_prompt(agent_name: str) -> str:
    """
    Build a complete prompt from YAML configuration.
    
    Args:
        agent_name: The name of the agent (fuzzer, scanner, enumerator, web_analyzer, exploit_researcher, reporter)
    
    Returns:
        Complete formatted prompt string
    """
    with open(PROMPTS_CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    agents_config = config['adaptive_system']['agents']
    agent_config = agents_config[agent_name]['prompt_config']
    
    prompt_parts = []
    prompt_parts.append(f"Role: {agent_config['role']}")
    prompt_parts.append(f"\n{agent_config['instruction']}")
    
    if 'output_constraints' in agent_config:
        prompt_parts.append("\nOutput Constraints:")
        for constraint in agent_config['output_constraints']:
            prompt_parts.append(f"- {constraint}")
    
    if 'style_or_tone' in agent_config:
        prompt_parts.append(f"\nStyle/Tone: {agent_config['style_or_tone']}")
    
    if 'goal' in agent_config:
        prompt_parts.append(f"\nGoal: {agent_config['goal']}")
    
    return "\n".join(prompt_parts)
