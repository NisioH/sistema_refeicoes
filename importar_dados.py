import os
import sys
import django
import pandas as pd
from datetime import datetime

# 1. Força o Python a enxergar a pasta atual
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Configuração do ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception:
    pass

# 3. IMPORTAÇÃO DO MODEL PARA O BANCO DE DADOS
from refeicoes.models import RegistroRefeicao


def safe_int(valor):
    """Transforma vazios, NaN ou tracinhos em 0"""
    if pd.isna(valor): return 0
    valor_str = str(valor).strip()
    if valor_str in ['-', '', 'nan', 'NaT']: return 0
    try:
        return int(float(valor_str))
    except ValueError:
        return 0


def importar_para_banco(nome_arquivo):
    print(f"\n🚀 --- INICIANDO IMPORTAÇÃO OFICIAL PARA A NUVEM: {nome_arquivo} --- \n")

    try:
        abas_do_excel = pd.read_excel(nome_arquivo, sheet_name=None)
        total_geral = 0

        for nome_aba, df in abas_do_excel.items():
            setor_atual = nome_aba.strip()
            print(f"\n🔍 A processar e enviar a aba: '{setor_atual}'...")

            df.columns = [str(c).strip() for c in df.columns]

            if 'Data' not in df.columns:
                print(f"  ⚠️ A aba '{nome_aba}' não tem a coluna 'Data'. A saltar...")
                continue

            cont_dias = 0

            for index, row in df.iterrows():
                data_val = row['Data']

                if pd.isna(data_val) or str(data_val).strip() == '':
                    continue

                # Converte a data para um objeto de data nativo que o banco de dados entende
                if isinstance(data_val, datetime):
                    data_db = data_val.date()
                else:
                    try:
                        data_db = pd.to_datetime(data_val, dayfirst=True).date()
                    except:
                        print(f"  ⚠️ Erro de formato de data na linha {index+2}. A saltar...")
                        continue

                cafe = safe_int(row.get('Cafe', 0))
                buffet = safe_int(row.get('AlmocoBuffet', 0))
                marmita = safe_int(row.get('AlmocoMarmita', 0))
                janta = safe_int(row.get('Janta', 0))
                lanche = safe_int(row.get('Lanche', 0))

                if cafe == 0 and buffet == 0 and marmita == 0 and janta == 0 and lanche == 0:
                    continue

                local = str(row.get('Cantina', '')).strip()
                if not local or local.lower() == 'nan':
                    local = "Cantina do Secador" if "secador" in setor_atual.lower() else "Cantina da Sede"

                # ----- INJEÇÃO NO BANCO DE DADOS -----
                try:
                    RegistroRefeicao.objects.create(
                        data_consumo=data_db,
                        local=local,
                        setor=setor_atual,
                        qtd_cafe=cafe,
                        qtd_almoco_buffet=buffet,
                        qtd_almoco_marmita=marmita,
                        qtd_janta=janta,
                        qtd_lanche=lanche
                    )
                    # Imprime no terminal em tempo real para você acompanhar o progresso
                    print(f"  ✅ Salvo no banco: {data_db.strftime('%d/%m/%Y')} | {setor_atual} | Café:{cafe} Buffet:{buffet} Marm:{marmita} Janta:{janta} Lanche:{lanche}")
                    cont_dias += 1
                except Exception as e:
                    print(f"  ❌ Erro ao salvar {data_db} - {setor_atual}: {e}")

            print(f"  ✅ Concluído: {cont_dias} registos da aba '{nome_aba}' enviados com sucesso.")
            total_geral += cont_dias

        print(f"\n🎉 FIM DA IMPORTAÇÃO! {total_geral} registos injetados na nuvem de forma permanente.")

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")


if __name__ == '__main__':
    arquivo_alvo = 'ControleRefeicoes.xlsx'
    importar_para_banco(arquivo_alvo)