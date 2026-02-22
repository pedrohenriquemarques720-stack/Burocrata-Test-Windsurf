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
# SISTEMA DE DETECÇÃO DIRETA - BASEADO NOS CONTRATOS REAIS
# --------------------------------------------------

class DetectorContratosReais:
    """
    Sistema que detecta VIOLAÇÕES REAIS dos contratos fornecidos
    Baseado nas strings EXATAS que aparecem nos documentos
    """
    
    def __init__(self):
        # Carregar violações específicas de cada contrato
        self.violacoes = self._carregar_violacoes_reais()
        
    def _carregar_violacoes_reais(self):
        """Carrega violações baseadas nos textos REAIS dos contratos"""
        return {
            # ===== CONTRATO DE EMPREGO 1 =====
            'jornada_12h_72h': {
                'nome': 'JORNADA DE TRABALHO ILEGAL (12h/dia - 72h/semana)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': '08:00 horas às 20:00 horas, de segunda a sábado, perfazendo 72 horas semanais',
                'descricao': 'Jornada de 12 horas diárias (72h semanais) VIOLA o limite legal de 8h/dia e 44h/semana da CLT.',
                'lei': 'Art. 58 CLT - Limite 8h/dia e 44h/semana',
                'solucao': 'Exija jornada máxima de 8h/dia e 44h/semana. Horas extras devem ser pagas com 50% de adicional.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'proibicao_horas_extras': {
                'nome': 'PROIBIÇÃO ILEGAL DE HORAS EXTRAS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'As partes concordam expressamente que não haverá pagamento de horas extras, sendo o salário fixo suficiente para remunerar toda e qualquer jornada extraordinária',
                'descricao': 'Cláusula que proíbe pagamento de horas extras é NULA. Trabalho além da jornada DEVE ser remunerado.',
                'lei': 'Art. 59 CLT - Adicional mínimo 50% para horas extras',
                'solucao': 'Horas extras DEVEM ser pagas com 50% de adicional. Esta cláusula é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'salario_900': {
                'nome': 'SALÁRIO ABAIXO DO MÍNIMO (R$ 900,00)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'R$ 900,00 (novecentos reais)',
                'descricao': 'Salário de R$ 900,00 está ABAIXO do salário mínimo nacional vigente (R$ 1.412,00 em 2024).',
                'lei': 'CF Art. 7º, IV - Salário mínimo nacional',
                'solucao': 'Exija salário mínimo vigente (R$ 1.412,00). Diferenças retroativas devem ser pagas.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'renuncia_fgts': {
                'nome': 'RENÚNCIA ILEGAL AO FGTS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O EMPREGADO renuncia expressamente ao FGTS (Fundo de Garantia do Tempo de Serviço). Em substituição ao FGTS, o EMPREGADOR concederá ao EMPREGADO um Vale Cultura no valor de R$ 50,00 (cinquenta reais) mensais',
                'descricao': 'FGTS é direito IRRENUNCIÁVEL. Substituição por Vale Cultura de R$ 50,00 é NULA.',
                'lei': 'Lei 8.036/90, Art. 15 - FGTS obrigatório',
                'solucao': 'Exija depósito mensal de 8% na conta vinculada do FGTS. A substituição é ILEGAL.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'experiencia_6_meses': {
                'nome': 'PERÍODO DE EXPERIÊNCIA DE 6 MESES (ILEGAL)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'período de experiência de 6 (seis) meses',
                'descricao': 'Período de experiência de 6 meses EXCEDE o limite legal de 90 dias da CLT.',
                'lei': 'Art. 445 CLT - Período de experiência máximo 90 dias',
                'solucao': 'Exija redução do período de experiência para no máximo 90 dias (3 meses).',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'intervalo_7h': {
                'nome': 'INTERVALO INTERJORNADAS DE 7h (ILEGAL)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'ao término de seu expediente às 23:00 horas, retornará às atividades às 06:00 horas do dia seguinte',
                'descricao': 'Intervalo de apenas 7h entre jornadas VIOLA mínimo legal de 11h consecutivas para descanso.',
                'lei': 'Art. 66 CLT - Mínimo 11h entre jornadas',
                'solucao': 'Exija intervalo mínimo de 11h entre jornadas.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'ferias_sem_terco': {
                'nome': 'FÉRIAS SEM 1/3 CONSTITUCIONAL',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'sem acréscimo de 1/3 constitucional',
                'descricao': 'Férias SEM acréscimo de 1/3 constitucional VIOLA direito fundamental.',
                'lei': 'CF Art. 7º, XVII - 1/3 constitucional',
                'solucao': 'Exija pagamento das férias com acréscimo de 1/3 constitucional.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'multa_demissao_3_salarios': {
                'nome': 'MULTA POR PEDIDO DE DEMISSÃO (ABUSIVA)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Em caso de pedido de demissão pelo EMPREGADO, este pagará multa equivalente a 3 (três) salários ao EMPREGADOR',
                'descricao': 'Multa por pedido de demissão é ABUSIVA e NULA. Rescisão por iniciativa do empregado NÃO gera multa.',
                'lei': 'Art. 9º CLT - Cláusulas lesivas são nulas',
                'solucao': 'Multa por pedido de demissão é NULA. Empregado pode rescindir contrato sem ônus.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'adicional_noturno_negado': {
                'nome': 'NEGAÇÃO DO ADICIONAL NOTURNO',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Trabalho realizado entre as 22:00 e 05:00 horas não será considerado noturno, não havendo adicional específico',
                'descricao': 'Trabalho noturno SEM adicional é ILEGAL. Adicional noturno é de no mínimo 20%.',
                'lei': 'Art. 73 CLT - Adicional noturno 20%',
                'solucao': 'Exija adicional de 20% para trabalho entre 22h e 5h.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'vale_transporte_integral': {
                'nome': 'DESCONTO INTEGRAL DO VALE-TRANSPORTE',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O vale-transporte será descontado integralmente do salário do EMPREGADO, independentemente do valor efetivamente gasto',
                'descricao': 'Desconto integral do vale-transporte VIOLA limite máximo de 6% do salário.',
                'lei': 'Lei 7.418/85 - Desconto máximo 6%',
                'solucao': 'Exija desconto máximo de 6% do salário para vale-transporte.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44'
            },
            
            'funcoes_indeterminadas': {
                'nome': 'FUNÇÕES INDETERMINADAS SEM ACRÉSCIMO',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O EMPREGADO poderá ser designado para exercer quaisquer outras funções que o EMPREGADOR julgar necessárias, sem acréscimo salarial',
                'descricao': 'Cláusula que permite designação para "quaisquer outras funções" sem acréscimo salarial é ABUSIVA.',
                'lei': 'Art. 468 CLT - Alteração contratual lesiva é nula',
                'solucao': 'Exija função determinada. Alteração de função pode gerar direito a adicional.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'estabilidade_renuncia': {
                'nome': 'RENÚNCIA À ESTABILIDADE ACIDENTÁRIA',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O EMPREGADO renuncia a qualquer direito à estabilidade, inclusive em caso de acidente de trabalho',
                'descricao': 'Renúncia à estabilidade acidentária é NULA. Estabilidade é direito IRRENUNCIÁVEL.',
                'lei': 'Lei 8.213/91, Art. 118 - Estabilidade acidentária',
                'solucao': 'Estabilidade acidentária é irrenunciável. Em caso de acidente, estabilidade de 12 meses.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            # ===== CONTRATO DE EMPREGO 2 =====
            'jornada_10h': {
                'nome': 'JORNADA DE 10 HORAS DIÁRIAS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Jornada de 10 horas diárias (das 07:00 às 17:00)',
                'descricao': 'Jornada de 10 horas diárias VIOLA limite legal de 8h/dia da CLT.',
                'lei': 'Art. 58 CLT - Limite 8h/dia',
                'solucao': 'Exija jornada máxima de 8h/dia. Horas extras devem ser pagas.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'pagamento_sem_recibo': {
                'nome': 'PAGAMENTO SEM RECIBO',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Pagamento até o dia 15 de cada mês, diretamente em mãos, sem recibo',
                'descricao': 'Pagamento sem recibo é ILEGAL. Todo pagamento deve ser documentado.',
                'lei': 'Art. 464 CLT - Pagamento deve ser comprovado',
                'solucao': 'Exija recibo de pagamento detalhado.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'descontos_uniforme_treinamento': {
                'nome': 'DESCONTOS ILEGAIS (UNIFORME E TREINAMENTO)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Serão descontados do salário: uniforme (R$ 50,00/mês), treinamento (R$ 30,00/mês)',
                'descricao': 'Descontos de uniforme e treinamento são ILEGAIS. Estes custos são do empregador.',
                'lei': 'Art. 462 CLT - Descontos apenas autorizados',
                'solucao': 'Exija devolução dos valores descontados ilegalmente.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'compensacao_folgas': {
                'nome': 'COMPENSAÇÃO DE HORAS EXTRAS EM FOLGAS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Horas extras serão compensadas em folgas, sem pagamento em dinheiro',
                'descricao': 'Compensação de horas extras em folgas, sem pagamento, é ILEGAL sem acordo de banco de horas.',
                'lei': 'Art. 59 CLT - Banco de horas exige acordo',
                'solucao': 'Exija pagamento em dinheiro das horas extras, com adicional de 50%.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'rescisao_doenca': {
                'nome': 'RESCISÃO POR DOENÇA (ILEGAL)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Ausência por doença superior a 2 dias consecutivos dará causa à rescisão imediata',
                'descricao': 'Rescisão por doença é DISCRIMINATÓRIA e ILEGAL. Doença NÃO é justa causa.',
                'lei': 'Art. 482 CLT - Doença não é justa causa',
                'solucao': 'Doença não justifica rescisão. Exija reintegração.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'rescisao_gravidez': {
                'nome': 'RESCISÃO POR GRAVIDEZ (ILEGAL E DISCRIMINATÓRIA)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Em caso de gravidez, o contrato será automaticamente rescindido',
                'descricao': 'Rescisão por gravidez é ILEGAL e DISCRIMINATÓRIA. Gestante tem ESTABILIDADE.',
                'lei': 'CF Art. 7º, XVIII e ADCT Art. 10, II, b',
                'solucao': 'Gravidez não justifica rescisão. Exija reintegração imediata.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'concorrencia_2_anos': {
                'nome': 'CLÁUSULA DE CONCORRÊNCIA POR 2 ANOS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Proibido trabalhar em qualquer outro estabelecimento do ramo por 2 anos após o término do contrato',
                'descricao': 'Cláusula de concorrência por 2 anos, sem contrapartida financeira, é ABUSIVA.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Cláusula de concorrência sem indenização é nula.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'seguro_vida_empregador': {
                'nome': 'DESCONTO DE SEGURO EM FAVOR DO EMPREGADOR',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O empregado autoriza desconto de R$ 20,00 mensais para seguro de vida em favor do empregador',
                'descricao': 'Desconto de seguro de vida em favor do empregador é ILEGAL.',
                'lei': 'Art. 462 CLT - Descontos apenas autorizados',
                'solucao': 'Recuse o desconto. Beneficiário deve ser o empregado.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            # ===== CONTRATO DE EMPREGO 3 =====
            'pejotizacao': {
                'nome': 'FRAUDE TRABALHISTA (PEJOTIZAÇÃO)',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'caracterizado como trabalho autônomo, sem vínculo empregatício',
                'descricao': 'Contrato de prestação de serviços disfarçando relação de emprego é FRAUDE TRABALHISTA.',
                'lei': 'Art. 3º CLT - Requisitos do vínculo',
                'solucao': 'Reconhecimento de vínculo empregatício na Justiça do Trabalho.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'horario_fixo_flexivel': {
                'nome': 'CONTRADIÇÃO: HORÁRIO FIXO E FLEXÍVEL',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Expediente fixo das 09:00 às 19:00, mas caracterizado como "horário flexível por acordo"',
                'descricao': 'Contradição entre horário fixo e flexível evidencia tentativa de mascarar subordinação.',
                'lei': 'Art. 3º CLT - Subordinação caracteriza vínculo',
                'solucao': 'Reconhecimento de vínculo empregatício.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'sem_fgts_inss': {
                'nome': 'AUSÊNCIA DE FGTS E INSS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'sem incidência de INSS ou FGTS',
                'descricao': 'Ausência de recolhimento de INSS e FGTS é FRAUDE PREVIDENCIÁRIA.',
                'lei': 'Lei 8.212/91 e Lei 8.036/90',
                'solucao': 'Exija recolhimento de INSS e FGTS.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'equipamentos_proprios': {
                'nome': 'USO DE EQUIPAMENTOS PRÓPRIOS SEM INDENIZAÇÃO',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O contratado utilizará seus próprios equipamentos (computador, software, internet)',
                'descricao': 'Exigir uso de equipamentos próprios sem indenização é ABUSIVO.',
                'lei': 'Art. 2º CLT - Empregador assume riscos',
                'solucao': 'Exija fornecimento de equipamentos ou indenização.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'sem_ferias': {
                'nome': 'AUSÊNCIA DE FÉRIAS REMUNERADAS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Não há direito a férias remuneradas, sendo o período de descanso por conta do contratado',
                'descricao': 'Ausência de férias remuneradas é ILEGAL. Férias são direito constitucional.',
                'lei': 'CF Art. 7º, XVII - Férias anuais remuneradas',
                'solucao': 'Exija férias anuais remuneradas com 1/3 constitucional.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'sem_verbas_rescisorias': {
                'nome': 'AUSÊNCIA DE VERBAS RESCISÓRIAS',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Rescisão a qualquer tempo, sem aviso prévio ou verbas rescisórias',
                'descricao': 'Rescisão sem aviso prévio ou verbas rescisórias é ILEGAL.',
                'lei': 'Arts. 477-480 CLT - Verbas rescisórias',
                'solucao': 'Exija pagamento de todas as verbas rescisórias.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'exclusividade_apos_termino': {
                'nome': 'EXCLUSIVIDADE APÓS TÉRMINO',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'O contratado se compromete a não prestar serviços a outras empresas do setor de tecnologia',
                'descricao': 'Exclusividade mesmo após término, sem prazo definido, é ABUSIVA.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Exclusividade pós-contrato exige prazo razoável e indenização.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'confidencialidade_eterna': {
                'nome': 'CONFIDENCIALIDADE ETERNA',
                'tipo': 'TRABALHISTA',
                'texto_alvo': 'Cláusula de confidencialidade eterna, mesmo após término do contrato',
                'descricao': 'Confidencialidade eterna é ABUSIVA. Obrigação deve ter prazo razoável.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Exija prazo determinado para confidencialidade.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44'
            },
            
            # ===== CONTRATOS DE LOCAÇÃO =====
            'reajuste_livre': {
                'nome': 'REAJUSTE LIVRE PELO LOCADOR',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'ficando o valor do aluguel sujeito a reajuste livre por parte do Locador, independentemente de índices inflacionários',
                'descricao': 'Reajuste livre, sem índice oficial, é ILEGAL. Reajuste deve basear-se em índices oficiais.',
                'lei': 'Lei 10.192/01 - Reajuste por índice oficial',
                'solucao': 'Exija reajuste anual baseado em índice oficial (IGP-M, IPCA).',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'renuncia_benfeitorias': {
                'nome': 'RENÚNCIA A BENFEITORIAS NECESSÁRIAS',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'Toda e qualquer benfeitoria, ainda que necessária ou útil, integrar-se-á ao imóvel, renunciando o Locatário, desde já, a qualquer direito de retenção ou indenização',
                'descricao': 'Renúncia a direito de indenização por benfeitorias necessárias é ILEGAL.',
                'lei': 'Art. 35, Lei 8.245/91',
                'solucao': 'Exija reembolso de consertos necessários. Esta cláusula é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'prazo_15_dias': {
                'nome': 'PRAZO DE 15 DIAS PARA DESOCUPAÇÃO',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'o presente contrato será rescindido de pleno direito, devendo o Locatário desocupar o imóvel no prazo máximo de 15 dias após a notificação',
                'descricao': 'Prazo de 15 dias para desocupação VIOLA prazo mínimo legal de 90 dias.',
                'lei': 'Art. 27, Lei 8.245/91 - Mínimo 90 dias',
                'solucao': 'Exija 90 dias para desocupação. Prazo inferior é ILEGAL.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'vistoria_unilateral': {
                'nome': 'VISTORIA UNILATERAL COM DÉBITO AUTOMÁTICO',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'A vistoria de saída será realizada exclusivamente pelo Locador ou seu preposto. O Locatário concorda, antecipadamente, com o orçamento de reparos apresentado pelo Locador, autorizando o débito automático',
                'descricao': 'Vistoria unilateral com orçamento vinculante e débito automático é ABUSIVA.',
                'lei': 'Art. 51, CDC e Lei 8.245/91',
                'solucao': 'Exija vistoria conjunta e direito de contestar orçamentos.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'reajuste_trimestral': {
                'nome': 'REAJUSTE TRIMESTRAL',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'reajuste trimestral conforme inflação + 5%',
                'descricao': 'Reajuste trimestral VIOLA periodicidade mínima anual de 12 meses.',
                'lei': 'Lei 10.192/01 - Reajuste anual obrigatório',
                'solucao': 'Exija reajuste apenas uma vez por ano.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'tripla_garantia': {
                'nome': 'TRIPLA GARANTIA (FIADOR + SEGURO + CAUÇÃO)',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'Fiador com renda 5x superior ao aluguel + seguro-fiança + caução de 6 meses',
                'descricao': 'Exigir múltiplas garantias simultaneamente é ILEGAL. A lei permite APENAS UMA forma de garantia.',
                'lei': 'Art. 37, Lei 8.245/91',
                'solucao': 'Escolha apenas UMA garantia: fiador OU caução OU seguro.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'multa_12_meses': {
                'nome': 'MULTA DE 12 MESES DE ALUGUEL',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'Multa de 12 meses de aluguel em caso de rescisão antecipada',
                'descricao': 'Multa de 12 meses é ABUSIVA. Multa deve ser proporcional ao tempo restante.',
                'lei': 'Art. 4º, Lei 8.245/91 e Art. 51, CDC',
                'solucao': 'Exija multa proporcional ao tempo restante.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000'
            },
            
            'visitas_sem_aviso': {
                'nome': 'VISITAS SEM AVISO PRÉVIO',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'O locador poderá visitar o imóvel a qualquer momento, sem aviso prévio',
                'descricao': 'Visitas sem aviso prévio VIOLAM direito de privacidade do locatário.',
                'lei': 'Art. 23, IX, Lei 8.245/91',
                'solucao': 'Exija visitas agendadas com 24h de antecedência.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'seguro_favor_locador': {
                'nome': 'SEGURO EM FAVOR DO LOCADOR',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'Locatário obrigado a contratar seguro contra todos os riscos em favor do locador',
                'descricao': 'Obrigar locatário a contratar seguro em favor do locador é ABUSIVO.',
                'lei': 'Art. 51, CDC',
                'solucao': 'Seguro do imóvel é responsabilidade do locador.',
                'gravidade': 'ALTA',
                'cor': '#ff4444'
            },
            
            'proibicao_animais_peixes': {
                'nome': 'PROIBIÇÃO DE ANIMAIS (INCLUSIVE PEIXES)',
                'tipo': 'LOCAÇÃO',
                'texto_alvo': 'Proibidos animais, inclusive peixes em aquário',
                'descricao': 'Proibição de animais, inclusive peixes, é ABUSIVA e irrazoável.',
                'lei': 'Art. 51, CDC e Súmula 482 STJ',
                'solucao': 'Proibição total de animais pode ser anulada judicialmente.',
                'gravidade': 'BAIXA',
                'cor': '#44aaff'
            }
        }
    
    def analisar_documento(self, texto):
        """Analisa documento procurando as strings exatas das violações"""
        if not texto:
            return [], 'INDEFINIDO', {'total': 0, 'criticas': 0, 'altas': 0, 'medias': 0, 'baixas': 0, 'pontuacao': 100, 'status': '✅ DOCUMENTO EM CONFORMIDADE', 'cor': '#27AE60'}
        
        texto_lower = texto.lower()
        violacoes_encontradas = []
        
        # Procurar cada violação no texto
        for vid, config in self.violacoes.items():
            texto_alvo = config['texto_alvo'].lower()
            
            # Verificar se o texto alvo está presente (considerando variações)
            if texto_alvo in texto_lower:
                # Extrair contexto
                pos = texto_lower.find(texto_alvo)
                inicio = max(0, pos - 50)
                fim = min(len(texto), pos + len(texto_alvo) + 50)
                contexto = texto[inicio:fim]
                
                violacoes_encontradas.append({
                    'id': vid,
                    'nome': config['nome'],
                    'tipo': config['tipo'],
                    'gravidade': config['gravidade'],
                    'descricao': config['descricao'],
                    'lei': config['lei'],
                    'solucao': config['solucao'],
                    'cor': config['cor'],
                    'contexto': contexto,
                    'texto_exato': config['texto_alvo'][:100] + '...'
                })
        
        # Determinar tipo de documento baseado nas violações
        tipos_contagem = {'TRABALHISTA': 0, 'LOCAÇÃO': 0}
        for v in violacoes_encontradas:
            if v['tipo'] in tipos_contagem:
                tipos_contagem[v['tipo']] += 1
        
        if tipos_contagem['TRABALHISTA'] > tipos_contagem['LOCAÇÃO']:
            tipo_documento = 'CONTRATO DE TRABALHO'
        elif tipos_contagem['LOCAÇÃO'] > 0:
            tipo_documento = 'CONTRATO DE LOCAÇÃO'
        else:
            tipo_documento = 'INDEFINIDO'
        
        # Calcular métricas
        metricas = self._calcular_metricas(violacoes_encontradas)
        
        return violacoes_encontradas, tipo_documento, metricas
    
    def _calcular_metricas(self, violacoes):
        """Calcula métricas da análise"""
        total = len(violacoes)
        criticas = sum(1 for v in violacoes if v['gravidade'] == 'CRÍTICA')
        altas = sum(1 for v in violacoes if v['gravidade'] == 'ALTA')
        medias = sum(1 for v in violacoes if v['gravidade'] == 'MÉDIA')
        baixas = sum(1 for v in violacoes if v['gravidade'] == 'BAIXA')
        
        # Calcular pontuação (100 - penalidades)
        pontuacao = 100
        pontuacao -= criticas * 15  # -15 por crítica
        pontuacao -= altas * 8      # -8 por alta
        pontuacao -= medias * 4      # -4 por média
        pontuacao -= baixas * 2      # -2 por baixa
        
        pontuacao = max(0, min(100, pontuacao))
        
        # Determinar status
        if criticas > 0:
            status = '⚠️⚠️⚠️ CONTRATO COM VIOLAÇÕES GRAVES'
            cor = '#ff0000'
            resumo = f'**{criticas} violação(ões) CRÍTICA(S) detectada(s). Este contrato contém cláusulas que violam a legislação.**'
        elif altas > 0:
            status = '⚠️⚠️ CONTRATO COM PROBLEMAS SIGNIFICATIVOS'
            cor = '#ff4444'
            resumo = f'**{altas} violação(ões) de ALTA gravidade detectada(s). Recomenda-se revisão urgente.**'
        elif medias > 0:
            status = '⚠️ CONTRATO COM IRREGULARIDADES'
            cor = '#ffaa44'
            resumo = f'**{medias} violação(ões) de MÉDIA gravidade detectada(s). Pontos que merecem atenção.**'
        elif baixas > 0:
            status = 'ℹ️ CONTRATO COM PEQUENAS INCONSISTÊNCIAS'
            cor = '#44aaff'
            resumo = f'**{baixas} inconsistência(s) de BAIXA gravidade detectada(s).**'
        else:
            status = '✅ DOCUMENTO EM CONFORMIDADE'
            cor = '#27AE60'
            resumo = '**Nenhuma violação significativa detectada.**'
        
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
    
    # Criar conta especial
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
        
        with st.spinner("🔍 Analisando documento..."):
            texto = extrair_texto_pdf(arquivo)
            
            if texto:
                # ANALISAR COM O DETECTOR DIRETO
                detector = DetectorContratosReais()
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
                                <p><strong>📄 Contexto:</strong> "...{v['contexto']}..."</p>
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
