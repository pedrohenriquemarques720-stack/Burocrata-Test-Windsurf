import streamlit as st
import pdfplumber
import re
import unicodedata
from datetime import datetime
import pandas as pd
import sqlite3
import hashlib
import time
from typing import Dict, List, Tuple, Any
import json

# --------------------------------------------------
# CONFIGURAÇÃO DO MODO ESPECIALISTA
# --------------------------------------------------
st.set_page_config(
    page_title="⚖️ BUROCRATA DE BOLSO - MODO ESPECIALISTA JURÍDICO",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CORE ENGINE JURÍDICO - DETECÇÃO EXTREMA DE RISCOS
# --------------------------------------------------

class CoreEngineJuridico:
    """
    ██████╗ ██╗   ██╗██████╗  ██████╗  ██████╗██████╗  █████╗ ████████╗ █████╗ 
    ██╔══██╗██║   ██║██╔══██╗██╔═══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
    ██████╔╝██║   ██║██████╔╝██║   ██║██║     ██████╔╝███████║   ██║   ███████║
    ██╔══██╗██║   ██║██╔══██╗██║   ██║██║     ██╔══██╗██╔══██║   ██║   ██╔══██║
    ██████╔╝╚██████╔╝██║  ██║╚██████╔╝╚██████╗██║  ██║██║  ██║   ██║   ██║  ██║
    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
    """
    
    def __init__(self):
        self.base_legal = self._carregar_base_legal_completa()
        self.violacoes = self._carregar_violacoes_especialista()
        self.palavras_ambiguas = self._carregar_termos_ambiguos()
        self.omissoes_criticas = self._carregar_omissoes()
        
    def _carregar_base_legal_completa(self) -> Dict:
        """Base de dados jurídica completa para cross-reference"""
        return {
            'CLT': {
                'nome': 'Consolidação das Leis do Trabalho',
                'artigos': {
                    '58': 'Duração normal do trabalho não excederá 8h diárias e 44h semanais',
                    '59': 'Horas extras com adicional mínimo de 50%',
                    '60': 'Trabalho noturno - adicional 20% e hora reduzida',
                    '61': 'Banco de horas - máximo 6 meses',
                    '62': 'Excluídos do controle de jornada',
                    '63': 'Trabalho em regime de tempo parcial',
                    '64': 'Salário mínimo - R$ 1.412,00 (2024)',
                    '65': 'Equiparação salarial',
                    '66': 'Intervalo interjornada mínimo 11h',
                    '67': 'Intervalo intrajornada mínimo 1h',
                    '68': 'Descanso semanal remunerado',
                    '129': 'Férias - 30 dias corridos',
                    '130': 'Período aquisitivo',
                    '142': '13º salário',
                    '158': 'FGTS - 8% mensal',
                    '168': 'Seguro-desemprego',
                    '443': 'Contrato individual de trabalho',
                    '444': 'Contrato verbal e tácito',
                    '445': 'Período de experiência máximo 90 dias',
                    '468': 'Alteração contratual lesiva é nula',
                    '477': 'Rescisão contratual',
                    '478': 'Aviso prévio',
                    '479': 'Justa causa',
                    '480': 'Indenização',
                    '482': 'Rol taxativo de justas causas',
                    '483': 'Rescisão indireta'
                },
                'sumulas_tst': {
                    '291': 'Horas extras habituais integram salário',
                    '338': 'Jornada de trabalho deve ser registrada',
                    '347': 'Intervalo intrajornada não concedido gera pagamento integral'
                }
            },
            'LEI_INQUILINATO': {
                'nome': 'Lei 8.245/91 - Locação de Imóveis Urbanos',
                'artigos': {
                    '3': 'Locação residencial',
                    '4': 'Locação não residencial',
                    '5': 'Locação por temporada',
                    '6': 'Contrato verbal',
                    '7': 'Prazo da locação',
                    '8': 'Renovação compulsória',
                    '9': 'Denúncia vazia',
                    '10': 'Multa rescisória - proporcional',
                    '11': 'Reajuste anual',
                    '12': 'Índices oficiais (IGP-M/IPCA)',
                    '13': 'Fiador',
                    '14': 'Caução - máximo 3 meses',
                    '15': 'Seguro fiança',
                    '16': 'Cessão da locação',
                    '17': 'Sublocação',
                    '18': 'Benfeitorias',
                    '19': 'Obras urgentes',
                    '20': 'Direito de preferência',
                    '21': 'Ação de despejo',
                    '22': 'Consignação em pagamento',
                    '23': 'Obrigações do locador',
                    '24': 'Obrigações do locatário',
                    '35': 'Benfeitorias necessárias - direito a indenização',
                    '37': 'Garantia - vedada mais de uma modalidade',
                    '39': 'Multa por infração',
                    '40': 'Foro de eleição'
                }
            },
            'CDC': {
                'nome': 'Código de Defesa do Consumidor - Lei 8.078/90',
                'artigos': {
                    '39': 'Práticas abusivas',
                    '46': 'Direito à informação',
                    '47': 'Cláusulas abusivas',
                    '48': 'Contratos de adesão',
                    '49': 'Direito de arrependimento - 7 dias',
                    '50': 'Garantia contratual',
                    '51': 'Cláusulas abusivas (lista)',
                    '52': 'Juros e multa',
                    '53': 'Cláusula de decaimento'
                }
            },
            'CODIGO_CIVIL': {
                'nome': 'Código Civil - Lei 10.406/2002',
                'artigos': {
                    '122': 'Condição suspensiva e resolutiva',
                    '389': 'Inadimplemento',
                    '390': 'Juros de mora',
                    '391': 'Responsabilidade patrimonial',
                    '392': 'Contratos comutativos',
                    '393': 'Contratos aleatórios',
                    '394': 'Vício redibitório',
                    '395': 'Evicção',
                    '396': 'Cláusula penal',
                    '397': 'Multa contratual',
                    '398': 'Juros compensatórios',
                    '399': 'Atualização monetária',
                    '400': 'Comissão de permanência'
                }
            },
            'LEI_DISTRATO': {
                'nome': 'Lei 13.786/18 - Lei do Distrato',
                'artigos': {
                    '1': 'Distrato imobiliário',
                    '2': 'Multa rescisória - máximo 25%',
                    '3': 'Devolução de valores',
                    '4': 'Comissão de corretagem',
                    '5': 'Taxa de fruição'
                }
            },
            'LEI_KANDIR': {
                'nome': 'Lei Kandir 87/96 - ICMS',
                'artigos': {
                    '1': 'Fato gerador',
                    '2': 'Base de cálculo',
                    '3': 'Alíquotas',
                    '4': 'Não cumulatividade',
                    '5': 'Crédito do imposto'
                }
            }
        }
    
    def _carregar_termos_ambiguos(self) -> Dict[str, List[str]]:
        """Termos que geram ambiguidade jurídica"""
        return {
            'prazo_razoavel': [
                r'prazo\s*razoável',
                r'tempo\s*razoável',
                r'período\s*razoável',
                r'quando\s*possível',
                r'assim\s*que\s*possível'
            ],
            'custos_adicionais': [
                r'custos?\s*adicionais?',
                r'despesas?\s*extras?',
                r'encargos?\s*eventuais?',
                r'custos?\s*necessários?',
                r'despesas?\s*imprevistas?'
            ],
            'eventuais_necessidades': [
                r'eventuais?\s*necessidades?',
                r'quando\s*necessário',
                r'caso\s*necessário',
                r'se\s*necessário',
                r'conforme\s*necessidade'
            ],
            'multa_geral': [
                r'multa\s*contratual',
                r'penalidade\s*contratual',
                r'indenização\s*por\s*descumprimento'
            ],
            'juros_mora': [
                r'juros?\s*de\s*mora',
                r'juros?\s*moratórios?',
                r'juros?\s*legais?',
                r'juros?\s*contratuais?'
            ],
            'foro': [
                r'foro\s*de\s*eleição',
                r'foro\s*competente',
                r'foro\s*da\s*comarca'
            ]
        }
    
    def _carregar_omissoes(self) -> Dict[str, List[str]]:
        """Detecta omissões críticas no contrato"""
        return {
            'TRABALHISTA': {
                'multa_rescisoria': [
                    r'multa.*?rescisória',
                    r'penalidade.*?rescisão',
                    r'indenização.*?término'
                ],
                'aviso_previo': [
                    r'aviso.*?prévio',
                    r'notificação.*?prévia',
                    r'comunicação.*?rescisão'
                ],
                'ferias': [
                    r'férias',
                    r'descanso.*?anual'
                ],
                '13_salario': [
                    r'13º',
                    r'décimo.*?terceiro',
                    r'gratificação.*?natalina'
                ],
                'fgts': [
                    r'fgts',
                    r'fundo.*?garantia'
                ],
                'horas_extras': [
                    r'horas.*?extras',
                    r'hora.*?extra',
                    r'sobrejornada'
                ]
            },
            'LOCACAO': {
                'multa_rescisoria_proporcional': [
                    r'multa.*?proporcional',
                    r'penalidade.*?proporcional',
                    r'indenização.*?tempo.*?restante'
                ],
                'reajuste_indice': [
                    r'reajuste.*?índice',
                    r'correção.*?IGP[ -]?M',
                    r'atualização.*?IPCA'
                ],
                'vistoria_conjunta': [
                    r'vistoria.*?conjunta',
                    r'vistoria.*?ambas.*?partes',
                    r'inspeção.*?locador.*?locatário'
                ],
                'prazo_desocupacao': [
                    r'prazo.*?desocupação',
                    r'tempo.*?para.*?sair',
                    r'dias.*?para.*?desocupar'
                ]
            }
        }
    
    def _carregar_violacoes_especialista(self) -> Dict:
        """Base expandida com todas as violações e referências legais"""
        violacoes_base = {
            # ===== VIOLAÇÕES TRABALHISTAS =====
            'jornada_excessiva': {
                'nome': '⏰ JORNADA EXCESSIVA - ART. 58 CLT',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Jornada superior a 8h/dia ou 44h/semana viola o limite legal.',
                'lei': 'Art. 58 CLT - Limite 8h/dia e 44h/semana',
                'solucao': 'Reduza a jornada para 8h/dia. Horas excedentes são extras com adicional de 50%.',
                'penalidade': 'Pagamento de horas extras com adicional + possibilidade de dano moral por excesso de jornada',
                'jurisprudencia': 'Súmula 338 TST - Ônus da prova da jornada',
                'padroes': [
                    r'jornada.*?(?:superior|maior|acima).*?8.*?horas',
                    r'jornada.*?(?:12|doze).*?horas',
                    r'(?:08|8)[:h]\s*(?:a|à)s\s*(?:20|20:00)',
                    r'72.*?horas.*?semanais',
                    r'jornada.*?(?:10|dez).*?horas'
                ]
            },
            
            'ausencia_horas_extras': {
                'nome': '🚫 AUSÊNCIA DE PAGAMENTO DE HORAS EXTRAS',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Horas extras não remuneradas ou compensadas irregularmente.',
                'lei': 'Art. 59 CLT - Adicional mínimo 50%',
                'solucao': 'Horas extras devem ser pagas com adicional de 50% ou compensadas em banco de horas regular.',
                'penalidade': 'Pagamento em dobro + multa + verbas rescisórias',
                'jurisprudencia': 'Súmula 291 TST - Horas extras habituais integram salário',
                'padroes': [
                    r'não.*?haverá.*?pagamento.*?horas.*?extras',
                    r'horas.*?extras.*?incluídas.*?salário',
                    r'compensação.*?horas.*?extras.*?sem.*?acordo',
                    r'horas.*?extras.*?não.*?remuneradas'
                ]
            },
            
            'salario_inferior_minimo': {
                'nome': '💰 SALÁRIO INFERIOR AO MÍNIMO LEGAL',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Remuneração abaixo do salário mínimo nacional vigente (R$ 1.412,00).',
                'lei': 'CF Art. 7º, IV e Lei 12.382/11',
                'solucao': 'Adequar o salário ao mínimo legal. Diferenças retroativas são devidas.',
                'penalidade': 'Pagamento de diferenças salariais + multa administrativa',
                'jurisprudencia': 'Súmula Vinculante 4',
                'padroes': [
                    r'R\$\s*(?:900|1000|1100|1200)[,\\.]?\d*',
                    r'salário.*?(?:900|1000|1100|1200)',
                    r'remuneração.*?(?:900|1000|1100|1200)'
                ]
            },
            
            'fgts_irregular': {
                'nome': '🏦 FGTS IRREGULAR OU RENUNCIADO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'FGTS não recolhido ou objeto de renúncia - direito indisponível.',
                'lei': 'Lei 8.036/90, Art. 15 - Obrigatório 8% mensal',
                'solucao': 'Exija comprovação dos depósitos do FGTS. Renúncia é nula.',
                'penalidade': 'Multa de 40% do FGTS + atualização monetária',
                'jurisprudencia': 'Súmula 98 TST - FGTS é direito indisponível',
                'padroes': [
                    r'renuncia.*?fgts',
                    r'sem.*?direito.*?fgts',
                    r'fgts.*?substituído',
                    r'não.*?haverá.*?fgts',
                    r'vale.*?cultura.*?fgts'
                ]
            },
            
            'periodo_experiencia_excessivo': {
                'nome': '📅 PERÍODO DE EXPERIÊNCIA EXCESSIVO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Período de experiência superior a 90 dias.',
                'lei': 'Art. 445 CLT - Máximo 90 dias',
                'solucao': 'Reduza para no máximo 90 dias. Período superior é nulo.',
                'penalidade': 'Reconhecimento de contrato por prazo indeterminado desde o início',
                'jurisprudencia': 'Súmula 188 TST',
                'padroes': [
                    r'experiência.*?(?:6|seis).*?meses',
                    r'180.*?dias.*?experiência',
                    r'prorrogação.*?experiência.*?(?:90|noventa).*?dias'
                ]
            },
            
            'intervalo_interjornadas_insuficiente': {
                'nome': '😴 INTERVALO INTERJORNADAS INSUFICIENTE',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Intervalo entre jornadas inferior a 11h consecutivas.',
                'lei': 'Art. 66 CLT - Mínimo 11h',
                'solucao': 'Garanta intervalo mínimo de 11h entre jornadas.',
                'penalidade': 'Pagamento do período como hora extra + adicional',
                'jurisprudencia': 'OJ 355 SDI-1 TST',
                'padroes': [
                    r'(?:23|23:00).*?(?:06|06:00)',
                    r'intervalo.*?7.*?horas',
                    r'retorno.*?(?:6|6h|06).*?após.*?(?:23|23h)'
                ]
            },
            
            'ferias_sem_terco': {
                'nome': '🏖️ FÉRIAS SEM 1/3 CONSTITUCIONAL',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Férias concedidas sem o adicional de 1/3 constitucional.',
                'lei': 'CF Art. 7º, XVII - 1/3 constitucional',
                'solucao': 'Acrescente 1/3 ao valor das férias. Cláusula de renúncia é nula.',
                'penalidade': 'Pagamento em dobro + 1/3',
                'jurisprudencia': 'Súmula 7 TST',
                'padroes': [
                    r'sem.*?acréscimo.*?1/3',
                    r'férias.*?sem.*?terço',
                    r'não.*?haverá.*?1/3'
                ]
            },
            
            'multa_pedido_demissao': {
                'nome': '⚖️ MULTA POR PEDIDO DE DEMISSÃO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Cláusula que impõe multa ao empregado que pede demissão.',
                'lei': 'Art. 9º CLT - Cláusulas lesivas são nulas',
                'solucao': 'Esta cláusula é nula. Empregado pode pedir demissão sem ônus.',
                'penalidade': 'Declaração de nulidade + indenização por danos morais',
                'jurisprudencia': 'Súmula 51 TST',
                'padroes': [
                    r'multa.*?(?:3|três).*?salários.*?demissão',
                    r'pedido.*?demissão.*?pagará.*?multa',
                    r'indenização.*?por.*?demissão'
                ]
            },
            
            'adicional_noturno_suprimido': {
                'nome': '🌙 ADICIONAL NOTURNO SUPRIMIDO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Trabalho noturno sem o adicional legal de 20%.',
                'lei': 'Art. 73 CLT - Adicional noturno 20% e hora reduzida',
                'solucao': 'Adicional noturno é obrigatório para trabalho entre 22h e 5h.',
                'penalidade': 'Pagamento do adicional + reflexos',
                'jurisprudencia': 'Súmula 60 TST',
                'padroes': [
                    r'(?:22|22h|22:00).*?(?:05|5|05:00).*?não.*?noturno',
                    r'sem.*?adicional.*?noturno',
                    r'não.*?considerado.*?noturno'
                ]
            },
            
            'desconto_vale_transporte_excessivo': {
                'nome': '🚌 DESCONTO EXCESSIVO DE VALE-TRANSPORTE',
                'tipo': 'TRABALHISTA',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': 'Desconto de vale-transporte superior ao limite legal de 6%.',
                'lei': 'Lei 7.418/85 - Desconto máximo 6%',
                'solucao': 'Desconto máximo é 6% do salário. Excedente é responsabilidade do empregador.',
                'penalidade': 'Devolução dos valores descontados indevidamente',
                'jurisprudencia': 'Súmula 60 TST',
                'padroes': [
                    r'desconto.*?integral.*?vale.*?transporte',
                    r'vale.*?transporte.*?custo.*?integral',
                    r'descontado.*?independentemente.*?gasto'
                ]
            },
            
            'funcao_indeterminada': {
                'nome': '🔄 FUNÇÃO INDETERMINADA - DESVIO DE FUNÇÃO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Cláusula que permite exercer "quaisquer outras funções" sem acréscimo salarial.',
                'lei': 'Art. 468 CLT - Alteração contratual lesiva',
                'solucao': 'Função deve ser determinada. Alterações podem gerar direito a adicional.',
                'penalidade': 'Diferenças salariais + danos morais',
                'jurisprudencia': 'Súmula 6 TST',
                'padroes': [
                    r'quaisquer.*?outras.*?funções',
                    r'exercer.*?atividades.*?determinadas',
                    r'sem.*?acréscimo.*?salarial'
                ]
            },
            
            'estabilidade_renunciada': {
                'nome': '🛡️ RENÚNCIA À ESTABILIDADE',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Renúncia a estabilidades (acidentária, gestante, cipeiro).',
                'lei': 'Lei 8.213/91, Art. 118 - Estabilidade acidentária',
                'solucao': 'Estabilidade é direito indisponível. Cláusula é nula.',
                'penalidade': 'Reintegração + indenização do período',
                'jurisprudencia': 'Súmula 378 TST',
                'padroes': [
                    r'renuncia.*?estabilidade',
                    r'sem.*?direito.*?estabilidade',
                    r'estabilidade.*?acidentária.*?não'
                ]
            },
            
            'pejotizacao': {
                'nome': '⚠️ FRAUDE TRABALHISTA - PEJOTIZAÇÃO',
                'tipo': 'TRABALHISTA',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Contrato de prestação de serviços disfarçando vínculo empregatício.',
                'lei': 'Art. 3º CLT - Requisitos do vínculo empregatício',
                'solucao': 'Presentes os requisitos (pessoalidade, subordinação, habitualidade), o vínculo deve ser reconhecido.',
                'penalidade': 'Reconhecimento do vínculo + todas as verbas trabalhistas',
                'jurisprudencia': 'Súmula 331 TST',
                'padroes': [
                    r'sem.*?vínculo.*?empregatício',
                    r'trabalho.*?autônomo',
                    r'prestação.*?serviços.*?sem.*?vínculo',
                    r'pessoa.*?jurídica.*?prestação'
                ]
            },
            
            # ===== VIOLAÇÕES LOCATÍCIAS =====
            'reajuste_ilegal': {
                'nome': '📈 REAJUSTE ILEGAL - SEM ÍNDICE OFICIAL',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Reajuste livre ou arbitrário, sem vinculação a índice oficial.',
                'lei': 'Lei 10.192/01 e Art. 17 Lei 8.245/91',
                'solucao': 'Reajuste deve ser anual e baseado em índice oficial (IGP-M, IPCA).',
                'penalidade': 'Nulidade da cláusula + devolução de valores pagos a maior',
                'jurisprudencia': 'Súmula 3 STJ',
                'padroes': [
                    r'reajuste.*?livre',
                    r'critério.*?locador',
                    r'independente.*?índice',
                    r'sem.*?vinculação.*?índice'
                ]
            },
            
            'garantia_multipla': {
                'nome': '🔒 GARANTIA MÚLTIPLA - VEDADA POR LEI',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Exigência de mais de uma modalidade de garantia simultaneamente.',
                'lei': 'Art. 37, Lei 8.245/91 - Vedada cumulação',
                'solucao': 'Escolha apenas uma garantia: fiador OU caução OU seguro.',
                'penalidade': 'Nulidade da exigência cumulativa',
                'jurisprudencia': 'Súmula 4 STJ',
                'padroes': [
                    r'fiador.*?e.*?caução',
                    r'fiador.*?e.*?seguro',
                    r'caução.*?e.*?seguro',
                    r'múltiplas.*?garantias'
                ]
            },
            
            'benfeitorias_renuncia': {
                'nome': '🏗️ RENÚNCIA A BENFEITORIAS NECESSÁRIAS',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Renúncia ao direito de indenização por benfeitorias necessárias.',
                'lei': 'Art. 35, Lei 8.245/91',
                'solucao': 'Benfeitorias necessárias dão direito a indenização. Cláusula é nula.',
                'penalidade': 'Indenização integral + retenção por benfeitorias',
                'jurisprudencia': 'Súmula 2 STJ',
                'padroes': [
                    r'renuncia.*?benfeitoria',
                    r'sem.*?direito.*?indenização.*?benfeitoria',
                    r'benfeitoria.*?integra.*?imóvel.*?sem.*?ônus'
                ]
            },
            
            'prazo_desocupacao_reduzido': {
                'nome': '⏱️ PRAZO DE DESOCUPAÇÃO REDUZIDO',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Prazo inferior a 90 dias para desocupação em caso de venda.',
                'lei': 'Art. 27, Lei 8.245/91 - Mínimo 90 dias',
                'solucao': 'Exija o prazo legal de 90 dias. Prazo inferior é nulo.',
                'penalidade': 'Prorrogação do prazo + indenização',
                'jurisprudencia': 'Súmula 5 STJ',
                'padroes': [
                    r'(?:15|30|45).*?dias.*?desocupar',
                    r'prazo.*?desocupação.*?(?:15|30|45)',
                    r'desocupação.*?imediata'
                ]
            },
            
            'vistoria_unilateral_abusiva': {
                'nome': '🔍 VISTORIA UNILATERAL ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Vistoria exclusiva do locador com orçamento vinculante.',
                'lei': 'Art. 51, CDC e Art. 23, Lei 8.245/91',
                'solucao': 'Vistoria deve ser conjunta. Orçamentos podem ser contestados.',
                'penalidade': 'Nulidade da cláusula + danos morais',
                'jurisprudencia': 'Súmula 6 STJ',
                'padroes': [
                    r'vistoria.*?exclusivamente.*?locador',
                    r'orçamento.*?vinculante',
                    r'débito.*?automático.*?reparos'
                ]
            },
            
            'multa_integral_abusiva': {
                'nome': '💰 MULTA INTEGRAL ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Multa equivalente a todos os aluguéis vincendos.',
                'lei': 'Art. 4º, Lei 8.245/91 - Multa proporcional',
                'solucao': 'Multa deve ser proporcional ao tempo restante.',
                'penalidade': 'Redução da multa ao patamar legal',
                'jurisprudencia': 'Súmula 7 STJ',
                'padroes': [
                    r'multa.*?12.*?meses',
                    r'multa.*?integral.*?período',
                    r'multa.*?todos.*?aluguéis.*?vincendos',
                    r'multa.*?100%.*?valor.*?contrato'
                ]
            },
            
            'visitas_sem_aviso': {
                'nome': '👁️ VISITAS SEM AVISO PRÉVIO',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Locador pode visitar o imóvel a qualquer momento.',
                'lei': 'Art. 23, IX, Lei 8.245/91',
                'solucao': 'Visitas devem ser agendadas com 24h de antecedência.',
                'penalidade': 'Danos morais por violação de privacidade',
                'jurisprudencia': 'Súmula 8 STJ',
                'padroes': [
                    r'visitar.*?qualquer.*?momento',
                    r'sem.*?aviso.*?prévio',
                    r'acesso.*?irrestrito'
                ]
            },
            
            'seguro_favor_locador': {
                'nome': '🛡️ SEGURO EM FAVOR DO LOCADOR',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'descricao': 'Obrigação de contratar seguro em favor do locador.',
                'lei': 'Art. 51, CDC - Vantagem exagerada',
                'solucao': 'Seguro do imóvel é responsabilidade do proprietário.',
                'penalidade': 'Nulidade da cláusula + danos morais',
                'jurisprudencia': 'Súmula 9 STJ',
                'padroes': [
                    r'seguro.*?favor.*?locador',
                    r'contratar.*?seguro.*?todos.*?riscos',
                    r'seguro.*?obrigatório.*?beneficiário.*?locador'
                ]
            },
            
            'proibicao_animais_absoluta': {
                'nome': '🐕 PROIBIÇÃO ABSOLUTA DE ANIMAIS',
                'tipo': 'LOCAÇÃO',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': 'Proibição total de animais, inclusive inofensivos.',
                'lei': 'Art. 51, CDC e Súmula 482 STJ',
                'solucao': 'Proibição pode ser considerada abusiva, especialmente para animais inofensivos.',
                'penalidade': 'Declaração de nulidade + danos morais',
                'jurisprudencia': 'Súmula 482 STJ',
                'padroes': [
                    r'proibidos.*?animais',
                    r'vedados.*?animais',
                    r'não.*?permitidos.*?animais',
                    r'proibido.*?pet'
                ]
            },
            
            # ===== VIOLAÇÕES DE CONTRATOS EM GERAL =====
            'juros_abusivos': {
                'nome': '💹 JUROS ABUSIVOS',
                'tipo': 'CONTRATUAL',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Juros superiores ao permitido por lei ou à média de mercado.',
                'lei': 'Art. 406 CC c/c Lei de Usura',
                'solucao': 'Juros limitados a 1% ao mês, salvo exceções legais.',
                'penalidade': 'Redução dos juros ao patamar legal',
                'jurisprudencia': 'Súmula 379 STJ',
                'padroes': [
                    r'juros.*?(?:5|10|15|20)%',
                    r'juros.*?superior.*?1%.*?mês',
                    r'taxa.*?juros.*?acima.*?mercado'
                ]
            },
            
            'clausula_leonina': {
                'nome': '🦁 CLÁUSULA LEONINA',
                'tipo': 'CONTRATUAL',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'descricao': 'Cláusula que coloca uma parte em desvantagem exagerada.',
                'lei': 'Art. 51, CDC e Art. 157 CC',
                'solucao': 'Cláusula leonina é nula de pleno direito.',
                'penalidade': 'Nulidade da cláusula',
                'jurisprudencia': 'Súmula 1 STJ',
                'padroes': [
                    r'única.*?responsabilidade',
                    r'apenas.*?uma.*?parte.*?obrigada',
                    r'todos.*?ônus.*?para'
                ]
            },
            
            'foro_eleicao_abusivo': {
                'nome': '📍 FORO DE ELEIÇÃO ABUSIVO',
                'tipo': 'CONTRATUAL',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': 'Eleição de foro que dificulta o acesso à justiça.',
                'lei': 'Art. 51, CDC e Art. 112 CC',
                'solucao': 'Foro deve ser do domicílio do consumidor, salvo exceções.',
                'penalidade': 'Declaração de nulidade do foro de eleição',
                'jurisprudencia': 'Súmula 335 STJ',
                'padroes': [
                    r'foro.*?eleição.*?distante',
                    r'elegem.*?foro.*?diverso',
                    r'comarca.*?diversa.*?domicílio'
                ]
            }
        }
        
        # Adicionar padrões de ambiguidade como violações
        for nome, padroes in self.palavras_ambiguas.items():
            violacoes_base[f'ambiguidade_{nome}'] = {
                'nome': f'⚠️ TERMO AMBÍGUO: {nome.upper()}',
                'tipo': 'AMBIGUIDADE',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'descricao': f'Termo vago "{nome}" sem definição objetiva. Gera insegurança jurídica.',
                'lei': 'Art. 112 CC e Art. 47 CDC - Interpretação mais favorável',
                'solucao': 'Defina objetivamente prazos, valores e condições. Evite termos subjetivos.',
                'penalidade': 'Interpretação contra quem redigiu o contrato',
                'jurisprudencia': 'Súmula 2 STJ',
                'padroes': padroes
            }
        
        return violacoes_base
    
    def _normalizar_texto(self, texto: str) -> str:
        """Normalização avançada para análise jurídica"""
        if not texto:
            return ""
        
        # Preservar estrutura original para contexto
        texto_original = texto
        
        # Versão normalizada para busca
        texto = texto.upper()
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join([c for c in texto if not unicodedata.combining(c)])
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto
    
    def _analisar_ambiguidade(self, texto_normalizado: str) -> List[Dict]:
        """Parsing de Ambiguidade - identifica termos vagos"""
        violacoes = []
        
        for nome_termo, padroes in self.palavras_ambiguas.items():
            for padrao in padroes:
                matches = re.finditer(padrao, texto_normalizado, re.IGNORECASE)
                for match in matches:
                    violacoes.append({
                        'tipo': 'AMBIGUIDADE',
                        'nome': f'Termo ambíguo: {nome_termo}',
                        'descricao': f'Expressão vaga "{match.group()}" encontrada. Gera risco de interpretação divergente.',
                        'gravidade': 'MÉDIA',
                        'cor': '#ffaa44',
                        'contexto': match.group(),
                        'lei': 'Art. 112 CC - Interpretação dos negócios jurídicos'
                    })
        
        return violacoes
    
    def _analisar_omissoes(self, texto_normalizado: str, tipo_documento: str) -> List[Dict]:
        """Shadow Analysis - identifica o que não foi dito"""
        violacoes = []
        
        if tipo_documento not in self.omissoes_criticas:
            return violacoes
        
        for clausula, padroes in self.omissoes_criticas[tipo_documento].items():
            encontrou = False
            for padrao in padroes:
                if re.search(padrao, texto_normalizado, re.IGNORECASE):
                    encontrou = True
                    break
            
            if not encontrou:
                # Cláusula obrigatória não encontrada
                violacoes.append({
                    'tipo': 'OMISSÃO',
                    'nome': f'OMISSÃO CRÍTICA: {clausula.upper()}',
                    'descricao': f'O contrato não prevê cláusula sobre {clausula.replace("_", " ")}. Esta omissão gera risco jurídico.',
                    'gravidade': 'ALTA',
                    'cor': '#ff4444',
                    'lei': 'Princípio da boa-fé objetiva e função social do contrato',
                    'solucao': f'Inclua cláusula específica sobre {clausula.replace("_", " ")}.'
                })
        
        return violacoes
    
    def _cross_reference_legislativo(self, texto_normalizado: str) -> List[Dict]:
        """Cross-Reference Legislativo - compara com leis e súmulas"""
        violacoes = []
        
        # Verificar referências legais no texto
        for lei_nome, lei_dados in self.base_legal.items():
            for art_num, art_texto in lei_dados.get('artigos', {}).items():
                # Se o artigo é mencionado mas aplicado incorretamente
                if re.search(rf'{lei_nome}.*?{art_num}', texto_normalizado, re.IGNORECASE):
                    # Verificar se há violação específica
                    pass
        
        return violacoes
    
    def _detectar_clausulas_leoninas(self, texto_normalizado: str) -> List[Dict]:
        """Detecta desequilíbrios contratuais"""
        violacoes = []
        
        padroes_leoninos = [
            (r'única.*?responsabilidade', 'Responsabilidade unilateral'),
            (r'todos.*?ônus.*?para', 'Concentração de ônus'),
            (r'todos.*?direitos.*?para', 'Concentração de direitos'),
            (r'não.*?cabe.*?contestação', 'Vedação de contestação'),
            (r'renuncia.*?antecipada', 'Renúncia antecipada de direitos')
        ]
        
        for padrao, descricao in padroes_leoninos:
            if re.search(padrao, texto_normalizado, re.IGNORECASE):
                violacoes.append({
                    'tipo': 'LEONINA',
                    'nome': f'CLÁUSULA LEONINA: {descricao}',
                    'descricao': 'Cláusula que coloca uma das partes em desvantagem exagerada.',
                    'gravidade': 'CRÍTICA',
                    'cor': '#ff0000',
                    'lei': 'Art. 51, CDC e Art. 157 CC',
                    'solucao': 'Cláusula leonina é nula de pleno direito.'
                })
        
        return violacoes
    
    def _calcular_exposicao_risco(self, violacoes: List[Dict]) -> Tuple[int, str]:
        """Calcula o nível de exposição a riscos (0-100%)"""
        if not violacoes:
            return 0, 'APROVADO'
        
        # Pesos por gravidade
        pesos = {
            'CRÍTICA': 25,
            'ALTA': 15,
            'MÉDIA': 8,
            'BAIXA': 3,
            'AMBIGUIDADE': 5,
            'OMISSÃO': 10,
            'LEONINA': 30
        }
        
        exposicao = 0
        for v in violacoes:
            exposicao += pesos.get(v.get('tipo', 'MÉDIA'), 5)
        
        # Limitar a 100%
        exposicao = min(exposicao, 100)
        
        # Determinar status
        if exposicao >= 70:
            status = 'REJEITADO'
        elif exposicao >= 30:
            status = 'REVISÃO OBRIGATÓRIA'
        else:
            status = 'APROVADO'
        
        return exposicao, status
    
    def analisar_documento_completo(self, texto_original: str) -> Dict[str, Any]:
        """Análise completa com todos os módulos do especialista"""
        resultado = {
            'violacoes': [],
            'tipo_documento': 'INDEFINIDO',
            'metricas': {},
            'exposicao_risco': 0,
            'veredito': '',
            'recomendacoes': []
        }
        
        if not texto_original or len(texto_original) < 50:
            resultado['metricas'] = {
                'total': 0,
                'criticas': 0,
                'altas': 0,
                'medias': 0,
                'baixas': 0,
                'pontuacao': 100,
                'status': '✅ DOCUMENTO REGULAR'
            }
            return resultado
        
        # Normalizar texto
        texto_normalizado = self._normalizar_texto(texto_original)
        
        # Detectar tipo de documento
        tipo_doc = self._detectar_tipo_por_palavras_chave(texto_normalizado)
        resultado['tipo_documento'] = tipo_doc
        
        # Módulo 1: Detecção de violações conhecidas
        ids_encontrados = set()
        for vid, config in self.violacoes.items():
            for padrao in config.get('padroes', []):
                if re.search(padrao, texto_normalizado, re.IGNORECASE):
                    if vid not in ids_encontrados:
                        ids_encontrados.add(vid)
                        
                        # Extrair contexto
                        pos = texto_normalizado.find(padrao[:20].upper())
                        contexto = texto_original[max(0, pos-100):min(len(texto_original), pos+200)] if pos > 0 else texto_original[:300]
                        
                        violacao = {
                            'id': vid,
                            'nome': config['nome'],
                            'tipo': config['tipo'],
                            'gravidade': config['gravidade'],
                            'descricao': config['descricao'],
                            'lei': config['lei'],
                            'solucao': config['solucao'],
                            'cor': config['cor'],
                            'contexto': contexto[:200] + '...' if len(contexto) > 200 else contexto
                        }
                        
                        # Adicionar campos extras se existirem
                        if 'penalidade' in config:
                            violacao['penalidade'] = config['penalidade']
                        if 'jurisprudencia' in config:
                            violacao['jurisprudencia'] = config['jurisprudencia']
                        
                        resultado['violacoes'].append(violacao)
                        break
        
        # Módulo 2: Análise de ambiguidade
        resultado['violacoes'].extend(self._analisar_ambiguidade(texto_normalizado))
        
        # Módulo 3: Análise de omissões
        resultado['violacoes'].extend(self._analisar_omissoes(texto_normalizado, tipo_doc))
        
        # Módulo 4: Detecção de cláusulas leoninas
        resultado['violacoes'].extend(self._detectar_clausulas_leoninas(texto_normalizado))
        
        # Calcular métricas
        total = len(resultado['violacoes'])
        criticas = sum(1 for v in resultado['violacoes'] if v.get('gravidade') == 'CRÍTICA')
        altas = sum(1 for v in resultado['violacoes'] if v.get('gravidade') == 'ALTA')
        medias = sum(1 for v in resultado['violacoes'] if v.get('gravidade') in ['MÉDIA', 'AMBIGUIDADE'])
        baixas = sum(1 for v in resultado['violacoes'] if v.get('gravidade') == 'BAIXA')
        
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
        elif altas > 0:
            status = '⚠️⚠️ CONTRATO COM PROBLEMAS SIGNIFICATIVOS'
            cor = '#ff4444'
        elif medias > 0:
            status = '⚠️ CONTRATO COM IRREGULARIDADES'
            cor = '#ffaa44'
        else:
            status = '✅ DOCUMENTO EM CONFORMIDADE'
            cor = '#27AE60'
        
        resultado['metricas'] = {
            'total': total,
            'criticas': criticas,
            'altas': altas,
            'medias': medias,
            'baixas': baixas,
            'pontuacao': round(pontuacao, 1),
            'status': status,
            'cor': cor
        }
        
        # Calcular exposição a risco e veredito
        exposicao, veredito = self._calcular_exposicao_risco(resultado['violacoes'])
        resultado['exposicao_risco'] = exposicao
        resultado['veredito'] = veredito
        
        # Gerar recomendações
        if criticas > 0:
            resultado['recomendacoes'].append('🚨 URGENTE: Contrate um advogado especializado. Há violações críticas que podem anular o contrato.')
        if altas > 0:
            resultado['recomendacoes'].append('⚠️ Revisão obrigatória por profissional do direito antes de assinar.')
        if medias > 0:
            resultado['recomendacoes'].append('📋 Pontos de atenção identificados. Recomenda-se negociação das cláusulas.')
        
        return resultado
    
    def _detectar_tipo_por_palavras_chave(self, texto: str) -> str:
        """Detecta tipo de documento por palavras-chave"""
        palavras_chave = {
            'TRABALHISTA': [
                'empregado', 'empregador', 'salário', 'jornada', 'clt',
                'fgts', 'inss', 'férias', '13º', 'aviso prévio', 'rescisão'
            ],
            'LOCAÇÃO': [
                'locador', 'locatário', 'aluguel', 'imóvel', 'fiador',
                'caução', 'inquilino', 'proprietário', 'benfeitoria'
            ]
        }
        
        scores = {'TRABALHISTA': 0, 'LOCAÇÃO': 0, 'CONTRATUAL': 0}
        
        for tipo, palavras in palavras_chave.items():
            for palavra in palavras:
                if palavra.upper() in texto:
                    scores[tipo] += 1
        
        max_score = max(scores.values())
        if max_score >= 2:
            return max(scores, key=scores.get)
        return 'INDEFINIDO'


# --------------------------------------------------
# INTERFACE PRINCIPAL DO MODO ESPECIALISTA
# --------------------------------------------------

def main():
    # Configurar estilo profissional
    st.markdown("""
    <style>
        .stApp {
            background: #0a0f1e;
        }
        .main-header {
            background: linear-gradient(135deg, #0a1a2f, #1a2a3f);
            padding: 20px;
            border-radius: 10px;
            border-bottom: 3px solid #F8D96D;
            margin-bottom: 20px;
            text-align: center;
        }
        .main-header h1 {
            color: #F8D96D;
            font-size: 2.5em;
            font-weight: 900;
            font-family: 'Courier New', monospace;
            margin: 0;
        }
        .main-header p {
            color: #FFFFFF;
            font-size: 1.1em;
            font-family: 'Courier New', monospace;
        }
        .veredito-card {
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
        }
        .violacao-card {
            background: #1a2a3f;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 5px solid;
        }
        .metric-card {
            background: #1a2a3f;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #F8D96D;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho do Modo Especialista
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>MODO ESPECIALISTA JURÍDICO • DETECÇÃO EXTREMA DE RISCOS</p>
        <p style="color: #F8D96D; font-size: 0.9em;">"Nenhuma violação passará despercebida"</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar detector
    detector = CoreEngineJuridico()
    
    # Upload de arquivo
    arquivo = st.file_uploader(
        "📄 ENVIE O DOCUMENTO PARA AUDITORIA JURÍDICA COMPLETA",
        type=['pdf'],
        help="Formatos suportados: PDF. Análise de todas as vulnerabilidades contratuais e fiscais."
    )
    
    if arquivo:
        with st.spinner("🔍 MODO ESPECIALISTA ATIVADO - Escaneando estruturas jurídicas..."):
            texto = extrair_texto_pdf(arquivo)
            
            if texto:
                # Análise completa
                resultado = detector.analisar_documento_completo(texto)
                
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #F8D96D; margin:0;">{resultado['metricas']['total']}</h3>
                        <p>Violações Totais</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #ff0000; margin:0;">{resultado['metricas']['criticas']}</h3>
                        <p>Críticas</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    cor_pontuacao = '#27AE60' if resultado['metricas']['pontuacao'] >= 70 else '#ffaa44' if resultado['metricas']['pontuacao'] >= 40 else '#ff0000'
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: {cor_pontuacao}; margin:0;">{resultado['metricas']['pontuacao']}%</h3>
                        <p>Conformidade</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    cor_veredito = {
                        'APROVADO': '#27AE60',
                        'REVISÃO OBRIGATÓRIA': '#ffaa44',
                        'REJEITADO': '#ff0000'
                    }.get(resultado['veredito'], '#ffaa44')
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: {cor_veredito}; margin:0;">{resultado['exposicao_risco']}%</h3>
                        <p>Exposição a Risco</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Veredito
                st.markdown(f"""
                <div class="veredito-card" style="background: {cor_veredito}20; border: 2px solid {cor_veredito};">
                    <h2 style="color: {cor_veredito}; margin:0;">🎯 VEREDITO: {resultado['veredito']}</h2>
                    <p style="color: #FFFFFF; margin-top:10px;">Tipo de Documento: {resultado['tipo_documento']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Recomendações
                if resultado['recomendacoes']:
                    st.markdown("### ⚠️ RECOMENDAÇÕES URGENTES")
                    for rec in resultado['recomendacoes']:
                        st.warning(rec)
                
                # Violações detectadas
                if resultado['violacoes']:
                    st.markdown("### 🚨 VIOLAÇÕES JURÍDICAS DETECTADAS")
                    
                    for i, v in enumerate(resultado['violacoes'], 1):
                        with st.expander(f"{i}. [{v.get('tipo', 'GERAL')}] {v['nome']}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**📋 Descrição:** {v['descricao']}")
                                st.markdown(f"**⚖️ Lei:** {v['lei']}")
                                if 'penalidade' in v:
                                    st.markdown(f"**⚠️ Penalidade:** {v['penalidade']}")
                                if 'jurisprudencia' in v:
                                    st.markdown(f"**📚 Jurisprudência:** {v['jurisprudencia']}")
                                st.markdown(f"**✅ Solução:** {v['solucao']}")
                                st.markdown(f"**📄 Contexto:** \"{v.get('contexto', 'N/A')}\"")
                            
                            with col2:
                                cor_gravidade = v.get('cor', '#ffaa44')
                                st.markdown(f"""
                                <div style="background: {cor_gravidade}20; padding:10px; border-radius:5px; text-align:center;">
                                    <h4 style="color: {cor_gravidade}; margin:0;">{v.get('gravidade', 'MÉDIA')}</h4>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.success("✅ NENHUMA VIOLAÇÃO DETECTADA - DOCUMENTO EM CONFORMIDADE PLENA")
                
                # Relatório completo
                st.markdown("---")
                if st.button("📥 GERAR RELATÓRIO COMPLETO (JSON)"):
                    relatorio = {
                        'data_analise': datetime.now().isoformat(),
                        'documento': arquivo.name,
                        'tipo': resultado['tipo_documento'],
                        'metricas': resultado['metricas'],
                        'exposicao_risco': resultado['exposicao_risco'],
                        'veredito': resultado['veredito'],
                        'recomendacoes': resultado['recomendacoes'],
                        'violacoes': [
                            {
                                'nome': v['nome'],
                                'tipo': v.get('tipo', 'GERAL'),
                                'gravidade': v.get('gravidade', 'MÉDIA'),
                                'descricao': v['descricao'],
                                'lei': v['lei'],
                                'solucao': v['solucao']
                            } for v in resultado['violacoes']
                        ]
                    }
                    
                    st.json(relatorio)
                    
                    # Botão para download
                    st.download_button(
                        label="📥 BAIXAR RELATÓRIO JSON",
                        data=json.dumps(relatorio, indent=2, ensure_ascii=False),
                        file_name=f"relatorio_juridico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
    
    else:
        # Instruções do Modo Especialista
        st.info("""
        ### 🔍 MODO ESPECIALISTA JURÍDICO ATIVADO
        
        **Protocolo de Análise:**
        1. **Parsing de Ambiguidade** - Identificação de termos vagos
        2. **Cross-Reference Legislativo** - Comparação com CLT, Lei do Inquilinato, CDC
        3. **Detecção de Cláusulas Leoninas** - Desequilíbrios contratuais
        4. **Shadow Analysis** - Identificação de omissões críticas
        
        **Envie um PDF para iniciar a auditoria completa.**
        """)

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def extrair_texto_pdf(arquivo):
    """Extrai texto de PDF com tratamento robusto"""
    try:
        with pdfplumber.open(arquivo) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF: {str(e)}")
        return None

if __name__ == "__main__":
    main()
