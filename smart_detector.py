import re
from detection import Detector, limpar_texto
from learning_engine import LearningEngine

class SmartDetector:
    """
    Detector Inteligente que APRENDE com os erros
    - Usa o detector original
    - Detecta falhas na análise
    - Aprende novos padrões automaticamente
    - Melhora continuamente
    """
    
    def __init__(self):
        self.detector = Detector()
        self.learning_engine = LearningEngine()
        self.min_problems_threshold = 2  # Se encontrar menos que isso, pode ser falha
    
    def analisar_documento_inteligente(self, texto, user_feedback=None, force_learning=False):
        """
        Análise inteligente com aprendizado
        
        Args:
            texto: Texto do documento
            user_feedback: Feedback do usuário (opcional)
            force_learning: Força aprendizado mesmo se detectar problemas
        """
        
        # Análise original
        resultado_original = self.detector.analisar_documento(texto)
        
        # Detectar possível falha na análise
        potential_failure = self.detect_potential_failure(texto, resultado_original)
        
        if potential_failure or force_learning:
            print("[INTELIGENCIA] Possivel falha detectada - Iniciando aprendizado...")
            
            # Salvar falha para aprendizado
            failure_record, new_patterns = self.learning_engine.analyze_failure(
                texto, resultado_original, user_feedback
            )
            
            # Se encontrou novos padrões, refazer análise
            if new_patterns:
                print(f"[APRENDIZADO] {len(new_patterns)} novos padroes detectados!")
                resultado_aprimorado = self.analisar_com_padroes_aprendidos(texto, new_patterns)
                
                # Mesclar resultados
                resultado_final = self.mesclar_resultados(resultado_original, resultado_aprimorado)
                resultado_final["learning_info"] = {
                    "failure_detected": True,
                    "new_patterns": len(new_patterns),
                    "improved_analysis": True,
                    "learning_record": failure_record
                }
                
                return resultado_final
            else:
                resultado_original["learning_info"] = {
                    "failure_detected": True,
                    "new_patterns": 0,
                    "improved_analysis": False,
                    "learning_record": failure_record
                }
                
                return resultado_original
        
        # Análise normal sem detecção de falha
        resultado_original["learning_info"] = {
            "failure_detected": False,
            "new_patterns": 0,
            "improved_analysis": False
        }
        
        return resultado_original
    
    def detect_potential_failure(self, texto, resultado):
        """Detecta se a análise pode ter falhado"""
        
        # Critérios para detectar falha:
        
        # 1. Documento longo mas poucos problemas detectados
        if len(texto) > 2000 and resultado["total"] < self.min_problems_threshold:
            return True
        
        # 2. Documento parece ser contrato mas não detectou tipo correto
        texto_limpo = limpar_texto(texto).lower()
        contract_keywords = ["contrato", "cláusula", "acordo", "termo", "condições"]
        
        if any(keyword in texto_limpo for keyword in contract_keywords):
            if resultado["tipo_documento"] == "DESCONHECIDO":
                return True
        
        # 3. Documento menciona valores mas não detectou problemas financeiros
        financial_keywords = ["r$", "multa", "valor", "pagamento", "aluguel", "salário"]
        has_financial = any(keyword in texto_limpo for keyword in financial_keywords)
        
        if has_financial and resultado["total"] < 1:
            return True
        
        # 4. Score muito alto mas documento tem termos suspeitos
        suspicious_keywords = [
            "obrigatório", "proibido", "exclusivo", "irretratável", 
            "multa", "penalidade", "responsabilidade", "indenização"
        ]
        
        suspicious_count = sum(1 for keyword in suspicious_keywords if keyword in texto_limpo)
        
        if resultado["score"] > 80 and suspicious_count > 3:
            return True
        
        return False
    
    def analisar_com_padroes_aprendidos(self, texto, new_patterns):
        """Refaz análise usando padrões aprendidos"""
        
        problemas_adicionais = []
        texto_limpo = limpar_texto(texto)
        
        for pattern in new_patterns:
            try:
                if re.search(pattern["regex"], texto_limpo, re.IGNORECASE):
                    problema = {
                        "descricao": f"[APRENDIDO] {pattern['description']}",
                        "gravidade": pattern["severity"],
                        "lei": "Padrão aprendido automaticamente",
                        "detalhe": f"Detectado pela IA: {pattern['context'][:100]}...",
                        "tipo": "APRENDIDO",
                        "confidence": pattern.get("confidence", 0.8),
                        "pattern_id": pattern.get("pattern_type", "UNKNOWN")
                    }
                    problemas_adicionais.append(problema)
                    
            except Exception as e:
                print(f"Erro ao aplicar padrão aprendido: {e}")
        
        # Criar resultado aprimorado
        resultado_original = self.detector.analisar_documento(texto)
        
        # Adicionar problemas aprendidos (sem duplicação)
        descricoes_existentes = {p["descricao"] for p in resultado_original["problemas"]}
        
        for problema in problemas_adicionais:
            if problema["descricao"] not in descricoes_existentes:
                resultado_original["problemas"].append(problema)
        
        # Recalcular métricas
        resultado_original = self.recalcular_metricas(resultado_original)
        
        return resultado_original
    
    def mesclar_resultados(self, resultado_original, resultado_aprimorado):
        """Mescla resultado original com resultado aprimorado"""
        
        # Usar o aprimorado como base
        resultado_final = resultado_aprimorado.copy()
        
        # Adicionar informações do aprendizado
        resultado_final["original_problems"] = resultado_original["total"]
        resultado_final["improvement"] = resultado_aprimorado["total"] - resultado_original["total"]
        
        return resultado_final
    
    def recalcular_metricas(self, resultado):
        """Recalcula métricas baseado nos problemas"""
        
        problemas = resultado["problemas"]
        
        # Contar problemas por gravidade
        criticos = len([p for p in problemas if p["gravidade"] == "CRÍTICA"])
        altos = len([p for p in problemas if p["gravidade"] == "ALTA"])
        medios = len([p for p in problemas if p["gravidade"] == "MÉDIA"])
        baixos = len([p for p in problemas if p["gravidade"] == "BAIXA"])
        
        total = len(problemas)
        
        # Recalcular score
        score = 100
        for problema in problemas:
            if problema["gravidade"] == "CRÍTICA":
                score -= 20
            elif problema["gravidade"] == "ALTA":
                score -= 10
            elif problema["gravidade"] == "MÉDIA":
                score -= 5
            else:
                score -= 2
        
        score = max(0, score)
        
        # Recalcular status
        if criticos >= 3:
            status = "🚨🚨🚨 GRAVÍSSIMO - MÚLTIPLAS VIOLAÇÕES CRÍTICAS!"
            cor = "#8B0000"
            nivel_risco = "RISCO CRÍTICO"
        elif criticos >= 1:
            status = "🚨 VIOLAÇÕES SÉRIAS - CONSULTE UM ADVOGADO!"
            cor = "#FF4500"
            nivel_risco = "RISCO ELEVADO"
        elif altos >= 3:
            status = "⚠️ MÚLTIPLOS PROBLEMAS - REVISÃO URGENTE!"
            cor = "#FF8C00"
            nivel_risco = "RISCO ALTO"
        elif total > 0:
            status = "⚠️ PROBLEMAS DETECTADOS - REVISE COM CUIDADO"
            cor = "#FFD700"
            nivel_risco = "RISCO MODERADO"
        else:
            status = "✅ DOCUMENTO APARENTEMENTE REGULAR"
            cor = "#27AE60"
            nivel_risco = "BAIXO RISCO"
        
        # Atualizar resultado
        resultado.update({
            "total": total,
            "criticos": criticos,
            "altos": altos,
            "medios": medios,
            "info": baixos,
            "score": round(score, 1),
            "status": status,
            "cor": cor,
            "nivel_risco": nivel_risco
        })
        
        return resultado
    
    def treinar_com_contratos_existentes(self, pasta_contratos):
        """Treina a IA com contratos existentes"""
        
        import os
        import pdfplumber
        
        print("[TREINAMENTO] Iniciando treinamento com contratos existentes...")
        
        contratos = [
            'CONTRATO DE EMPREGO 1.pdf',
            'CONTRATO DE EMPREGO 2.pdf', 
            'CONTRATO DE EMPREGO 3.pdf',
            'CONTRATO DE LOCAÇÃO 2.pdf',
            'CONTRATO DE LOCAÇÃO 3.pdf',
            'CONTRATOS DE LOCAÇÃO COM ARMADILHAS.pdf',
            'Contrato de Locação Residencial.pdf'
        ]
        
        caminho_base = pasta_contratos
        
        for contrato in contratos:
            caminho_completo = os.path.join(caminho_base, contrato)
            
            try:
                # Extrair texto
                texto = ""
                with pdfplumber.open(caminho_completo) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            texto += page_text + "\n"
                
                if texto:
                    print(f"[TREINAMENTO] Analisando: {contrato}")
                    
                    # Forçar aprendizado
                    resultado = self.analisar_documento_inteligente(
                        texto, 
                        user_feedback="Treinamento automatico",
                        force_learning=True
                    )
                    
                    print(f"   Problemas detectados: {resultado['total']}")
                    print(f"   [APRENDIZADO] Padroes aprendidos: {resultado['learning_info']['new_patterns']}")
                    
            except Exception as e:
                print(f"ERRO ao processar {contrato}: {e}")
        
        # Mostrar resumo do aprendizado
        summary = self.learning_engine.get_learning_summary()
        print(f"\n[RESUMO DO TREINAMENTO]")
        print(f"   Total analisado: {summary['total_analyzed']}")
        print(f"   Falhas detectadas: {summary['failures_detected']}")
        print(f"   Padroes aprendidos: {summary['patterns_learned']}")
        print(f"   Taxa de aprendizado: {summary['learning_rate']:.2%}")
        
        # Sugestões de melhoria
        suggestions = self.learning_engine.suggest_improvements()
        if suggestions:
            print(f"\n[SUGESTOES DE MELHORIA]")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
    
    def get_learning_status(self):
        """Retorna status do aprendizado"""
        return self.learning_engine.get_learning_summary()
