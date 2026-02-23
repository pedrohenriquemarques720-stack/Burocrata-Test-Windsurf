from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import pdfplumber
import traceback
import sys
from datetime import datetime
from dotenv import load_dotenv

# Importar o Core Engine Jurídico
try:
    from core_juridico import CoreEngineJuridico
    print("✅ CoreEngineJuridico importado com sucesso!")
except Exception as e:
    print(f"❌ ERRO AO IMPORTAR CoreEngineJuridico: {e}")
    traceback.print_exc()
    CoreEngineJuridico = None

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

print("="*50)
print("🚀 SERVIDOR INICIANDO - MODO DEBUG")
print("="*50)

# ===== FUNÇÃO AUXILIAR =====
def extrair_texto_pdf_bytes(bytes_pdf):
    """Extrai texto de bytes de PDF"""
    try:
        print("📄 Tentando extrair texto do PDF...")
        with pdfplumber.open(io.BytesIO(bytes_pdf)) as pdf:
            texto = ""
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
                    print(f"   Página {i+1}: {len(texto_pagina)} caracteres")
                else:
                    print(f"   ⚠️ Página {i+1}: sem texto extraível")
            return texto if texto.strip() else None
    except Exception as e:
        print(f"❌ Erro ao extrair PDF: {e}")
        traceback.print_exc()
        return None

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "core_juridico_carregado": CoreEngineJuridico is not None,
        "timestamp": datetime.now().isoformat()
    })

# ===== ROTA DE TESTE =====
@app.route('/ping')
def ping():
    return jsonify({"pong": True, "status": "online"})

# ===== ROTA PARA ANÁLISE JURÍDICA =====
@app.route('/analisar-documento', methods=['POST', 'OPTIONS'])
def analisar_documento():
    """Recebe um PDF e retorna análise jurídica completa"""
    
    print("\n" + "="*50)
    print("📥 NOVA REQUISIÇÃO RECEBIDA EM /analisar-documento")
    print("="*50)
    
    # Responder a requisições OPTIONS (preflight CORS)
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response, 200
    
    try:
        # Verificar se CoreEngineJuridico foi carregado
        if CoreEngineJuridico is None:
            print("❌ CoreEngineJuridico não foi carregado!")
            return jsonify({
                "success": False, 
                "error": "Erro interno: motor jurídico não carregado. Verifique logs."
            }), 500
        
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            print("❌ Nenhum arquivo enviado")
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        usuario_id = request.form.get('usuario_id', 'anonimo')
        
        print(f"📄 Arquivo: {file.filename}")
        print(f"👤 Usuário: {usuario_id}")
        print(f"📦 Tamanho: {len(file.read())} bytes")
        file.seek(0)  # Voltar ao início do arquivo
        
        # Validar arquivo
        if file.filename == '':
            return jsonify({"success": False, "error": "Nome de arquivo vazio"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Formato não suportado. Envie PDF."}), 400
        
        # Extrair texto do PDF
        print("🔍 Extraindo texto...")
        texto = extrair_texto_pdf_bytes(file.read())
        
        if not texto:
            return jsonify({"success": False, "error": "Não foi possível extrair texto do PDF"}), 400
        
        print(f"📝 Texto extraído: {len(texto)} caracteres")
        print(f"📝 Primeiros 200 caracteres: {texto[:200]}")
        
        # Inicializar detector jurídico
        print("⚖️ Inicializando CoreEngineJuridico...")
        detector = CoreEngineJuridico()
        print("✅ Detector inicializado")
        
        # Analisar documento
        print("🔬 Analisando documento...")
        resultado = detector.analisar_documento_completo(texto)
        
        print(f"✅ Análise concluída!")
        print(f"📊 Total de violações: {resultado['metricas']['total']}")
        print(f"🎯 Veredito: {resultado['veredito']}")
        
        return jsonify({
            "success": True,
            "resultado": resultado
        })
        
    except Exception as e:
        print(f"❌ ERRO NA ANÁLISE: {type(e).__name__}: {e}")
        print("📋 Traceback completo:")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": f"Erro interno: {type(e).__name__} - {str(e)}"
        }), 500

# ===== LISTAR ROTAS =====
print("\n📋 Rotas disponíveis:")
for rule in app.url_map.iter_rules():
    print(f"   {rule}")

# ===== INICIALIZAR =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Servidor iniciando na porta {port}")
    print("✅ Pronto para receber requisições!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
