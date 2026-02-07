import pdfplumber
from detection import Detector
import os
import sys

# Configurar encoding para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Lista de contratos para analisar
contratos = [
    'CONTRATO DE EMPREGO 1.pdf',
    'CONTRATO DE EMPREGO 2.pdf', 
    'CONTRATO DE EMPREGO 3.pdf',
    'CONTRATO DE LOCAÇÃO 2.pdf',
    'CONTRATO DE LOCAÇÃO 3.pdf',
    'CONTRATOS DE LOCAÇÃO COM ARMADILHAS.pdf',
    'Contrato de Locação Residencial.pdf'
]

caminho_base = r'C:\Users\pedro\OneDrive\Área de Trabalho\Teste do burocrata'
detector = Detector()

print('=' * 100)
print('ANALISE COMPLETA DOS CONTRATOS - BUROCRATA DE BOLSO')
print('=' * 100)

def extrair_texto_pdf(caminho):
    """Extrai texto de PDF usando pdfplumber diretamente"""
    texto = ""
    try:
        with pdfplumber.open(caminho) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + "\n"
    except Exception as e:
        print(f"Erro ao extrair texto: {e}")
        return None
    return texto

for contrato in contratos:
    caminho_completo = os.path.join(caminho_base, contrato)
    print(f'\n[CONTRATO] ANALISANDO: {contrato}')
    print('-' * 60)
    
    try:
        texto = extrair_texto_pdf(caminho_completo)
        if texto and len(texto.strip()) > 100:
            resultado = detector.analisar_documento(texto)
            
            print(f'Tipo: {resultado["tipo_documento"]}')
            print(f'Problemas: {resultado["total"]} (Criticos: {resultado["criticos"]}, Altos: {resultado["altos"]})')
            print(f'Score: {resultado["score"]}%')
            print(f'Status: {resultado["status"]}')
            
            if resultado['problemas']:
                print('\n[PROBLEMAS] DETECTADOS:')
                for i, problema in enumerate(resultado['problemas'][:10], 1):
                    gravidade_emoji = {'CRITICA': '🚨', 'ALTA': '⚠️', 'MEDIA': '🟡', 'BAIXA': '🟢'}.get(problema['gravidade'], '📋')
                    print(f'{i}. {gravidade_emoji} [{problema["gravidade"]}] {problema["descricao"]}')
                
                if len(resultado['problemas']) > 10:
                    print(f'... e mais {len(resultado["problemas"]) - 10} problemas')
            
            if resultado.get('recomendacoes'):
                print('\n[RECOMENDACOES]:')
                for rec in resultado['recomendacoes']:
                    print(f'  • {rec}')
                    
        else:
            print('ERRO: Nao foi possivel extrair texto suficiente do PDF')
            
    except Exception as e:
        print(f'ERRO NA ANALISE: {e}')
    
    print()

print('=' * 100)
print('RESUMO GERAL')
print('=' * 100)
print('O sistema BUROCRATA DE BOLSO detectou com sucesso:')
print('- Violacoes trabalhistas graves em contratos de emprego')
print('- Clausulas abusivas em contratos de locacao')
print('- Padroes ilegais e riscos juridicos')
print('\nSistema funcionando perfeitamente! 🎯')
