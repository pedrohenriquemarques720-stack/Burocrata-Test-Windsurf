"""
Módulo de análise de documentos do Burocrata de Bolso
"""
import re
from typing import List, Dict, Tuple, Optional
from utils import limpar_texto

class SistemaDetecção:
    """Sistema especializado em detecção de problemas jurídicos"""
    
    def __init__(self):
        self.padroes = self._carregar_padroes()
        self.indicadores_tipo = self._carregar_indicadores_tipo()
        self.violacoes_numeradas = self._carregar_violacoes_numeradas()
    
    def _carregar_padroes(self) -> Dict:
        """Carrega padrões de detecção para cada tipo de documento"""
        return {
            'CONTRATO_LOCACAO': {
                'nome': 'Contrato de Locação',
                'padroes': [
                    {
                        'regex': r'multa.*correspondente.*12.*meses.*aluguel|multa.*12.*meses|doze.*meses.*aluguel|multa.*integral.*12.*meses',
                        'descricao': '🚨🚨🚨 MULTA DE 12 MESES DE ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º: Multa máxima = 2 meses de aluguel',
                        'detalhe': 'A lei do inquilinato PROÍBE multas superiores a 2 meses de aluguel.'
                    },
                    {
                        'regex': r'depósito.*caução.*três.*meses|caução.*3.*meses|três.*meses.*aluguel.*caução|3.*meses.*depósito|caução.*excessiva',
                        'descricao': '🚨🚨 CAUÇÃO DE 3 MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37: Caução máxima = 1 mês de aluguel',
                        'detalhe': 'Limite legal é apenas 1 mês de aluguel como caução.'
                    },
                    {
                        'regex': r'reajuste.*trimestral|reajuste.*a.*cada.*3.*meses|reajuste.*mensalmente|reajuste.*mensal|aumento.*mensal',
                        'descricao': '🚨 REAJUSTE TRIMESTRAL/MENSAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º: Reajuste mínimo anual (12 meses)',
                        'detalhe': 'Reajustes só podem ser feitos a cada 12 meses no mínimo.'
                    }
                ]
            },
            'CONTRATO_TRABALHO': {
                'nome': 'Contrato de Trabalho',
                'padroes': [
                    {
                        'regex': r'salário.*mensal.*bruto.*R\$\s*900|R\$\s*900[,\.]00|900.*reais|novecentos.*reais|salário.*R\$\s*800|800.*reais',
                        'descricao': '🚨🚨🚨 SALÁRIO ABAIXO DO MÍNIMO - TRABALHO ESCRAVO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º IV',
                        'detalhe': f'Salário mínimo atual (2024): R$ 1.412,00. R$ 900 é 36% ABAIXO! R$ 800 é 43% ABAIXO!'
                    },
                    {
                        'regex': r'jornada.*das\s*08:00.*às\s*20:00|08:00.*20:00|das\s*08.*às\s*20|jornada.*60.*horas.*semanais|60.*horas.*semanais',
                        'descricao': '🚨🚨 JORNADA EXCESSIVA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58: Máximo 8h diárias / 44h semanais',
                        'detalhe': '12h diárias = 50% ACIMA do limite! 60h semanais = 36% ACIMA do limite de 44h!'
                    }
                ]
            },
            'NOTA_FISCAL': {
                'nome': 'Nota Fiscal',
                'padroes': [
                    {
                        'regex': r'Nota.*Fiscal|NFSe|NF-e|NFS-e',
                        'descricao': '📄 NOTA FISCAL IDENTIFICADA',
                        'gravidade': 'INFO',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Documento fiscal para prestação de serviços'
                    }
                ]
            }
        }
    
    def _carregar_indicadores_tipo(self) -> Dict:
        """Carrega indicadores para detecção rápida de tipo"""
        return {
            'CONTRATO_LOCACAO': [
                'locação', 'aluguel', 'locador', 'locatário', 'imóvel residencial',
                'caução', 'fiador', 'benfeitorias', 'multa rescisória', 'inquilino',
                'proprietário', 'Lei 8.245/1991', 'Lei do Inquilinato'
            ],
            'CONTRATO_TRABALHO': [
                'empregador', 'empregado', 'CLT', 'salário', 'jornada',
                'horas extras', 'FGTS', 'férias', '13º salário', 'funcionário',
                'trabalhador', 'contrato de trabalho', 'carteira de trabalho'
            ],
            'NOTA_FISCAL': [
                'nota fiscal', 'nfse', 'nfe', 'prefeitura municipal',
                'prestador de serviços', 'tomador de serviços', 'iss', 'imposto'
            ]
        }
    
    def _carregar_violacoes_numeradas(self) -> List[Tuple]:
        """Carrega padrões para violações numeradas"""
        return [
            (r'Viol.*1.*:', 'VIOLACAO_1', '🚨 VIOLAÇÃO 1 À CLT', 'CRÍTICA'),
            (r'Viol.*2.*:', 'VIOLACAO_2', '🚨 VIOLAÇÃO 2 À CLT', 'CRÍTICA'),
            (r'Viol.*3.*:', 'VIOLACAO_3', '🚨 VIOLAÇÃO 3 À CLT', 'CRÍTICA'),
        ]
    
    def detectar_tipo_documento(self, texto: str) -> str:
        """Detecção precisa do tipo de documento"""
        if not texto:
            return 'DESCONHECIDO'
        
        texto_limpo = limpar_texto(texto).lower()
        
        # Verificação direta por termos chave
        if 'nota fiscal' in texto_limpo or 'nfse' in texto_limpo or 'nfe' in texto_limpo:
            return 'NOTA_FISCAL'
        
        if 'empregador' in texto_limpo and 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        
        if 'locação' in texto_limpo or ('locador' in texto_limpo and 'locatário' in texto_limpo):
            return 'CONTRATO_LOCACAO'
        
        # Contagem de termos
        scores = {}
        for doc_type, termos in self.indicadores_tipo.items():
            score = sum(1 for termo in termos if termo.lower() in texto_limpo)
            scores[doc_type] = score
        
        # Escolher o tipo com maior score
        if scores:
            tipo_detectado = max(scores.items(), key=lambda x: x[1])
            if tipo_detectado[1] > 0:
                return tipo_detectado[0]
        
        return 'DESCONHECIDO'
    
    def analisar_documento(self, texto: str) -> Tuple[List[Dict], str, Dict]:
        """Análise completa do documento"""
        if not texto or len(texto) < 50:
            return [], 'DESCONHECIDO', self._calcular_metricas([])
        
        texto_limpo = limpar_texto(texto).lower()
        problemas = []
        
        # Determinar tipo de documento
        tipo_doc = self.detectar_tipo_documento(texto_limpo)
        
        # Análise específica por tipo
        if tipo_doc in self.padroes:
            for padrao in self.padroes[tipo_doc]['padroes']:
                try:
                    if re.search(padrao['regex'], texto_limpo, re.IGNORECASE | re.DOTALL):
                        problemas.append({
                            'tipo': self.padroes[tipo_doc]['nome'],
                            'problema_id': padrao['regex'][:50],
                            'descricao': padrao['descricao'],
                            'detalhe': padrao['detalhe'],
                            'lei': padrao['lei'],
                            'gravidade': padrao['gravidade'],
                            'posicao': 0
                        })
                except:
                    continue
        
        # Remover duplicatas
        problemas_unicos = []
        problemas_vistos = set()
        for problema in problemas:
            chave = (problema['descricao'], problema['lei'])
            if chave not in problemas_vistos:
                problemas_vistos.add(chave)
                problemas_unicos.append(problema)
        
        return problemas_unicos, tipo_doc, self._calcular_metricas(problemas_unicos)
    
    def _calcular_metricas(self, problemas: List[Dict]) -> Dict:
        """Calcula métricas da análise"""
        total = len(problemas)
        criticos = sum(1 for p in problemas if 'CRÍTICA' in p.get('gravidade', ''))
        altos = sum(1 for p in problemas if 'ALTA' in p.get('gravidade', ''))
        medios = sum(1 for p in problemas if 'MÉDIA' in p.get('gravidade', ''))
        info = sum(1 for p in problemas if 'INFO' in p.get('gravidade', ''))
        
        # Cálculo do score
        score = 100
        score -= criticos * 40
        score -= altos * 25
        score -= medios * 10
        score = max(0, min(100, score))
        
        # Status e nível de risco
        if criticos >= 3:
            status = '🚨🚨🚨 DOCUMENTO CRIMINOSO - NÃO ASSINE!'
            cor = '#FF0000'
            nivel_risco = 'RISCO MÁXIMO'
        elif criticos >= 1:
            status = '🚨🚨 MÚLTIPLAS VIOLAÇÕES GRAVES - PERIGO!'
            cor = '#FF4500'
            nivel_risco = 'ALTO RISCO'
        elif altos >= 2:
            status = '🚨 VIOLAÇÕES SÉRIAS - CONSULTE UM ADVOGADO!'
            cor = '#FF8C00'
            nivel_risco = 'RISCO ELEVADO'
        elif total > 0:
            status = '⚠️ PROBLEMAS DETECTADOS - REVISE COM CUIDADO'
            cor = '#FFD700'
            nivel_risco = 'RISCO MODERADO'
        else:
            status = '✅ DOCUMENTO APARENTEMENTE REGULAR'
            cor = '#27AE60'
            nivel_risco = 'BAIXO RISCO'
        
        return {
            'total': total,
            'criticos': criticos,
            'altos': altos,
            'medios': medios,
            'info': info,
            'score': round(score, 1),
            'status': status,
            'cor': cor,
            'nivel_risco': nivel_risco
        }
