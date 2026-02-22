import streamlit as st
import pdfplumber
import re
import unicodedata
from datetime import datetime
import pandas as pd
import sqlite3
import hashlib
import time

# --------------------------------------------------
# SISTEMA DE DETECÇÃO IMPLACÁVEL - MÚLTIPLAS CAMADAS
# --------------------------------------------------

class DetectorImplacavel:
    """
    SISTEMA DE DETECÇÃO COM 3 CAMADAS:
    1. Busca por texto exato (com normalização)
    2. Busca por palavras-chave e contexto
    3. Busca por padrões regex inteligentes
    """
    
    def __init__(self):
        # Base de violações completa
        self.violacoes = self._carregar_base_violacoes()
        self.palavras_chave = self._gerar_palavras_chave()
        
    def _carregar_base_violacoes(self):
        """Carrega base completa de violações com múltiplos padrões cada"""
        return {
            # ===== CONTRATO DE EMPREGO 1 =====
            'jornada_12h_72h': {
                'nome': '⏰ JORNADA DE 12H DIÁRIAS (72H SEMANAIS)',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Jornada de 12 horas diárias VIOLA o limite legal de 8h/dia e 44h/semana da CLT.',
                'lei': 'Art. 58 CLT - Limite 8h/dia e 44h/semana',
                'solucao': 'Exija jornada máxima de 8h/dia e 44h/semana. Horas extras devem ser pagas com 50% de adicional.',
                'padroes': [
                    # Padrões exatos do contrato
                    r'08:00\s*hORAS?\s*ÀS\s*20:00\s*hORAS?',
                    r'08\s*h\s*ÀS\s*20\s*h',
                    r'DAS\s*08\s*[h:]?\s*ÀS\s*20\s*[h:]?',
                    
                    # Padrões genéricos para jornada excessiva
                    r'JORNADA\s*DE\s*TRABALHO\s*SERÁ\s*DAS\s*08\s*[h:]?\s*(?:A|À)S\s*20\s*[h:]?',
                    r'JORNADA.*?(?:12|DOZE)\s*HORAS?\s*DIÁRIAS',
                    r'72\s*HORAS?\s*SEMANAIS',
                    
                    # Padrões para dias de trabalho
                    r'DE\s*SEGUNDA\s*A\s*SÁBADO',
                    r'SEGUNDA.*?SÁBADO',
                    
                    # Contexto completo
                    r'08:00.*?20:00.*?SEGUNDA.*?SÁBADO.*?72.*?HORAS'
                ]
            },
            
            'proibicao_horas_extras': {
                'nome': '🚫 PROIBIÇÃO ILEGAL DE HORAS EXTRAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Cláusula que proíbe pagamento de horas extras é NULA. Trabalho além da jornada DEVE ser remunerado.',
                'lei': 'Art. 59 CLT - Adicional mínimo 50% para horas extras',
                'solucao': 'Horas extras DEVEM ser pagas com 50% de adicional. Esta cláusula é NULA.',
                'padroes': [
                    r'NÃO\s*HAVERÁ\s*PAGAMENTO\s*DE\s*HORAS\s*EXTRAS',
                    r'NÃO\s*HAVERÁ\s*HORAS\s*EXTRAS',
                    r'PROIBID[OA]\s*HORAS\s*EXTRAS',
                    r'SALÁRIO\s*FIXO\s*SUFICIENTE\s*PARA\s*REMUNERAR\s*JORNADA\s*EXTRAORDINÁRIA',
                    r'SEM\s*DIREITO\s*A\s*HORAS\s*EXTRAS',
                    r'HORAS\s*EXTRAS\s*NÃO\s*SERÃO\s*REMUNERADAS',
                    r'EXTRAS\s*INCLUÍDAS\s*NO\s*SALÁRIO'
                ]
            },
            
            'salario_900': {
                'nome': '💰 SALÁRIO ABAIXO DO MÍNIMO (R$ 900,00)',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': f'Salário de R$ 900,00 está ABAIXO do salário mínimo nacional vigente (R$ 1.412,00 em 2024).',
                'lei': 'CF Art. 7º, IV - Salário mínimo nacional',
                'solucao': 'Exija salário mínimo vigente (R$ 1.412,00). Diferenças retroativas devem ser pagas.',
                'padroes': [
                    r'R\$\s*900[,\\.]00',
                    r'R\$\s*900[,\\.]\s*00',
                    r'900[,\\.]00\s*\(?NOVECENTOS\s*REAIS\)?',
                    r'NOVECENTOS\s*REAIS',
                    r'SALÁRIO\s*MENSAL\s*SERÁ\s*DE\s*R\$\s*900',
                    r'R\$\s*900[,\\.]\d*\s*MENSAL'
                ]
            },
            
            'renuncia_fgts': {
                'nome': '🏦 RENÚNCIA ILEGAL AO FGTS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'FGTS é direito IRRENUNCIÁVEL. Substituição por Vale Cultura de R$ 50,00 é NULA.',
                'lei': 'Lei 8.036/90, Art. 15 - FGTS obrigatório',
                'solucao': 'Exija depósito mensal de 8% na conta vinculada do FGTS. A substituição é ILEGAL.',
                'padroes': [
                    r'EMPREGADO\s*RENUNCIA\s*EXPRESSAMENTE\s*AO\s*FGTS',
                    r'RENUNCIA.*?FGTS',
                    r'EM\s*SUBSTITUIÇÃO\s*AO\s*FGTS',
                    r'VALE\s*CULTURA\s*NO\s*VALOR\s*DE\s*R\$\s*50[,\\.]00',
                    r'SUBSTITUIÇÃO.*?FGTS.*?VALE\s*CULTURA'
                ]
            },
            
            'experiencia_6_meses': {
                'nome': '📅 PERÍODO DE EXPERIÊNCIA DE 6 MESES',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Período de experiência de 6 meses EXCEDE o limite legal de 90 dias da CLT.',
                'lei': 'Art. 445 CLT - Período de experiência máximo 90 dias',
                'solucao': 'Exija redução do período de experiência para no máximo 90 dias (3 meses).',
                'padroes': [
                    r'PERÍODO\s*DE\s*EXPERIÊNCIA\s*DE\s*6\s*\(?SEIS\)?\s*MESES',
                    r'EXPERIÊNCIA\s*DE\s*6\s*MESES',
                    r'6\s*MESES\s*DE\s*EXPERIÊNCIA',
                    r'180\s*DIAS\s*DE\s*EXPERIÊNCIA'
                ]
            },
            
            'intervalo_7h': {
                'nome': '😴 INTERVALO INTERJORNADAS DE 7H',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Intervalo de apenas 7h entre jornadas VIOLA mínimo legal de 11h consecutivas para descanso.',
                'lei': 'Art. 66 CLT - Mínimo 11h entre jornadas',
                'solucao': 'Exija intervalo mínimo de 11h entre jornadas.',
                'padroes': [
                    r'TÉRMINO\s*DE\s*SEU\s*EXPEDIENTE\s*ÀS\s*23:00\s*HORAS',
                    r'RETORNARÁ\s*ÀS\s*06:00\s*HORAS\s*DO\s*DIA\s*SEGUINTE',
                    r'23:00.*?06:00',
                    r'INTERVALO.*?7\s*HORAS.*?ENTRE.*?JORNADAS'
                ]
            },
            
            'ferias_sem_terco': {
                'nome': '🏖️ FÉRIAS SEM 1/3 CONSTITUCIONAL',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Férias SEM acréscimo de 1/3 constitucional VIOLA direito fundamental.',
                'lei': 'CF Art. 7º, XVII - 1/3 constitucional',
                'solucao': 'Exija pagamento das férias com acréscimo de 1/3 constitucional.',
                'padroes': [
                    r'SEM\s*ACRÉSCIMO\s*DE\s*1/3\s*CONSTITUCIONAL',
                    r'FÉRIAS.*?SEM\s*1/3',
                    r'NÃO\s*HAVERÁ\s*1/3.*?FÉRIAS'
                ]
            },
            
            'multa_demissao_3_salarios': {
                'nome': '⚖️ MULTA POR PEDIDO DE DEMISSÃO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Multa por pedido de demissão é ABUSIVA e NULA. Rescisão por iniciativa do empregado NÃO gera multa.',
                'lei': 'Art. 9º CLT - Cláusulas lesivas são nulas',
                'solucao': 'Multa por pedido de demissão é NULA. Empregado pode rescindir contrato sem ônus.',
                'padroes': [
                    r'PEDIDO\s*DE\s*DEMISSÃO\s*PELO\s*EMPREGADO.*?PAGARÁ\s*MULTA\s*EQUIVALENTE\s*A\s*3\s*SALÁRIOS',
                    r'MULTA.*?3\s*SALÁRIOS.*?DEMISSÃO',
                    r'INDENIZAÇÃO.*?3\s*SALÁRIOS.*?DEMISSÃO'
                ]
            },
            
            'adicional_noturno_negado': {
                'nome': '🌙 NEGAÇÃO DO ADICIONAL NOTURNO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Trabalho noturno SEM adicional é ILEGAL. Adicional noturno é de no mínimo 20%.',
                'lei': 'Art. 73 CLT - Adicional noturno 20%',
                'solucao': 'Exija adicional de 20% para trabalho entre 22h e 5h.',
                'padroes': [
                    r'TRABALHO\s*REALIZADO\s*ENTRE\s*AS\s*22:00\s*E\s*05:00\s*HORAS\s*NÃO\s*SERÁ\s*CONSIDERADO\s*NOTURNO',
                    r'22:00.*?05:00.*?NÃO.*?NOTURNO',
                    r'SEM\s*ADICIONAL\s*NOTURNO'
                ]
            },
            
            'vale_transporte_integral': {
                'nome': '🚌 DESCONTO INTEGRAL DO VALE-TRANSPORTE',
                'tipo': 'TRABALHISTA',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': 'Desconto integral do vale-transporte VIOLA limite máximo de 6% do salário.',
                'lei': 'Lei 7.418/85 - Desconto máximo 6%',
                'solucao': 'Exija desconto máximo de 6% do salário para vale-transporte.',
                'padroes': [
                    r'VALE-TRANSPORTE\s*SERÁ\s*DESCONTADO\s*INTEGRALMENTE',
                    r'DESCONTO.*?INTEGRAL.*?VALE.*?TRANSPORTE',
                    r'INDEPENDENTEMENTE\s*DO\s*VALOR\s*EFETIVAMENTE\s*GASTO'
                ]
            },
            
            'funcoes_indeterminadas': {
                'nome': '🔄 FUNÇÕES INDETERMINADAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Cláusula que permite designação para "quaisquer outras funções" sem acréscimo salarial é ABUSIVA.',
                'lei': 'Art. 468 CLT - Alteração contratual lesiva é nula',
                'solucao': 'Exija função determinada. Alteração de função pode gerar direito a adicional.',
                'padroes': [
                    r'DESIGNADO\s*PARA\s*EXERCER\s*QUAISQUER\s*OUTRAS\s*FUNÇÕES',
                    r'QUAISQUER.*?OUTRAS.*?FUNÇÕES.*?SEM.*?ACRÉSCIMO',
                    r'PLURISSURBODINAÇÃO',
                    r'OUTRAS\s*FUNÇÕES\s*QUE\s*O\s*EMPREGADOR\s*JULGAR\s*NECESSÁRIAS'
                ]
            },
            
            'estabilidade_renuncia': {
                'nome': '🛡️ RENÚNCIA À ESTABILIDADE',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Renúncia à estabilidade acidentária é NULA. Estabilidade é direito IRRENUNCIÁVEL.',
                'lei': 'Lei 8.213/91, Art. 118 - Estabilidade acidentária',
                'solucao': 'Estabilidade acidentária é irrenunciável. Em caso de acidente, estabilidade de 12 meses.',
                'padroes': [
                    r'EMPREGADO\s*RENUNCIA\s*A\s*QUALQUER\s*DIREITO\s*À\s*ESTABILIDADE',
                    r'RENUNCIA.*?ESTABILIDADE.*?ACIDENTE\s*DE\s*TRABALHO',
                    r'SEM\s*DIREITO.*?ESTABILIDADE.*?ACIDENTE'
                ]
            },
            
            # ===== CONTRATO DE EMPREGO 2 =====
            'jornada_10h': {
                'nome': '⏰ JORNADA DE 10 HORAS DIÁRIAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Jornada de 10 horas diárias VIOLA limite legal de 8h/dia da CLT.',
                'lei': 'Art. 58 CLT - Limite 8h/dia',
                'solucao': 'Exija jornada máxima de 8h/dia. Horas extras devem ser pagas.',
                'padroes': [
                    r'JORNADA\s*DE\s*10\s*HORAS\s*DIÁRIAS',
                    r'07:00\s*ÀS\s*17:00',
                    r'DAS\s*07\s*[h:]?\s*ÀS\s*17\s*[h:]?'
                ]
            },
            
            'pagamento_sem_recibo': {
                'nome': '📝 PAGAMENTO SEM RECIBO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Pagamento sem recibo é ILEGAL. Todo pagamento deve ser documentado.',
                'lei': 'Art. 464 CLT - Pagamento deve ser comprovado',
                'solucao': 'Exija recibo de pagamento detalhado.',
                'padroes': [
                    r'PAGAMENTO.*?DIRETAMENTE\s*EM\s*MÃOS.*?SEM\s*RECIBO',
                    r'PAGAMENTO.*?SEM\s*RECIBO',
                    r'SEM\s*RECIBO\s*DE\s*PAGAMENTO'
                ]
            },
            
            'descontos_uniforme_treinamento': {
                'nome': '💰 DESCONTOS ILEGAIS (UNIFORME E TREINAMENTO)',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Descontos de uniforme e treinamento são ILEGAIS. Estes custos são do empregador.',
                'lei': 'Art. 462 CLT - Descontos apenas autorizados',
                'solucao': 'Exija devolução dos valores descontados ilegalmente.',
                'padroes': [
                    r'SERÃO\s*DESCONTADOS\s*DO\s*SALÁRIO:?\s*UNIFORME.*?TREINAMENTO',
                    r'DESCONTOS?.*?UNIFORME.*?R\$\s*50',
                    r'DESCONTOS?.*?TREINAMENTO.*?R\$\s*30'
                ]
            },
            
            'compensacao_folgas': {
                'nome': '🔄 COMPENSAÇÃO DE HORAS EXTRAS EM FOLGAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Compensação de horas extras em folgas, sem pagamento, é ILEGAL sem acordo de banco de horas.',
                'lei': 'Art. 59 CLT - Banco de horas exige acordo',
                'solucao': 'Exija pagamento em dinheiro das horas extras, com adicional de 50%.',
                'padroes': [
                    r'HORAS\s*EXTRAS\s*SERÃO\s*COMPENSADAS\s*EM\s*FOLGAS',
                    r'COMPENSAÇÃO.*?HORAS\s*EXTRAS.*?FOLGAS.*?SEM\s*PAGAMENTO',
                    r'HORAS\s*EXTRAS.*?COMPENSADAS.*?SEM\s*PAGAMENTO'
                ]
            },
            
            'rescisao_doenca': {
                'nome': '🏥 RESCISÃO POR DOENÇA',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Rescisão por doença é DISCRIMINATÓRIA e ILEGAL. Doença NÃO é justa causa.',
                'lei': 'Art. 482 CLT - Doença não é justa causa',
                'solucao': 'Doença não justifica rescisão. Exija reintegração.',
                'padroes': [
                    r'AUSÊNCIA\s*POR\s*DOENÇA\s*SUPERIOR\s*A\s*2\s*DIAS.*?RESCISÃO\s*IMEDIATA',
                    r'DOENÇA.*?DARÁ\s*CAUSA\s*À\s*RESCISÃO',
                    r'RESCISÃO.*?POR\s*DOENÇA'
                ]
            },
            
            'rescisao_gravidez': {
                'nome': '🤰 RESCISÃO POR GRAVIDEZ',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Rescisão por gravidez é ILEGAL e DISCRIMINATÓRIA. Gestante tem ESTABILIDADE.',
                'lei': 'CF Art. 7º, XVIII e ADCT Art. 10, II, b',
                'solucao': 'Gravidez não justifica rescisão. Exija reintegração imediata.',
                'padroes': [
                    r'EM\s*CASO\s*DE\s*GRAVIDEZ.*?CONTRATO\s*SERÁ\s*AUTOMATICAMENTE\s*RESCINDIDO',
                    r'GRAVIDEZ.*?RESCISÃO.*?AUTOMÁTICA',
                    r'RESCISÃO.*?POR\s*GRAVIDEZ'
                ]
            },
            
            'concorrencia_2_anos': {
                'nome': '🚫 CLÁUSULA DE CONCORRÊNCIA POR 2 ANOS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Cláusula de concorrência por 2 anos, sem contrapartida financeira, é ABUSIVA.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Cláusula de concorrência sem indenização é nula.',
                'padroes': [
                    r'PROIBIDO\s*TRABALHAR\s*EM\s*QUALQUER\s*OUTRO\s*ESTABELECIMENTO.*?2\s*ANOS',
                    r'CONCORRÊNCIA.*?2\s*ANOS.*?APÓS.*?TÉRMINO'
                ]
            },
            
            'seguro_vida_empregador': {
                'nome': '💔 SEGURO EM FAVOR DO EMPREGADOR',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Desconto de seguro de vida em favor do empregador é ILEGAL.',
                'lei': 'Art. 462 CLT - Descontos apenas autorizados',
                'solucao': 'Recuse o desconto. Beneficiário deve ser o empregado.',
                'padroes': [
                    r'AUTORIZA\s*DESCONTO\s*DE\s*R\$\s*20[,\\.]00\s*MENSAIS\s*PARA\s*SEGURO\s*DE\s*VIDA\s*EM\s*FAVOR\s*DO\s*EMPREGADOR',
                    r'SEGURO\s*DE\s*VIDA.*?EM\s*FAVOR\s*DO\s*EMPREGADOR'
                ]
            },
            
            # ===== CONTRATO DE EMPREGO 3 =====
            'pejotizacao': {
                'nome': '⚠️ FRAUDE TRABALHISTA (PEJOTIZAÇÃO)',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Contrato de prestação de serviços disfarçando relação de emprego é FRAUDE TRABALHISTA.',
                'lei': 'Art. 3º CLT - Requisitos do vínculo',
                'solucao': 'Reconhecimento de vínculo empregatício na Justiça do Trabalho.',
                'padroes': [
                    r'CARACTERIZADO\s*COMO\s*TRABALHO\s*AUTÔNOMO.*?SEM\s*VÍNCULO\s*EMPREGATÍCIO',
                    r'SEM\s*VÍNCULO\s*EMPREGATÍCIO',
                    r'NÃO\s*CARACTERIZADO\s*VÍNCULO',
                    r'PRESTAÇÃO\s*DE\s*SERVIÇOS.*?AUTÔNOMO'
                ]
            },
            
            'horario_fixo_flexivel': {
                'nome': '⚠️ CONTRADIÇÃO: HORÁRIO FIXO E FLEXÍVEL',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Contradição entre horário fixo e flexível evidencia tentativa de mascarar subordinação.',
                'lei': 'Art. 3º CLT - Subordinação caracteriza vínculo',
                'solucao': 'Reconhecimento de vínculo empregatício.',
                'padroes': [
                    r'EXPEDIENTE\s*FIXO.*?CARACTERIZADO\s*COMO\s*HORÁRIO\s*FLEXÍVEL',
                    r'FIXO.*?FLEXÍVEL.*?POR\s*ACORDO'
                ]
            },
            
            'sem_fgts_inss': {
                'nome': '⚠️ AUSÊNCIA DE FGTS E INSS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Ausência de recolhimento de INSS e FGTS é FRAUDE PREVIDENCIÁRIA.',
                'lei': 'Lei 8.212/91 e Lei 8.036/90',
                'solucao': 'Exija recolhimento de INSS e FGTS.',
                'padroes': [
                    r'SEM\s*INCIDÊNCIA\s*DE\s*INSS\s*OU\s*FGTS',
                    r'SEM\s*INSS.*?FGTS',
                    r'PAGAMENTO\s*COMO\s*HONORÁRIOS\s*PROFISSIONAIS'
                ]
            },
            
            'equipamentos_proprios': {
                'nome': '💻 EQUIPAMENTOS PRÓPRIOS SEM INDENIZAÇÃO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Exigir uso de equipamentos próprios sem indenização é ABUSIVO.',
                'lei': 'Art. 2º CLT - Empregador assume riscos',
                'solucao': 'Exija fornecimento de equipamentos ou indenização.',
                'padroes': [
                    r'UTILIZARÁ\s*SEUS\s*PRÓPRIOS\s*EQUIPAMENTOS.*?COMPUTADOR.*?SOFTWARE.*?INTERNET',
                    r'EQUIPAMENTOS\s*PRÓPRIOS',
                    r'COMPUTADOR.*?PRÓPRIO'
                ]
            },
            
            'sem_ferias': {
                'nome': '🏖️ AUSÊNCIA DE FÉRIAS REMUNERADAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Ausência de férias remuneradas é ILEGAL. Férias são direito constitucional.',
                'lei': 'CF Art. 7º, XVII - Férias anuais remuneradas',
                'solucao': 'Exija férias anuais remuneradas com 1/3 constitucional.',
                'padroes': [
                    r'NÃO\s*HÁ\s*DIREITO\s*A\s*FÉRIAS\s*REMUNERADAS',
                    r'SEM\s*DIREITO.*?FÉRIAS',
                    r'FÉRIAS.*?POR\s*CONTA\s*DO\s*CONTRATADO'
                ]
            },
            
            'sem_verbas_rescisorias': {
                'nome': '📋 AUSÊNCIA DE VERBAS RESCISÓRIAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Rescisão sem aviso prévio ou verbas rescisórias é ILEGAL.',
                'lei': 'Arts. 477-480 CLT - Verbas rescisórias',
                'solucao': 'Exija pagamento de todas as verbas rescisórias.',
                'padroes': [
                    r'RESCISÃO\s*A\s*QUALQUER\s*TEMPO.*?SEM\s*AVISO\s*PRÉVIO\s*OU\s*VERBAS\s*RESCISÓRIAS',
                    r'SEM\s*VERBAS\s*RESCISÓRIAS',
                    r'SEM\s*AVISO\s*PRÉVIO.*?RESCISÃO'
                ]
            },
            
            'exclusividade_apos_termino': {
                'nome': '🔒 EXCLUSIVIDADE APÓS TÉRMINO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Exclusividade mesmo após término, sem prazo definido, é ABUSIVA.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Exclusividade pós-contrato exige prazo razoável e indenização.',
                'padroes': [
                    r'NÃO\s*PRESTAR\s*SERVIÇOS\s*A\s*OUTRAS\s*EMPRESAS\s*DO\s*SETOR\s*DE\s*TECNOLOGIA',
                    r'EXCLUSIVIDADE.*?APÓS.*?TÉRMINO'
                ]
            },
            
            'confidencialidade_eterna': {
                'nome': '🤫 CONFIDENCIALIDADE ETERNA',
                'tipo': 'TRABALHISTA',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': 'Confidencialidade eterna é ABUSIVA. Obrigação deve ter prazo razoável.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Exija prazo determinado para confidencialidade.',
                'padroes': [
                    r'CONFIDENCIALIDADE\s*ETERNA.*?MESMO\s*APÓS\s*TÉRMINO',
                    r'CONFIDENCIALIDADE.*?ETERNA'
                ]
            },
            
            # ===== CONTRATOS DE LOCAÇÃO =====
            'reajuste_livre': {
                'nome': '📈 REAJUSTE LIVRE PELO LOCADOR',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Reajuste livre, sem índice oficial, é ILEGAL. Reajuste deve basear-se em índices oficiais.',
                'lei': 'Lei 10.192/01 - Reajuste por índice oficial',
                'solucao': 'Exija reajuste anual baseado em índice oficial (IGP-M, IPCA).',
                'padroes': [
                    r'REAJUSTE\s*LIVRE\s*POR\s*PARTE\s*DO\s*LOCADOR.*?INDEPENDENTEMENTE\s*DE\s*ÍNDICES\s*INFLACIONÁRIOS',
                    r'REAJUSTE\s*LIVRE.*?SEM\s*ÍNDICE',
                    r'A\s*CRITÉRIO\s*DO\s*LOCADOR'
                ]
            },
            
            'renuncia_benfeitorias': {
                'nome': '🏗️ RENÚNCIA A BENFEITORIAS',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Renúncia a direito de indenização por benfeitorias necessárias é ILEGAL.',
                'lei': 'Art. 35, Lei 8.245/91',
                'solucao': 'Exija reembolso de consertos necessários. Esta cláusula é NULA.',
                'padroes': [
                    r'TODA\s*E\s*QUALQUER\s*BENFEITORIA.*?RENUNCIANDO\s*O\s*LOCATÁRIO.*?A\s*QUALQUER\s*DIREITO\s*DE\s*RETENÇÃO\s*OU\s*INDENIZAÇÃO',
                    r'RENÚNCIA.*?BENFEITORIAS',
                    r'SEM\s*DIREITO.*?INDENIZAÇÃO.*?BENFEITORIA'
                ]
            },
            
            'prazo_15_dias': {
                'nome': '⏱️ PRAZO DE 15 DIAS PARA DESOCUPAÇÃO',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Prazo de 15 dias para desocupação VIOLA prazo mínimo legal de 90 dias.',
                'lei': 'Art. 27, Lei 8.245/91 - Mínimo 90 dias',
                'solucao': 'Exija 90 dias para desocupação. Prazo inferior é ILEGAL.',
                'padroes': [
                    r'DESOCUPAR\s*O\s*IMÓVEL\s*NO\s*PRAZO\s*MÁXIMO\s*DE\s*15\s*DIAS',
                    r'PRAZO.*?15\s*DIAS.*?DESOCUPAÇÃO',
                    r'15\s*DIAS.*?APÓS\s*NOTIFICAÇÃO'
                ]
            },
            
            'vistoria_unilateral': {
                'nome': '🔍 VISTORIA UNILATERAL COM DÉBITO AUTOMÁTICO',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Vistoria unilateral com orçamento vinculante e débito automático é ABUSIVA.',
                'lei': 'Art. 51, CDC e Lei 8.245/91',
                'solucao': 'Exija vistoria conjunta e direito de contestar orçamentos.',
                'padroes': [
                    r'VISTORIA\s*DE\s*SAÍDA\s*SERÁ\s*REALIZADA\s*EXCLUSIVAMENTE\s*PELO\s*LOCADOR.*?CONCORDA.*?COM\s*O\s*ORÇAMENTO.*?AUTORIZANDO\s*O\s*DÉBITO\s*AUTOMÁTICO',
                    r'VISTORIA.*?UNILATERAL.*?DÉBITO\s*AUTOMÁTICO'
                ]
            },
            
            'reajuste_trimestral': {
                'nome': '📆 REAJUSTE TRIMESTRAL',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Reajuste trimestral VIOLA periodicidade mínima anual de 12 meses.',
                'lei': 'Lei 10.192/01 - Reajuste anual obrigatório',
                'solucao': 'Exija reajuste apenas uma vez por ano.',
                'padroes': [
                    r'REAJUSTE\s*TRIMESTRAL\s*CONFORME\s*INFLAÇÃO\s*\+?\s*5%',
                    r'REAJUSTE.*?TRIMESTRAL',
                    r'A\s*CADA\s*3\s*MESES.*?REAJUSTE'
                ]
            },
            
            'tripla_garantia': {
                'nome': '🔒 TRIPLA GARANTIA (FIADOR + SEGURO + CAUÇÃO)',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Exigir múltiplas garantias simultaneamente é ILEGAL. A lei permite APENAS UMA forma de garantia.',
                'lei': 'Art. 37, Lei 8.245/91',
                'solucao': 'Escolha apenas UMA garantia: fiador OU caução OU seguro.',
                'padroes': [
                    r'FIADOR\s*COM\s*RENDA\s*5X\s*SUPERIOR.*?SEGURO-FIANÇA.*?CAUÇÃO\s*DE\s*6\s*MESES',
                    r'FIADOR.*?E.*?SEGURO.*?E.*?CAUÇÃO',
                    r'MÚLTIPLAS.*?GARANTIAS'
                ]
            },
            
            'multa_12_meses': {
                'nome': '💰 MULTA DE 12 MESES DE ALUGUEL',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Multa de 12 meses é ABUSIVA. Multa deve ser proporcional ao tempo restante.',
                'lei': 'Art. 4º, Lei 8.245/91 e Art. 51, CDC',
                'solucao': 'Exija multa proporcional ao tempo restante.',
                'padroes': [
                    r'MULTA\s*DE\s*12\s*MESES\s*DE\s*ALUGUEL\s*EM\s*CASO\s*DE\s*RESCISÃO\s*ANTECIPADA',
                    r'MULTA.*?12\s*MESES',
                    r'12\s*MESES.*?MULTA'
                ]
            },
            
            'visitas_sem_aviso': {
                'nome': '👁️ VISITAS SEM AVISO PRÉVIO',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Visitas sem aviso prévio VIOLAM direito de privacidade do locatário.',
                'lei': 'Art. 23, IX, Lei 8.245/91',
                'solucao': 'Exija visitas agendadas com 24h de antecedência.',
                'padroes': [
                    r'LOCADOR\s*PODERÁ\s*VISITAR\s*O\s*IMÓVEL\s*A\s*QUALQUER\s*MOMENTO.*?SEM\s*AVISO\s*PRÉVIO',
                    r'VISITAS.*?SEM\s*AVISO',
                    r'A\s*QUALQUER\s*MOMENTO.*?SEM\s*AVISO'
                ]
            },
            
            'seguro_favor_locador': {
                'nome': '🛡️ SEGURO EM FAVOR DO LOCADOR',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Obrigar locatário a contratar seguro em favor do locador é ABUSIVO.',
                'lei': 'Art. 51, CDC',
                'solucao': 'Seguro do imóvel é responsabilidade do locador.',
                'padroes': [
                    r'LOCATÁRIO\s*OBRIGADO\s*A\s*CONTRATAR\s*SEGURO\s*CONTRA\s*TODOS\s*OS\s*RISCOS\s*EM\s*FAVOR\s*DO\s*LOCADOR',
                    r'SEGURO.*?EM\s*FAVOR\s*DO\s*LOCADOR'
                ]
            },
            
            'proibicao_animais_peixes': {
                'nome': '🐕 PROIBIÇÃO DE ANIMAIS (INCLUSIVE PEIXES)',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'BAIXA',
                'cor': '#44aaff',
                'descricao': 'Proibição de animais, inclusive peixes, é ABUSIVA e irrazoável.',
                'lei': 'Art. 51, CDC e Súmula 482 STJ',
                'solucao': 'Proibição total de animais pode ser anulada judicialmente.',
                'padroes': [
                    r'PROIBIDOS\s*ANIMAIS.*?INCLUSIVE\s*PEIXES\s*EM\s*AQUÁRIO',
                    r'PROIBIDOS\s*ANIMAIS.*?PEIXES',
                    r'ANIMAIS.*?INCLUSIVE\s*PEIXES'
                ]
            }
        }
    
    def _gerar_palavras_chave(self):
        """Gera palavras-chave para detecção contextual"""
        return {
            'TRABALHISTA': [
                'jornada', 'horas extras', 'salário', 'fgts', 'inss', 'clt',
                'férias', '13º', 'aviso prévio', 'rescisão', 'estabilidade',
                'adicional noturno', 'vale transporte', 'intervalo', 'descanso',
                'experiência', 'demissão', 'empregador', 'empregado', 'funcionário'
            ],
            'LOCAÇÃO': [
                'locador', 'locatário', 'aluguel', 'imóvel', 'fiador', 'caução',
                'benfeitoria', 'reajuste', 'vistoria', 'desocupação', 'venda',
                'inquilino', 'proprietário', 'garantia', 'multa', 'rescisão'
            ]
        }
    
    def _normalizar_texto(self, texto):
        """Normaliza texto para busca (remove acentos, espaços extras, maiúsculas)"""
        if not texto:
            return ""
        
        # Converter para maiúsculas (facilita busca)
        texto = texto.upper()
        
        # Remover acentos
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join([c for c in texto if not unicodedata.combining(c)])
        
        # Normalizar espaços
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto
    
    def analisar_documento(self, texto_original):
        """Analisa documento com múltiplas camadas de detecção"""
        if not texto_original or len(texto_original) < 50:
            return [], 'INDEFINIDO', self._calcular_metricas([])
        
        # Preparar texto para busca
        texto_normalizado = self._normalizar_texto(texto_original)
        violacoes_encontradas = []
        ids_encontrados = set()
        
        # CAMADA 1: Busca por padrões regex em texto normalizado
        for vid, config in self.violacoes.items():
            for padrao in config['padroes']:
                try:
                    if re.search(padrao, texto_normalizado, re.IGNORECASE):
                        if vid not in ids_encontrados:
                            ids_encontrados.add(vid)
                            
                            # Extrair contexto
                            pos = texto_normalizado.find(padrao[:20].upper())
                            if pos > 0:
                                inicio = max(0, pos - 100)
                                fim = min(len(texto_original), pos + 200)
                                contexto = texto_original[inicio:fim]
                            else:
                                contexto = texto_original[:300]
                            
                            violacoes_encontradas.append({
                                'id': vid,
                                'nome': config['nome'],
                                'tipo': config['tipo'],
                                'gravidade': config['gravidade'],
                                'descricao': config['descricao'],
                                'lei': config['lei'],
                                'solucao': config['solucao'],
                                'cor': config['cor'],
                                'contexto': contexto
                            })
                            break
                except:
                    continue
        
        # CAMADA 2: Se nenhuma violação encontrada, busca por palavras-chave
        if not violacoes_encontradas:
            # Detectar tipo de documento
            tipo_doc = self._detectar_tipo_por_palavras_chave(texto_normalizado)
            
            # Se for documento trabalhista, adicionar violação genérica
            if tipo_doc == 'CONTRATO DE TRABALHO':
                # Verificar palavras suspeitas
                palavras_suspeitas = []
                if 'SALÁRIO' in texto_normalizado and 'R$' in texto_normalizado:
                    # Tentar extrair valor do salário
                    match = re.search(r'R\$\s*(\d+)[,\\.]?\d*', texto_normalizado)
                    if match:
                        salario = int(match.group(1))
                        if salario < 1412:
                            # Adicionar violação de salário mínimo
                            violacoes_encontradas.append({
                                'id': 'salario_suspeito',
                                'nome': '⚠️ SALÁRIO POTENCIALMENTE ABAIXO DO MÍNIMO',
                                'tipo': 'TRABALHISTA',
                                'gravidade': 'ALTA',
                                'cor': '#ff4444',
                                'descricao': f'Foi identificado um valor de salário (R$ {salario}) que pode estar abaixo do mínimo legal (R$ 1.412,00).',
                                'lei': 'CF Art. 7º, IV - Salário mínimo nacional',
                                'solucao': 'Verifique se o salário está de acordo com o mínimo legal.',
                                'contexto': texto_original[:500]
                            })
        
        # Determinar tipo de documento
        tipo_documento = self._determinar_tipo_documento(violacoes_encontradas, texto_normalizado)
        
        # Calcular métricas
        metricas = self._calcular_metricas(violacoes_encontradas)
        
        return violacoes_encontradas, tipo_documento, metricas
    
    def _detectar_tipo_por_palavras_chave(self, texto):
        """Detecta tipo de documento por palavras-chave"""
        score_trabalhista = 0
        score_locacao = 0
        
        for palavra in self.palavras_chave['TRABALHISTA']:
            if palavra.upper() in texto:
                score_trabalhista += 1
        
        for palavra in self.palavras_chave['LOCAÇÃO']:
            if palavra.upper() in texto:
                score_locacao += 1
        
        if score_trabalhista > score_locacao:
            return 'CONTRATO DE TRABALHO'
        elif score_locacao > 0:
            return 'CONTRATO DE LOCAÇÃO'
        else:
            return 'INDEFINIDO'
    
    def _determinar_tipo_documento(self, violacoes, texto):
        """Determina o tipo de documento baseado nas violações e no texto"""
        if not violacoes:
            return self._detectar_tipo_por_palavras_chave(texto)
        
        tipos = {'TRABALHISTA': 0, 'LOCAÇÃO': 0}
        for v in violacoes:
            if v['tipo'] in tipos:
                tipos[v['tipo']] += 1
        
        if tipos['TRABALHISTA'] > tipos['LOCAÇÃO']:
            return 'CONTRATO DE TRABALHO'
        elif tipos['LOCAÇÃO'] > 0:
            return 'CONTRATO DE LOCAÇÃO'
        else:
            return 'INDEFINIDO'
    
    def _calcular_metricas(self, violacoes):
        """Calcula métricas da análise"""
        total = len(violacoes)
        criticas = sum(1 for v in violacoes if v['gravidade'] == 'CRÍTICA')
        altas = sum(1 for v in violacoes if v['gravidade'] == 'ALTA')
        medias = sum(1 for v in violacoes if v['gravidade'] == 'MÉDIA')
        baixas = sum(1 for v in violacoes if v['gravidade'] == 'BAIXA')
        
        # Calcular pontuação
        pontuacao = 100
        pontuacao -= criticas * 15
        pontuacao -= altas * 8
        pontuacao -= medias * 4
        pontuacao -= baixas * 2
        pontuacao = max(0, min(100, pontuacao))
        
        # Status
        if criticas > 0:
            status = '⚠️⚠️⚠️ CONTRATO COM VIOLAÇÕES GRAVES'
            cor = '#ff0000'
            resumo = f'**{criticas} violação(ões) CRÍTICA(S) detectada(s)!**'
        elif altas > 0:
            status = '⚠️⚠️ CONTRATO COM PROBLEMAS SIGNIFICATIVOS'
            cor = '#ff4444'
            resumo = f'**{altas} violação(ões) de ALTA gravidade detectada(s).**'
        elif medias > 0:
            status = '⚠️ CONTRATO COM IRREGULARIDADES'
            cor = '#ffaa44'
            resumo = f'**{medias} violação(ões) de MÉDIA gravidade detectada(s).**'
        elif baixas > 0:
            status = 'ℹ️ CONTRATO COM PEQUENAS INCONSISTÊNCIAS'
            cor = '#44aaff'
            resumo = f'**{baixas} inconsistência(s) detectada(s).**'
        else:
            status = '✅ DOCUMENTO EM CONFORMIDADE'
            cor = '#27AE60'
            resumo = '**Nenhuma violação detectada.**'
        
        return {
            'total': total,
            'criticas': criticas,
            'altas': altas,
            'medias': medias,
            'baixas': baixas,
            'pontuacao': round(pontuacao, 1),
            'status': status,
            'cor': cor,
            'resumo': resumo
        }

# --------------------------------------------------
# FUNÇÕES AUXILIARES DE AUTENTICAÇÃO (mantidas iguais)
# --------------------------------------------------

def hash_palavra_passe(palavra_passe):
    return hashlib.sha256(palavra_passe.encode()).hexdigest()

CAMINHO_BD = 'utilizadores_burocrata.db'

def inicializar_base_dados():
    conn = sqlite3.connect(CAMINHO_BD)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            palavra_passe_hash TEXT NOT NULL,
            plano TEXT DEFAULT 'GRATUITO',
            burocreditos INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'ATIVO'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS historico_analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilizador_id INTEGER,
            nome_ficheiro TEXT,
            tipo_documento TEXT,
            problemas_detetados INTEGER,
            pontuacao_conformidade REAL,
            data_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilizador_id) REFERENCES utilizadores (id)
        )
    ''')
    
    conta_especial_email = "pedrohenriquemarques720@gmail.com"
    palavra_passe_especial_hash = hash_palavra_passe("Liz1808#")
    
    c.execute("SELECT COUNT(*) FROM utilizadores WHERE email = ?", (conta_especial_email,))
    resultado = c.fetchone()
    
    if resultado and resultado[0] == 0:
        c.execute('''
            INSERT INTO utilizadores (nome, email, palavra_passe_hash, plano, burocreditos)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Pedro Henrique (Conta Especial)", conta_especial_email, palavra_passe_especial_hash, 'PRO', 999999))
    
    conn.commit()
    conn.close()

inicializar_base_dados()

def criar_utilizador(nome, email, palavra_passe):
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM utilizadores WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "E-mail já registado"
        
        palavra_passe_hash = hash_palavra_passe(palavra_passe)
        
        c.execute('''
            INSERT INTO utilizadores (nome, email, palavra_passe_hash, plano, burocreditos)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, palavra_passe_hash, 'GRATUITO', 0))
        
        conn.commit()
        conn.close()
        return True, "Utilizador criado com sucesso!"
        
    except Exception as e:
        return False, f"Erro: {str(e)}"

def autenticar_utilizador(email, palavra_passe):
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        palavra_passe_hash = hash_palavra_passe(palavra_passe)
        
        c.execute('''
            SELECT id, nome, email, plano, burocreditos, estado 
            FROM utilizadores 
            WHERE email = ? AND palavra_passe_hash = ? AND estado = 'ATIVO'
        ''', (email, palavra_passe_hash))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return True, {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreditos': resultado[4],
                'estado': resultado[5]
            }
        else:
            return False, "E-mail ou palavra-passe incorretos"
            
    except Exception as e:
        return False, f"Erro: {str(e)}"

def obter_utilizador_por_id(utilizador_id):
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, nome, email, plano, burocreditos, estado 
            FROM utilizadores 
            WHERE id = ?
        ''', (utilizador_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreditos': resultado[4],
                'estado': resultado[5]
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

def atualizar_burocreditos(utilizador_id, quantidade):
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute("SELECT email FROM utilizadores WHERE id = ?", (utilizador_id,))
        utilizador = c.fetchone()
        
        if utilizador and utilizador[0] == "pedrohenriquemarques720@gmail.com":
            conn.close()
            return True
        
        c.execute('''
            UPDATE utilizadores 
            SET burocreditos = burocreditos + ? 
            WHERE id = ?
        ''', (quantidade, utilizador_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro: {e}")
        return False

def registar_analise(utilizador_id, nome_ficheiro, tipo_documento, problemas, pontuacao):
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO historico_analises 
            (utilizador_id, nome_ficheiro, tipo_documento, problemas_detetados, pontuacao_conformidade)
            VALUES (?, ?, ?, ?, ?)
        ''', (utilizador_id, nome_ficheiro, tipo_documento, problemas, pontuacao))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def extrair_texto_pdf(ficheiro):
    try:
        with pdfplumber.open(ficheiro) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        return None

# --------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------------------------------
st.set_page_config(
    page_title="Burocrata de Bolso - Expert Jurídico",
    page_icon="⚖️",
    layout="wide"
)

# --------------------------------------------------
# CSS (simplificado)
# --------------------------------------------------
st.markdown("""
<style>
    .stApp {
        background: #0a1a2f !important;
    }
    .header-main {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #0a1a2f, #1a2a3f);
        border-bottom: 3px solid #F8D96D;
        margin-bottom: 20px;
    }
    .header-main h1 {
        color: #F8D96D;
        font-size: 2.5em;
        margin: 0;
    }
    .header-main p {
        color: white;
        font-size: 1.1em;
    }
    .user-card {
        background: #1a2a3f;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #F8D96D;
        margin: 10px 0;
    }
    .violation-card {
        background: #1a2a3f;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid;
        margin: 10px 0;
    }
    .metric-box {
        background: #1a2a3f;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #F8D96D;
    }
    .stButton > button {
        background: linear-gradient(135deg, #F8D96D, #d4aA37);
        color: black;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TELA DE LOGIN
# --------------------------------------------------
def tela_login():
    st.markdown('<div class="header-main"><h1>⚖️ BUROCRATA DE BOLSO</h1><p>Expert Jurídico</p></div>', unsafe_allow_html=True)
    
    if 'modo' not in st.session_state:
        st.session_state.modo = 'login'
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background:#1a2a3f; padding:30px; border-radius:15px; border:2px solid #F8D96D;">', unsafe_allow_html=True)
        
        if st.session_state.modo == 'login':
            st.markdown('<h3 style="color:#F8D96D; text-align:center;">🔐 ENTRAR</h3>', unsafe_allow_html=True)
            
            email = st.text_input("E-mail", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password", placeholder="Sua senha")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🚀 Entrar", use_container_width=True):
                    if email and senha:
                        ok, dados = autenticar_utilizador(email, senha)
                        if ok:
                            st.session_state.user = dados
                            st.session_state.auth = True
                            st.success("✅ Login OK!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ E-mail ou senha inválidos")
            
            with col_b:
                if st.button("📝 Criar Conta", use_container_width=True):
                    st.session_state.modo = 'cadastro'
                    st.rerun()
        
        else:
            st.markdown('<h3 style="color:#F8D96D; text-align:center;">📝 CRIAR CONTA</h3>', unsafe_allow_html=True)
            
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar Senha", type="password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Cadastrar", use_container_width=True):
                    if nome and email and senha and confirmar:
                        if senha != confirmar:
                            st.error("❌ Senhas não conferem")
                        elif len(senha) < 6:
                            st.error("❌ Senha muito curta")
                        else:
                            ok, msg = criar_utilizador(nome, email, senha)
                            if ok:
                                st.success("✅ Conta criada! Faça login.")
                                st.session_state.modo = 'login'
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
            
            with col_b:
                if st.button("🔙 Voltar", use_container_width=True):
                    st.session_state.modo = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------
def tela_principal():
    user = st.session_state.user
    is_especial = user['email'] == "pedrohenriquemarques720@gmail.com"
    
    st.markdown(f'''
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>Olá, {user['nome']} | Créditos: {"∞" if is_especial else user['burocreditos']}</p>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="user-card">📄 Envie seu contrato em PDF para análise jurídica</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
    
    # Upload
    arquivo = st.file_uploader("Selecione o arquivo PDF", type=['pdf'])
    
    if arquivo:
        if not is_especial and user['burocreditos'] < 10:
            st.error("❌ Créditos insuficientes! Entre em contato com contatoburocrat@outlook.com")
            return
        
        with st.spinner("🔍 Analisando documento com IA Jurídica..."):
            texto = extrair_texto_pdf(arquivo)
            
            if texto:
                # ANALISAR COM O DETECTOR IMPLACÁVEL
                detector = DetectorImplacavel()
                violacoes, tipo_doc, metricas = detector.analisar_documento(texto)
                
                # Registrar análise
                if user['id']:
                    registar_analise(user['id'], arquivo.name, tipo_doc, metricas['total'], metricas['pontuacao'])
                    if not is_especial:
                        atualizar_burocreditos(user['id'], -10)
                        user['burocreditos'] -= 10
                
                # RESULTADOS
                st.markdown("---")
                
                # Score
                st.markdown(f'''
                <div style="background:#1a2a3f; padding:20px; border-radius:10px; border-left:6px solid {metricas['cor']}; margin:20px 0;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h3 style="color:{metricas['cor']}; margin:0;">{metricas['status']}</h3>
                            <p style="color:white;">Tipo: {tipo_doc} | {metricas['resumo']}</p>
                        </div>
                        <div style="font-size:3em; font-weight:bold; color:{metricas['cor']};">{metricas['pontuacao']}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                # Métricas
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1: st.metric("Total", metricas['total'])
                with col2: st.metric("Críticas", metricas['criticas'], delta_color="inverse")
                with col3: st.metric("Altas", metricas['altas'])
                with col4: st.metric("Médias", metricas['medias'])
                with col5: st.metric("Baixas", metricas['baixas'])
                
                # Lista de violações
                if violacoes:
                    st.markdown("### 🚨 VIOLAÇÕES DETECTADAS")
                    
                    for i, v in enumerate(violacoes, 1):
                        with st.expander(f"{i}. {v['nome']}"):
                            st.markdown(f'''
                            <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:8px; border-left:4px solid {v['cor']};">
                                <p><strong>📋 Descrição:</strong> {v['descricao']}</p>
                                <p><strong>⚖️ Lei:</strong> {v['lei']}</p>
                                <p><strong>✅ Solução:</strong> {v['solucao']}</p>
                                <p><strong>📄 Contexto:</strong> "...{v['contexto'][:200]}..."</p>
                                <p><strong>⚠️ Gravidade:</strong> <span style="color:{v['cor']};">{v['gravidade']}</span></p>
                            </div>
                            ''', unsafe_allow_html=True)
                else:
                    st.success("✅ NENHUMA VIOLAÇÃO DETECTADA NESTE DOCUMENTO!")
    
    else:
        # Exemplos
        st.markdown("### 📋 Exemplos de violações que detectamos:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **CONTRATOS DE TRABALHO:**
            - Jornada 12h/dia (08-20h) - ILEGAL
            - Salário R$ 900,00 (abaixo do mínimo)
            - Renúncia ao FGTS por Vale Cultura
            - Período de experiência de 6 meses
            - Intervalo de 7h entre jornadas
            - Férias sem 1/3 constitucional
            - Multa por pedido de demissão
            - Adicional noturno negado
            """)
        with col2:
            st.markdown("""
            **CONTRATOS DE LOCAÇÃO:**
            - Reajuste livre sem índice
            - Renúncia a benfeitorias necessárias
            - Prazo de 15 dias para desocupação
            - Vistoria unilateral com débito automático
            - Garantia dupla/tripla (fiador + caução + seguro)
            - Multa de 12 meses de aluguel
            - Visitas sem aviso prévio
            - Proibição de animais (inclusive peixes)
            """)

# --------------------------------------------------
# MAIN
# --------------------------------------------------
def main():
    if 'auth' not in st.session_state:
        st.session_state.auth = False
    
    if not st.session_state.auth:
        tela_login()
    else:
        tela_principal()

if __name__ == "__main__":
    main()
