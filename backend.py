from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import io
import pdfplumber
from datetime import datetime
from dotenv import load_dotenv

# Importar o Core Engine Jurídico
from core_juridico import CoreEngineJuridico

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")  # Permite requisições de qualquer origem

# Configurações
ABACATE_API_KEY = os.getenv('ABACATE_API_KEY', '')
ABACATE_WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', '')
APP_URL = os.getenv('APP_URL', 'https://burocrata-backend.onrender.com')

print("🚀 Servidor Burocrata iniciando...")
print(f"📡 Servidor rodando em: {APP_URL}")

# ===== FUNÇÃO AUXILIAR PARA EXTRAIR TEXTO DO PDF =====
def extrair_texto_pdf_bytes(bytes_pdf):
    """Extrai texto de bytes de PDF"""
    try:
        with pdfplumber.open(io.BytesIO(bytes_pdf)) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        print(f"❌ Erro ao extrair PDF: {e}")
        return None

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "payment": "AbacatePay integrado",
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate",
        "api_key_configured": bool(ABACATE_API_KEY),
        "rotas_disponiveis": ["/", "/ping", "/analisar-documento"]
    })

# ===== ROTA DE TESTE (PING) =====
@app.route('/ping')
def ping():
    return jsonify({
        "pong": True,
        "timestamp": datetime.now().isoformat(),
        "status": "online"
    })

# ===== ROTA PARA ANÁLISE JURÍDICA =====
@app.route('/analisar-documento', methods=['POST', 'OPTIONS'])
def analisar_documento():
    """Recebe um PDF e retorna análise jurídica completa"""
    
    # Responder a requisições OPTIONS (preflight CORS)
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response, 200
    
    print("📥 Requisição recebida em /analisar-documento")
    print(f"📌 Método: {request.method}")
    
    try:
        # Verificar se arquivo foi enviado
        if 'file' not in request.files:
            print("❌ Erro: Nenhum arquivo enviado")
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        usuario_id = request.form.get('usuario_id', 'anonimo')
        
        print(f"📄 Arquivo recebido: {file.filename}")
        print(f"👤 Usuário ID: {usuario_id}")
        
        # Validar arquivo
        if file.filename == '':
            return jsonify({"success": False, "error": "Nome de arquivo vazio"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Formato não suportado. Envie PDF."}), 400
        
        # Extrair texto do PDF
        print("🔍 Extraindo texto do PDF...")
        texto = extrair_texto_pdf_bytes(file.read())
        
        if not texto:
            return jsonify({"success": False, "error": "Não foi possível extrair texto do PDF"}), 400
        
        print(f"📝 Texto extraído: {len(texto)} caracteres")
        
        # Inicializar detector jurídico
        print("⚖️ Inicializando CoreEngineJuridico...")
        detector = CoreEngineJuridico()
        
        # Analisar documento
        print("🔬 Analisando documento...")
        resultado = detector.analisar_documento_completo(texto)
        
        print(f"✅ Análise concluída! {resultado['metricas']['total']} violações encontradas")
        print(f"🎯 Veredito: {resultado['veredito']}")
        
        return jsonify({
            "success": True,
            "resultado": resultado
        })
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

# ===== LISTAR TODAS AS ROTAS DISPONÍVEIS =====
print("\n📋 Rotas disponíveis:")
for rule in app.url_map.iter_rules():
    print(f"   {rule}")

# ===== INICIALIZAR SERVIDOR =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('ENV') != 'production'
    
    print(f"\n🚀 Servidor iniciando na porta {port}")
    print(f"🌐 Modo: {'Produção' if not debug_mode else 'Desenvolvimento'}")
    print("✅ Pronto para receber requisições!\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
