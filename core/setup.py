"""
Configuração inicial do logger e setup de ambiente para a aplicação.

Este módulo pode ser usado para configurar logging global.
"""

import logging

# Configuração global de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
