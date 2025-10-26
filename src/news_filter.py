"""Módulo de herramientas de filtrado de noticias"""

import re

def should_keep_news(title):
    """
    Determina si una noticia debe conservarse.
    Debe ser sobre IA y no debe ser spam.

    Args:
        title (str): Título de la noticia (en chino)

    Returns:
        bool: True si debe conservarse, False si debe filtrarse
    """
    
    # 1. Filtrar spam (palabras clave a eliminar)
    filter_keywords = ['广告', '推广', '赞助', '合作', '活动', '福利', '优惠']
    if any(keyword in title for keyword in filter_keywords):
        return False  # Es spam, no conservar

    # 2. Comprobar si es sobre IA (palabras clave a conservar)
    # Comprobamos tanto en mayúsculas/minúsculas para 'AI', 'GPT', etc.
    title_lower = title.lower()
    
    # Lista ampliada de palabras clave de IA
    ai_keywords = [
        # --- Términos Fundamentales ---
        'ai',        # AI
        '人工智能',  # Inteligencia Artificial
        'agi',       # AGI (Inteligencia General Artificial)
        'aigc',      # AIGC (Contenido Generado por IA)
        
        # --- Modelos y Arquitecturas ---
        'gpt',       # GPT
        'llm',       # LLM (Large Language Model)
        '大模型',    # Modelo Grande
        '机器学习',  # Machine Learning
        '深度学习',  # Deep Learning
        '神经网络',  # Neural Network
        'rag',       # RAG (Retrieval-Augmented Generation)

        # --- Empresas Principales ---
        'openai',    # OpenAI
        'anthropic', # Anthropic
        'google',    # Google
        '谷歌',      # Google
        'deepmind',  # DeepMind
        'meta',      # Meta
        'microsoft', # Microsoft
        '微软',      # Microsoft
        'nvidia',    # Nvidia
        '英伟达',    # Nvidia
        'baidu',     # Baidu
        '百度',      # Baidu
        'alibaba',   # Alibaba
        '阿里巴巴',  # Alibaba
        'tencent',   # Tencent
        '腾讯',      # Tencent
        'mistral',   # Mistral AI
        'xai',       # xAI
        
        # --- Modelos/Productos Populares ---
        'claude',    # Claude
        'sora',      # Sora
        'gemini',    # Gemini
        'llama',     # Llama
        'copilot',   # Copilot
        'stable diffusion', # Stable Diffusion
        'midjourney',# Midjourney
        'vision pro', # Vision Pro (relacionado)
        'ernie',     # ERNIE (Baidu)
        '文心一言',  # ERNIE (Baidu)
    ]
    
    if any(keyword in title_lower for keyword in ai_keywords):
        return True  # Es sobre IA y no es spam, conservar

    # 3. Si no es spam pero tampoco es sobre IA, filtrar
    return False

