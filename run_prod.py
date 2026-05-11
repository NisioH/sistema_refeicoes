import os
import sys
from waitress import serve
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

if __name__ == '__main__':
    print("---- SISTEMA DE REFEIÇÕES ATIVO ---")
    print("Acessar em: http://localhost:8000/")
    print("Para fechar, basta fecha esta janela.")

    serve(application, host='0.0.0.0', port=8000, threads=8)
 