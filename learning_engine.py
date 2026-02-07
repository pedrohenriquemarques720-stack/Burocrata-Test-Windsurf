import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
import pdfplumber

class LearningEngine:
    """
    Inteligência Artificial que APRENDE com os erros do Burocrata
    - Detecta falhas na análise
    - Salva documentos para estudo
    - Extrai novos padrões automaticamente
    - Melhora o sistema continuamente
    """
    
    def __init__(self):
        self.learning_db = "learning_database.json"
        self.documents_folder = "learning_documents"
        self.patterns_history = "patterns_history.json"
        
        # Criar pastas se não existirem
        os.makedirs(self.documents_folder, exist_ok=True)
        
        # Carregar base de aprendizado
        self.load_learning_database()
    
    def load_learning_database(self):
        """Carrega base de dados de aprendizado"""
        try:
            with open(self.learning_db, 'r', encoding='utf-8') as f:
                self.learning_data = json.load(f)
        except:
            self.learning_data = {
                "failed_analyses": [],
                "learned_patterns": [],
                "improved_detections": [],
                "statistics": {
                    "total_analyzed": 0,
                    "failures_detected": 0,
                    "patterns_learned": 0,
                    "accuracy_improved": 0
                }
            }
    
    def save_learning_database(self):
        """Salva base de dados de aprendizado"""
        with open(self.learning_db, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
    
    def analyze_failure(self, document_text: str, original_result: Dict, user_feedback: str = None):
        """
        Analisa uma falha na detecção e aprende com ela
        
        Args:
            document_text: Texto do documento
            original_result: Resultado original da análise
            user_feedback: Feedback do usuário (opcional)
        """
        
        failure_record = {
            "timestamp": datetime.now().isoformat(),
            "document_type": original_result.get("tipo_documento", "DESCONHECIDO"),
            "original_problems": len(original_result.get("problemas", [])),
            "original_score": original_result.get("score", 100),
            "user_feedback": user_feedback,
            "document_length": len(document_text),
            "suspicious_terms": self.extract_suspicious_terms(document_text),
            "potential_patterns": self.identify_potential_patterns(document_text)
        }
        
        # Salvar documento para estudo futuro
        doc_filename = f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        doc_path = os.path.join(self.documents_folder, doc_filename)
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(f"DOCUMENTO: {failure_record['timestamp']}\n")
            f.write(f"TIPO DETECTADO: {failure_record['document_type']}\n")
            f.write(f"PROBLEMAS: {failure_record['original_problems']}\n")
            f.write(f"SCORE: {failure_record['original_score']}\n")
            f.write(f"FEEDBACK: {user_feedback}\n")
            f.write("=" * 80 + "\n")
            f.write(document_text)
        
        failure_record["document_path"] = doc_path
        
        # Adicionar à base de aprendizado sempre que for chamado
        self.learning_data["failed_analyses"].append(failure_record)
        self.learning_data["statistics"]["failures_detected"] += 1
        
        # Tentar aprender novos padrões
        new_patterns = self.extract_new_patterns(document_text, failure_record)
        if new_patterns:
            self.learning_data["learned_patterns"].extend(new_patterns)
            self.learning_data["statistics"]["patterns_learned"] += len(new_patterns)
        
        # Salvar aprendizado
        self.save_learning_database()
        
        return failure_record, new_patterns
    
    def extract_suspicious_terms(self, text: str) -> List[str]:
        """Extrai termos suspeitos que poderiam indicar problemas não detectados"""
        
        suspicious_keywords = [
            # Trabalho
            "salário", "horas", "jornada", "adicional", "extra", "fgts", "férias", "13º",
            "contrato", "empregador", "empregado", "clt", "rescisão", "multa", "aviso prévio",
            
            # Locação
            "aluguel", "locador", "locatário", "multa", "caução", "fiador", "reajuste",
            "visita", "benfeitorias", "despejo", "rescisão", "imóvel", "imobiliária",
            
            # Financeiro
            "r$", "valor", "pagamento", "multa", "juros", "correção", "índice", "inflação",
            
            # Legal
            "lei", "artigo", "cláusula", "contrato", "acordo", "termo", "condição",
            
            # Problemáticos
            "obrigatório", "proibido", "vedado", "exclusivo", "irretratável", "definitivo"
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for keyword in suspicious_keywords:
            if keyword in text_lower:
                # Encontrar contexto ao redor do termo
                pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                found_terms.extend(matches[:3])  # Limitar para não poluir
        
        return list(set(found_terms))
    
    def identify_potential_patterns(self, text: str) -> List[Dict]:
        """Identifica padrões potenciais que não foram detectados"""
        
        patterns = []
        
        # Procurar por números com contextos suspeitos
        number_patterns = [
            (r'(\d+)\s*meses.*multa', "MULTA_MESES", "Multa com X meses"),
            (r'multa.*(\d+)\s*meses', "MULTA_MESES_INVERSO", "Multa de X meses"),
            (r'(\d+)\s*horas.*dia|jornada.*(\d+)\s*horas', "JORNADA_HORAS", "Jornada de X horas"),
            (r'(\d+)\s*horas.*semana|semanal.*(\d+)\s*horas', "JORNADA_SEMANAL", "Jornada de X horas semanais"),
            (r'r\$\s*(\d+[.,]?\d*)', "VALOR_RS", "Valor em reais"),
            (r'(\d+)%.*multa|multa.*(\d+)%', "MULTA_PERCENTUAL", "Multa de X%"),
            (r'(\d+)\s*minutos.*intervalo|intervalo.*(\d+)\s*minutos', "INTERVALO_MINUTOS", "Intervalo de X minutos")
        ]
        
        for pattern, pattern_type, description in number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        match = [m for m in match if m][0]  # Pegar primeiro não vazio
                    
                    patterns.append({
                        "type": pattern_type,
                        "description": description,
                        "value": match,
                        "context": self.get_context(text, match),
                        "confidence": self.calculate_confidence(pattern_type, match)
                    })
        
        return patterns
    
    def extract_new_patterns(self, text: str, failure_record: Dict) -> List[Dict]:
        """Extrai novos padrões baseados na falha"""
        
        new_patterns = []
        
        # Se o documento parece ser um contrato mas não detectou problemas
        if failure_record["original_problems"] < 3:
            suspicious_patterns = self.identify_potential_patterns(text)
            
            for pattern in suspicious_patterns:
                if pattern["confidence"] > 0.7:  # Alta confiança
                    new_pattern = {
                        "timestamp": datetime.now().isoformat(),
                        "pattern_type": pattern["type"],
                        "description": pattern["description"],
                        "regex": self.create_regex_from_pattern(pattern),
                        "severity": self.infer_severity(pattern),
                        "source_document": failure_record["document_path"],
                        "confidence": pattern["confidence"],
                        "context": pattern["context"]
                    }
                    
                    new_patterns.append(new_pattern)
        
        return new_patterns
    
    def create_regex_from_pattern(self, pattern: Dict) -> str:
        """Cria regex a partir do padrão identificado"""
        
        base_patterns = {
            "MULTA_MESES": r'multa.*{value}.*meses|{value}.*meses.*multa',
            "JORNADA_HORAS": r'jornada.*{value}.*horas|{value}.*horas.*jornada',
            "JORNADA_SEMANAL": r'jornada.*{value}.*horas.*semanal|{value}.*horas.*semanais',
            "VALOR_RS": r'r\$\s*{value}',
            "MULTA_PERCENTUAL": r'multa.*{value}%|{value}%.*multa',
            "INTERVALO_MINUTOS": r'intervalo.*{value}.*minutos|{value}.*minutos.*intervalo'
        }
        
        pattern_type = pattern["type"]
        value = pattern["value"]
        
        if pattern_type in base_patterns:
            return base_patterns[pattern_type].format(value=re.escape(value))
        
        # Padrão genérico
        return re.escape(value)
    
    def infer_severity(self, pattern: Dict) -> str:
        """Infere a gravidade do padrão"""
        
        severity_rules = {
            "MULTA_MESES": "CRÍTICA" if int(pattern["value"]) > 2 else "ALTA",
            "JORNADA_HORAS": "CRÍTICA" if int(pattern["value"]) > 8 else "ALTA",
            "JORNADA_SEMANAL": "CRÍTICA" if int(pattern["value"]) > 44 else "ALTA",
            "VALOR_RS": "CRÍTICA" if float(pattern["value"].replace(',', '.')) < 1500 else "MEDIA",
            "MULTA_PERCENTUAL": "CRÍTICA" if float(pattern["value"]) > 10 else "ALTA",
            "INTERVALO_MINUTOS": "CRÍTICA" if int(pattern["value"]) < 30 else "ALTA"
        }
        
        return severity_rules.get(pattern["type"], "MEDIA")
    
    def calculate_confidence(self, pattern_type: str, value: str) -> float:
        """Calcula confiança do padrão"""
        
        try:
            num_value = float(value.replace(',', '.'))
            
            confidence_rules = {
                "MULTA_MESES": 0.9 if num_value > 3 else 0.7,
                "JORNADA_HORAS": 0.9 if num_value > 8 else 0.6,
                "JORNADA_SEMANAL": 0.9 if num_value > 44 else 0.6,
                "VALOR_RS": 0.8 if num_value < 1500 else 0.5,
                "MULTA_PERCENTUAL": 0.8 if num_value > 5 else 0.6,
                "INTERVALO_MINUTOS": 0.9 if num_value < 45 else 0.6
            }
            
            return confidence_rules.get(pattern_type, 0.5)
            
        except:
            return 0.5
    
    def get_context(self, text: str, value: str) -> str:
        """Pega contexto ao redor do valor"""
        
        pattern = rf'.{{0,100}}{re.escape(value)}.{{0,100}}'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        return ""
    
    def get_learning_summary(self) -> Dict:
        """Retorna resumo do aprendizado"""
        
        stats = self.learning_data["statistics"]
        
        return {
            "total_analyzed": stats["total_analyzed"],
            "failures_detected": stats["failures_detected"],
            "patterns_learned": stats["patterns_learned"],
            "accuracy_improved": stats["accuracy_improved"],
            "recent_failures": len([f for f in self.learning_data["failed_analyses"] 
                                 if f["timestamp"] > "2026-02-07"]),
            "learning_rate": stats["patterns_learned"] / max(1, stats["failures_detected"])
        }
    
    def suggest_improvements(self) -> List[str]:
        """Sugere melhorias baseadas no aprendizado"""
        
        suggestions = []
        
        # Analisar falhas recentes
        recent_failures = [f for f in self.learning_data["failed_analyses"] 
                          if f["timestamp"] > "2026-02-07"]
        
        if recent_failures:
            # Tipos de documento com mais falhas
            doc_types = {}
            for failure in recent_failures:
                doc_type = failure["document_type"]
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            most_failed = max(doc_types.items(), key=lambda x: x[1])
            suggestions.append(f"Focar em melhorar detecção para {most_failed[0]} ({most_failed[1]} falhas)")
            
            # Padrões comuns não detectados
            common_patterns = {}
            for failure in recent_failures:
                for pattern in failure.get("potential_patterns", []):
                    pattern_type = pattern["type"]
                    common_patterns[pattern_type] = common_patterns.get(pattern_type, 0) + 1
            
            if common_patterns:
                most_common = max(common_patterns.items(), key=lambda x: x[1])
                suggestions.append(f"Adicionar padrões para {most_common[0]} ({most_common[1]} ocorrências)")
        
        return suggestions
