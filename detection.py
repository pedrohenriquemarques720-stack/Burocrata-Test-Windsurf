import re
from utils import limpar_texto

class Detector:
    """Sistema de detecção de problemas jurídicos - VERSÃO 2.0"""
    
    def __init__(self):
        # Padrões EXTREMAMENTE específicos e abrangentes - ATUALIZADO 2024
        self.padroes = {
            'CONTRATO_LOCACAO': {
                'nome': 'Contrato de Locação',
                'padroes': [
                    # MULTAS - CRÍTICAS
                    {
                        'regex': r'multa.*correspondente.*12.*meses.*aluguel|multa.*12.*meses|doze.*meses.*aluguel|multa.*integral.*12.*meses|multa.*ano.*inteiro|multa.*período.*restante',
                        'descricao': '🚨🚨🚨 MULTA DE 12 MESES DE ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º: Multa máxima = 2 meses de aluguel',
                        'detalhe': 'A lei do inquilinato PROÍBE multas superiores a 2 meses de aluguel. Multa de 12 meses é ABUSIVA e NULA!'
                    },
                    {
                        'regex': r'multa.*superior.*2.*meses|multa.*excedente.*2.*meses|multa.*acima.*2.*meses|multa.*maior.*2.*meses',
                        'descricao': '🚨 MULTA ACIMA DE 2 MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º',
                        'detalhe': 'Multa rescisória não pode exceder 2 meses de aluguel, mesmo que proporcional.'
                    },
                    {
                        'regex': r'multa.*não.*proporcional|multa.*integral.*independentemente.*tempo|multa.*fixa.*sem.*proporcionalidade',
                        'descricao': '🚨 MULTA SEM PROPORCIONALIDADE - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º + Súmula 595 STJ',
                        'detalhe': 'Multa deve ser proporcional ao tempo cumprido do contrato.'
                    },
                    
                    # CAUÇÃO - CRÍTICAS
                    {
                        'regex': r'depósito.*caução.*três.*meses|caução.*3.*meses|três.*meses.*aluguel.*caução|3.*meses.*depósito|caução.*excessiva|caução.*superior.*1.*mês',
                        'descricao': '🚨🚨 CAUÇÃO DE 3 MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37: Caução máxima = 1 mês de aluguel',
                        'detalhe': 'Limite legal é apenas 1 mês de aluguel como caução. 3 meses é TRIPLO do permitido!'
                    },
                    {
                        'regex': r'caução.*superior.*um.*mês|caução.*maior.*1.*mês|depósito.*maior.*1.*mês',
                        'descricao': '🚨 CAUÇÃO ACIMA DE 1 MÊS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37',
                        'detalhe': 'Caução não pode exceder 1 mês de aluguel.'
                    },
                    
                    # REAJUSTE - CRÍTICOS
                    {
                        'regex': r'reajuste.*trimestral|reajuste.*a.*cada.*3.*meses|reajuste.*mensalmente|reajuste.*mensal|aumento.*mensal|reajuste.*bimestral',
                        'descricao': '🚨 REAJUSTE TRIMESTRAL/MENSAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º: Reajuste mínimo anual (12 meses)',
                        'detalhe': 'Reajustes só podem ser feitos a cada 12 meses no mínimo. Reajuste trimestral é 4x mais frequente que o permitido!'
                    },
                    {
                        'regex': r'reajuste.*sem.*índice.*oficial|reajuste.*livre|reajuste.*conforme.*mercado|reajuste.*acordo|índice.*livre',
                        'descricao': '🚨 REAJUSTE SEM ÍNDICE OFICIAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices oficiais (IGPM, INCC, IPCA). Índice livre é abusivo.'
                    },
                    {
                        'regex': r'reajuste.*dólar|reajuste.*variação.*dólar|reajuste.*câmbio',
                        'descricao': '🚨🚨 REAJUSTE PELO DÓLAR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices brasileiros, NÃO o dólar. Variação cambial é proibida!'
                    },
                    {
                        'regex': r'aumento.*fixo.*20%.*ano|20%.*ao.*ano.*fixo|percentual.*fixo.*20%',
                        'descricao': '🚨 AUMENTO FIXO DE 20% AO ANO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Percentuais fixos não seguem inflação oficial. Deve usar índices oficiais.'
                    },
                    
                    # VISITAS E PRIVACIDADE - CRÍTICOS
                    {
                        'regex': r'visitas.*qualquer.*tempo.*sem.*aviso|visitas.*sem.*aviso.*prévio|visitas.*a.*qualquer.*momento|entrar.*qualquer.*hora.*sem.*aviso|ingresso.*imediato.*imóvel',
                        'descricao': '🚨🚨 VISITAS SEM AVISO - VIOLAÇÃO DE DOMICÍLIO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991 Art. 23 + Código Penal Art. 150',
                        'detalhe': 'Locador deve avisar com antecedência mínima de 12 horas. Entrar sem aviso pode configurar crime de violação de domicílio!'
                    },
                    {
                        'regex': r'ingressar.*imóvel.*qualquer.*momento.*sem.*aviso|acesso.*livre.*imóvel|chave.*disponível.*locador',
                        'descricao': '🚨 INGRESSO LIVRE NO IMÓVEL - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Penal Art. 150 + CDC Art. 51',
                        'detalhe': 'Locatário tem direito à intimidade. Acesso livre do locador é crime de violação de domicílio!'
                    },
                    {
                        'regex': r'vistorias.*surpresa|vistorias.*sem.*aviso|inspeção.*surpresa',
                        'descricao': '⚠️ VISTORIAS SURPRESA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991',
                        'detalhe': 'Vistorias exigem aviso prévio mínimo de 12 horas.'
                    },
                    
                    # BENFEITORIAS - CRÍTICAS
                    {
                        'regex': r'renúncia.*indenização.*benfeitorias.*necessárias|benfeitorias.*necessárias.*sem.*indenização|renúncia.*retensão.*benfeitorias|abrir.*mão.*benfeitorias',
                        'descricao': '🚨🚨 RENÚNCIA A BENFEITORIAS NECESSÁRIAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 35 + Lei 8.245/1991',
                        'detalhe': 'Locatário tem direito à indenização por benfeitorias necessárias. Cláusula é NULA!'
                    },
                    {
                        'regex': r'benfeitorias.*sem.*direito.*indenização|benfeitorias.*não.*indenizáveis|improvements.*não.*pagos',
                        'descricao': '🚨 BENFEITORIAS SEM INDENIZAÇÃO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 35',
                        'detalhe': 'Benfeitorias úteis e necessárias devem ser indenizadas.'
                    },
                    
                    # ANIMAIS - ALTO
                    {
                        'regex': r'vedada.*permanência.*animais|proibido.*animais.*estimação|não.*permitido.*animais|animais.*proibidos|pets.*não.*permitidos',
                        'descricao': '⚠️ PROIBIÇÃO DE ANIMAIS - CLAUSULA ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51: Cláusulas abusivas são nulas',
                        'detalhe': 'Proibição total de animais pode ser considerada abusiva e nula. Deve analisar caso a caso.'
                    },
                    
                    # VENDA DO IMÓVEL - ALTO
                    {
                        'regex': r'contrato.*automaticamente.*resciso.*venda|venda.*imóvel.*contrato.*rescindido|retomada.*48.*horas.*venda|venda.*fim.*contrato',
                        'descricao': '⚠️ RESCISÃO AUTOMÁTICA POR VENDA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 9º: Contrato segue para novo proprietário',
                        'detalhe': 'Na venda do imóvel, o contrato continua com o novo proprietário. Prazo de desocupação mínimo é de 30 dias.'
                    },
                    {
                        'regex': r'desocupação.*imediata.*venda|despejo.*imediato.*venda|saída.*30.*dias.*venda',
                        'descricao': '🚨 PRAZO DE DESOCUPAÇÃO INFERIOR A 30 DIAS - ILEGAL',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 9º',
                        'detalhe': 'Prazo mínimo para desocupação em caso de venda é 30 dias.'
                    },
                    
                    # FIADORES - MÉDIO
                    {
                        'regex': r'fiadores.*com.*renda.*comprovada|exigência.*fiador|obrigatoriedade.*fiador',
                        'descricao': '⚠️ EXIGÊNCIA DE FIADORES - PODE SER ABUSIVA',
                        'gravidade': 'MÉDIA',
                        'lei': 'CDC Art. 51 + Jurisprudência',
                        'detalhe': 'Exigência de fiadores pode ser substituída por seguro fiança.'
                    },
                    
                    # RESPONSABILIDADE ESTRUTURAL - CRÍTICA
                    {
                        'regex': r'locatário.*assume.*responsabilidade.*estrutural|dano.*estrutural.*locatário|reparos.*estruturais.*locatário|fundação.*locatário|telhado.*locatário',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR ESTRUTURA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22: Despesas com estrutura são do locador',
                        'detalhe': 'Telhado, fundação, fiação central e tubulações são responsabilidade do LOCADOR!'
                    },
                    {
                        'regex': r'locatário.*responsável.*vícios.*construção|vícios.*ocultos.*locatário|defeitos.*estrutura.*locatário',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR VÍCIOS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22',
                        'detalhe': 'Vícios construtivos e defeitos ocultos são responsabilidade do locador.'
                    },
                    
                    # PAGAMENTO ANTECIPADO - ALTO
                    {
                        'regex': r'pagamento.*antecipado.*mês.*vencer|aluguel.*primeiro.*dia.*mês|pagamento.*adiantado.*obrigatório',
                        'descricao': '⚠️ PAGAMENTO ANTECIPADO OBRIGATÓRIO - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 3º',
                        'detalhe': 'Pagamento antecipado só é permitido em locações SEM garantia.'
                    },
                    
                    # IMPOSTO DE RENDA - CRÍTICO
                    {
                        'regex': r'locatário.*pagar.*imposto.*renda.*locador|imposto.*renda.*locatário.*pagar|IR.*locatário.*responsável',
                        'descricao': '🚨🚨 LOCATÁRIO PAGANDO IR DO LOCADOR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Lei Tributária',
                        'detalhe': 'Imposto de Renda é encargo PESSOAL do contribuinte (locador). Transferência é ilegal!'
                    },
                    
                    # DESPEJO - CRÍTICO
                    {
                        'regex': r'despejo.*imediato.*atrasar.*1.*dia|trocar.*fechaduras.*atraso|despejo.*24.*horas|despejo.*48.*horas',
                        'descricao': '🚨🚨 DESPEJO IMEDIATO POR 1 DIA DE ATRASO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Código de Processo Civil',
                        'detalhe': 'Despejo só pode ser determinado por ORDEM JUDICIAL após processo legal. Não existe despejo imediato!'
                    },
                    {
                        'regex': r'multa.*atraso.*10%.*dia|multa.*diária.*excessiva|penalidade.*diária.*atraso',
                        'descricao': '⚠️ MULTA DIÁRIA EXCESSIVA - ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51',
                        'detalhe': 'Multa diária excessiva pode ser considerada abusiva e reduzida judicialmente.'
                    },
                    
                    # CUMULAÇÃO DE GARANTIAS - ALTO
                    {
                        'regex': r'cumulação.*modalidades.*garantia|caução.*E.*fiador|seguro.*E.*caução|múltiplas.*garantias',
                        'descricao': '⚠️ CUMULAÇÃO DE GARANTIAS - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 37',
                        'detalhe': 'É proibida a cumulação de modalidades de garantia (caução E fiador).'
                    },
                    
                    # CLÁUSULAS LEONINAS - CRÍTICO
                    {
                        'regex': r'cláusula.*leonina|cláusula.*excessivamente.*onerosa|cláusula.*abuso.*direito',
                        'descricao': '🚨 CLÁUSULA LEONINA - NULA!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 423 + CDC Art. 51',
                        'detalhe': 'Cláusulas que impõem vantagem excessiva a uma parte são nulas.'
                    }
                ]
            },
            {
                'regex': r'salário.*inferior.*mínimo|salário.*abaixo.*mínimo|remuneração.*abaixo.*mínimo',
                'descricao': '🚨🚨 SALÁRIO INFERIOR AO MÍNIMO CONSTITUCIONAL!',
                'gravidade': 'CRÍTICA',
                'lei': 'Constituição Federal Art. 7º IV',
                'detalhe': 'Nenhum trabalhador pode receber menos que o salário mínimo.'
            },
            {
                'regex': r'jornada.*das\s*08:00.*às\s*20:00|08:00.*20:00|das\s*08.*às\s*20|jornada.*60.*horas.*semanais|60.*horas.*semanais|12.*horas.*diárias',
                'descricao': '🚨🚨 JORNADA EXCESSIVA - ILEGAL!',
                'gravidade': 'CRÍTICA',
                'lei': 'CLT Art. 58: Máximo 8h diárias / 44h semanais',
                'detalhe': '12h diárias = 50% ACIMA do limite! 60h semanais = 36% ACIMA do limite de 44h!'
            },
            {
                'regex': r'não.*haverá.*pagamento.*horas.*extras|sem.*pagamento.*horas.*extras|sem.*direito.*horas.*extras|horas.*extras.*não.*remuneradas',
                'descricao': '🚨🚨 SEM PAGAMENTO DE HORAS EXTRAS - ILEGAL!',
                'gravidade': 'CRÍTICA',
                'lei': 'CLT Art. 59: Horas extras obrigatórias após 8h/dia',
                'detalhe': 'Horas extras são DIREITO do trabalhador e DEVEM ser pagas com adicional!'
            },
            {
                'regex': r'23:00.*retornar.*06:00|encerrar.*23:00.*retornar.*06:00|intervalo.*interjornada.*7.*horas|7.*horas.*descanso',
                'descricao': '🚨🚨 INTERVALO INTERJORNADA DE 7 HORAS - ILEGAL!',
                'gravidade': 'CRÍTICA',
                'lei': 'CLT Art. 66: Mínimo 11 horas entre jornadas',
                'detalhe': '7 horas entre jornadas = 36% ABAIXO do mínimo de 11h!'
            },
            {
                'regex': r'intervalo.*refeição.*30.*minutos|30.*minutos.*refeição|intervalo.*10.*minutos|10.*minutos.*almoço|intervalo.*inferior.*1.*hora',
                'descricao': '🚨 INTERVALO INSUFICIENTE PARA REFEIÇÃO - ILEGAL!',
                'gravidade': 'CRÍTICA',
                'lei': 'CLT Art. 71: Mínimo 1 hora para jornada >6h',
                'detalhe': '30 minutos = 50% ABAIXO do mínimo! 10 minutos = VIOLAÇÃO GRAVÍSSIMA!'
            },
            {
                'regex': r'renúncia.*FGTS|renúncia.*Fundo.*Garantia|Vale.*Cultura.*substituição.*FGTS|FGTS.*descontado.*folha.*pagamento|não.*terá.*FGTS',
                'descricao': '🚨🚨🚨 RENÚNCIA AO FGTS - CRIME!',
                'gravidade': 'CRÍTICA',
                'lei': 'Lei 8.036/1990 Art. 15: FGTS é OBRIGATÓRIO',
                'detalhe': 'FGTS é DIREITO IRRENUNCIÁVEL! "Vale Cultura" NÃO substitui FGTS!'
            },
            {
                'regex': r'Cláusula.*Abusiva|cláusula.*abusiva|contrato.*contém.*abusividade',
                'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO ABUSIVA PELO PRÓPRIO CONTRATO!',
                'gravidade': 'CRÍTICA',
                'lei': 'CDC Art. 51',
                'detalhe': 'O próprio contrato reconhece que contém cláusulas abusivas!'
            },
            {
                'regex': r'Cláusula.*Ilegal|cláusula.*ilegal|contrato.*ilegalidade',
                'descricao': '🚨🚨 CLÁUSULA IDENTIFICADA COMO ILEGAL PELO PRÓPRIO CONTRATO!',
                'gravidade': 'CRÍTICA',
                'lei': 'Legislação trabalhista',
                'detalhe': 'O contrato ADMITE conter cláusulas ilegais!'
            },
            {
                'regex': r'Cláusula.*Nula|cláusula.*nula|nulidade.*cláusula',
                'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO NULA PELO PRÓPRIO CONTRATO!',
                'gravidade': 'CRÍTICA',
                'lei': 'Legislação aplicável',
                'detalhe': 'O contrato reconhece que possui cláusulas sem valor jurídico!'
            }
        }
        }
        
        # Termos para detecção rápida de tipo - ATUALIZADO
        self.indicadores_tipo = {
            'CONTRATO_LOCACAO': [
                'locação', 'aluguel', 'locador', 'locatário', 'imóvel residencial',
                'caução', 'fiador', 'benfeitorias', 'multa rescisória', 'inquilino',
                'proprietário', 'Lei 8.245/1991', 'Lei do Inquilinato', 'contrato de aluguel'
            ],
            'CONTRATO_TRABALHO': [
                'empregador', 'empregado', 'CLT', 'salário', 'jornada',
                'horas extras', 'FGTS', 'férias', '13º salário', 'funcionário',
                'trabalhador', 'contrato de trabalho', 'carteira de trabalho', 'holerite'
            ],
            'NOTA_FISCAL': [
                'nota fiscal', 'nfse', 'nfe', 'prefeitura municipal',
        
        texto_limpo = limpar_texto(texto).lower()
        
        # Verificação direta por termos chave
        if 'nota fiscal' in texto_limpo or 'nfse' in texto_limpo or 'nfe' in texto_limpo:
            return 'NOTA_FISCAL'
        
        if 'empregador' in texto_limpo and 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        
        if 'locação' in texto_limpo or ('locador' in texto_limpo and 'locatário' in texto_limpo):
            return 'CONTRATO_LOCACAO'
        if 'empregador' in texto_limpo and 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        
        if 'locação' in texto_limpo or ('locador' in texto_limpo and 'locatário' in texto_limpo):
            return 'CONTRATO_LOCACAO'
        
        # Contagem de termos
        scores = {}
        for doc_type, termos in self.indicadores_tipo.items():
            score = 0
            for termo in termos:
                if termo.lower() in texto_limpo:
                    score += 3
            scores[doc_type] = score
        
        # Escolher o tipo com maior score
        if scores:
            tipo_detectado = max(scores.items(), key=lambda x: x[1])
            if tipo_detectado[1] > 0:
                return tipo_detectado[0]
        
        return 'DESCONHECIDO'
    
    def analisar_documento(self, texto):
        """Análise super agressiva e abrangente"""
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
    
    def _calcular_metricas(self, problemas):
        """Cálculo agressivo de métricas"""
        total = len(problemas)
        criticos = sum(1 for p in problemas if 'CRÍTICA' in p.get('gravidade', ''))
        altos = sum(1 for p in problemas if 'ALTA' in p.get('gravidade', ''))
        medios = sum(1 for p in problemas if 'MÉDIA' in p.get('gravidade', ''))
        info = sum(1 for p in problemas if 'INFO' in p.get('gravidade', ''))
        
        # Penalização EXTREMA
        score = 100
        score -= criticos * 40  # -40 por crítica
        score -= altos * 25     # -25 por alta
        score -= medios * 10    # -10 por média
        score -= info * 0       # info não penaliza
        
        score = max(0, min(100, score))
        
        # Status ULTRA alarmante para problemas
        if criticos >= 5:
            status = '🚨🚨🚨 DOCUMENTO CRIMINAL - DENUNCIE!'
            cor = '#8B0000'
            nivel_risco = 'RISCO EXTREMO'
        elif criticos >= 3:
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
