import pdfplumber
from smart_detector import SmartDetector
import os

# Inicializar detector inteligente
smart_detector = SmartDetector()

print("BUROCRATA DE BOLSO - INTELIGENCIA ARTIFICIAL")
print("=" * 60)

# 1. Treinar com seus contratos existentes
print("\nFASE 1: TREINAMENTO COM CONTRATOS EXISTENTES")
pasta_contratos = r'C:\Users\pedro\OneDrive\Área de Trabalho\Teste do burocrata'
smart_detector.treinar_com_contratos_existentes(pasta_contratos)

# 2. Testar com um contrato específico
print("\nFASE 2: TESTE DE DETECCAO INTELIGENTE")

# Testar com CONTRATO DE EMPREGO 1
contrato_teste = 'CONTRATO DE EMPREGO 1.pdf'
caminho_completo = os.path.join(pasta_contratos, contrato_teste)

try:
    # Extrair texto
    texto = ""
    with pdfplumber.open(caminho_completo) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texto += page_text + "\n"
    
    print(f"\n[CONTRATO] ANALISANDO: {contrato_teste}")
    print("-" * 40)
    
    # Análise inteligente
    resultado = smart_detector.analisar_documento_inteligente(texto)
    
    print(f"Tipo: {resultado['tipo_documento']}")
    print(f"Problemas: {resultado['total']} (Criticos: {resultado['criticos']})")
    print(f"Score: {resultado['score']}%")
    print(f"Status: {resultado['status']}")
    
    # Informações do aprendizado
    learning = resultado.get('learning_info', {})
    print(f"\n[INTELIGENCIA]:")
    print(f"   Falha detectada: {learning.get('failure_detected', False)}")
    print(f"   Padroes aprendidos: {learning.get('new_patterns', 0)}")
    print(f"   Analise melhorada: {learning.get('improved_analysis', False)}")
    
    if learning.get('improvement', 0) > 0:
        print(f"   [MELHORIA]: +{learning['improvement']} problemas detectados!")
    
    # Mostrar problemas aprendidos
    problemas_aprendidos = [p for p in resultado['problemas'] if p.get('tipo') == 'APRENDIDO']
    if problemas_aprendidos:
        print(f"\n[PROBLEMAS DETECTADOS PELA IA]:")
        for i, problema in enumerate(problemas_aprendidos, 1):
            print(f"   {i}. {problema['descricao']}")
            print(f"      Confianca: {problema.get('confidence', 0):.1%}")
    
    # Status geral do aprendizado
    print(f"\n[STATUS DO APRENDIZADO]:")
    status = smart_detector.get_learning_status()
    print(f"   Total analisado: {status['total_analyzed']}")
    print(f"   Padroes aprendidos: {status['patterns_learned']}")
    print(f"   Taxa de aprendizado: {status['learning_rate']:.2%}")
    
except Exception as e:
    print(f"ERRO no teste: {e}")

print("\nSISTEMA DE APRENDIZADO ATIVO!")
print("   A IA agora aprende com cada erro detectado!")
print("   Cada documento analisado torna o sistema mais inteligente!")
