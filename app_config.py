"""
Configuração centralizada da aplicação Flet
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Diretório base
BASE_DIR = Path(__file__).resolve().parent

# ===== API DJANGO =====
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_REFEICOES_ENDPOINT = f"{API_BASE_URL}/api/registros-refeicao/"

# Timeout das requisições
REQUEST_TIMEOUT = 10  # segundos

# ===== PREÇOS (padrão, podem ser sobrescritos pela API) =====
PRECOS_PADRAO = {
    'cafe': 9.00,
    'buffet': 24.00,
    'marmita': 21.50,
    'janta': 21.50,
    'lanche': 9.00
}

# ===== SETORES =====
SETORES_SECADOR = [
    "Colaborador secador",
    "Colaborador algodoeira",
    "Terceirizado algodoeira",
    "Safrista algodoeira",
    "Corporativo",
    "Terceiros Fazenda"
]

SETORES_SEDE = [
    "Colaborador sede",
    "Corporativo",
    "Terceiros Fazenda"
]

LOCAIS_REFEICAO = {
    'SECADOR': 'Cantina do Secador',
    'SEDE': 'Cantina Sede'
}

# ===== INTERFACE FLET =====
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 850
THEME_MODE = "DARK"  # "LIGHT" ou "DARK"
BGCOLOR = "#0f1116"
PADDING = 30

# ===== LOGS =====
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app_flet.log"
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
