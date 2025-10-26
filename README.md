# 📰 Noticias Diarias de IA

Recopilación automática de noticias sobre Inteligencia Artificial desde fuentes chinas, filtradas y traducidas al español.

> Basado en [EverydayTechNews](https://github.com/nowscott/EverydayTechNews) por [@nowscott](https://github.com/nowscott)

## 🎯 ¿Qué hace?

1. **Extrae** noticias tecnológicas de IT之家 cada 2 horas
2. **Filtra** solo contenido relacionado con IA (GPT, LLMs, OpenAI, Anthropic, etc.)
3. **Ordena** por relevancia según votación de usuarios
4. **Traduce** automáticamente del chino al español

## 🚀 Instalación

```bash
# 1. Haz fork del repositorio
# 2. Listo - Los workflows se ejecutan automáticamente
```

No requiere configuración adicional.

## ⏰ Horarios (España UTC+1)

- **Cada 2 horas**: Scraping de noticias
- **18:30**: Ordenamiento por puntuación
- **19:00**: Filtrado y traducción → Archivo listo en `news_archive/es/`

## 🧪 Prueba Local

```bash
pip install -r requirements.txt
python test_pipeline.py  # Verifica que todo funciona
python src/main.py       # Ejecuta el proceso completo
```

## 📁 Salida

```
news_archive/
├── 2025-10/
│   └── 26.md          # Noticias originales (chino)
└── es/
    └── 2025-10-26.md  # Noticias filtradas y traducidas
```

## 🔧 Diferencias con el original

- ✅ Filtrado específico para IA
- ✅ Traducción automática al español  
- ✅ Sin envío de correos
- ✅ Enfoque en archivo local

## 📄 Licencia

Hereda la licencia del [repositorio original](https://github.com/nowscott/EverydayTechNews).