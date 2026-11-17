"""Shared non-secret model configuration for both sides of the bridge."""
import os

GATEWAY = 'https://st8tp3ajl0df3n8b8l8qu.apigateway-cn-beijing.volceapi.com/v1'
MODEL = 'deepseek-v4-flash'

def configure():
    base = os.getenv('OPENAI_API_BASE') or os.getenv('OPENAI_BASE_URL') or GATEWAY
    base = base.rstrip('/')
    if base.endswith(('/responses', '/chat/completions', '/compatible')):
        raise ValueError('Use the Chat Completions base URL ending in /v1')
    for name in ('OPENAI_API_BASE', 'OPENAI_BASE_URL'):
        if os.getenv(name) and os.environ[name].rstrip('/') != base:
            raise ValueError('OPENAI_API_BASE and OPENAI_BASE_URL must match')
        os.environ[name] = base
    model = os.getenv('OPENAI_MODEL') or MODEL
    os.environ['OPENAI_MODEL'] = model
    os.environ.setdefault('JAVA_AGENT_EVENT_TIMEOUT', '300')
    return model, base
