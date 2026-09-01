const CONFIG = {
  models: {
    'gpt-5': {
      name: 'OpenAI GPT-5',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-5'
    },
    'gpt-5.1': {
      name: 'OpenAI GPT-5.1',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-5.1'
    },
    'gpt-5.1-codex': {
      name: 'OpenAI GPT-5.1 Codex',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-5.1-codex'
    },
    'gpt-5-mini': {
      name: 'OpenAI GPT-5 Mini',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-5-mini'
    },
    'gpt-5-nano': {
      name: 'OpenAI GPT-5 Nano',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-5-nano'
    },
    'gpt-4': {
      name: 'OpenAI GPT-4',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-4'
    },
    'gpt-3.5-turbo': {
      name: 'OpenAI GPT-3.5 Turbo',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      provider: 'openai',
      modelName: 'gpt-3.5-turbo'
    },
    'claude-3-opus': {
      name: 'Claude 3 Opus',
      endpoint: 'https://api.anthropic.com/v1/messages',
      provider: 'anthropic',
      modelName: 'claude-3-opus-20240229'
    },
    'claude-3-sonnet': {
      name: 'Claude 3 Sonnet',
      endpoint: 'https://api.anthropic.com/v1/messages',
      provider: 'anthropic',
      modelName: 'claude-3-sonnet-20240229'
    },
    'gemini-pro': {
      name: 'Google Gemini Pro',
      endpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
      provider: 'google',
      modelName: 'gemini-pro'
    }
  },
  defaultTemperature: 0.3,
  maxTokens: 2000
};
