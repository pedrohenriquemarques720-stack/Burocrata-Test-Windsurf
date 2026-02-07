import re

def limpar_texto(texto):
    """Limpa texto removendo caracteres especiais e normalizando"""
    if not texto:
        return ""
    
    # Converter para string se não for
    texto = str(texto)
    
    # Remover caracteres de controle e substituir por espaço
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', texto)
    
    # Normalizar caracteres Unicode
    try:
        import unicodedata
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except:
        pass
    
    # Converter para minúsculas
    texto = texto.lower()
    
    # Remover espaços extras
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

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
                        'regex': r'multa.*correspondente.*12.*meses.*aluguel|multa.*12.*meses|doze.*meses.*aluguel|multa.*integral.*12.*meses|multa.*ano.*inteiro|multa.*período.*restante|multa.*doze.*vezes|12.*vezes.*aluguel',
                        'descricao': '🚨🚨🚨 MULTA DE 12 MESES DE ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º: Multa máxima = 2 meses de aluguel',
                        'detalhe': 'A lei do inquilinato PROÍBE multas superiores a 2 meses de aluguel. Multa de 12 meses é ABUSIVA e NULA!'
                    },
                    {
                        'regex': r'multa.*superior.*2.*meses|multa.*excedente.*2.*meses|multa.*acima.*2.*meses|multa.*maior.*2.*meses|multa.*3.*meses|multa.*4.*meses|multa.*5.*meses|multa.*6.*meses',
                        'descricao': '🚨 MULTA ACIMA DE 2 MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º',
                        'detalhe': 'Multa rescisória não pode exceder 2 meses de aluguel, mesmo que proporcional.'
                    },
                    {
                        'regex': r'multa.*não.*proporcional|multa.*integral.*independentemente.*tempo|multa.*fixa.*sem.*proporcionalidade|multa.*cheia|multa.*inteira',
                        'descricao': '🚨 MULTA SEM PROPORCIONALIDADE - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º + Súmula 595 STJ',
                        'detalhe': 'Multa deve ser proporcional ao tempo cumprido do contrato.'
                    },
                    
                    # CAUÇÃO - CRÍTICAS
                    {
                        'regex': r'depósito.*caução.*três.*meses|caução.*3.*meses|três.*meses.*aluguel.*caução|3.*meses.*depósito|caução.*excessiva|caução.*superior.*1.*mês|caução.*2.*meses|caução.*4.*meses|caução.*5.*meses',
                        'descricao': '🚨🚨 CAUÇÃO DE 3+ MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37: Caução máxima = 1 mês de aluguel',
                        'detalhe': 'Limite legal é apenas 1 mês de aluguel como caução. 3+ meses é ilegal!'
                    },
                    {
                        'regex': r'caução.*superior.*um.*mês|caução.*maior.*1.*mês|depósito.*maior.*1.*mês|caução.*acima.*1.*mês',
                        'descricao': '🚨 CAUÇÃO ACIMA DE 1 MÊS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37',
                        'detalhe': 'Caução não pode exceder 1 mês de aluguel.'
                    },
                    
                    # REAJUSTE - CRÍTICOS
                    {
                        'regex': r'reajuste.*trimestral|reajuste.*a.*cada.*3.*meses|reajuste.*mensalmente|reajuste.*mensal|aumento.*mensal|reajuste.*bimestral|reajuste.*a.*cada.*2.*meses|reajuste.*semestral',
                        'descricao': '🚨 REAJUSTE TRIMESTRAL/MENSAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º: Reajuste mínimo anual (12 meses)',
                        'detalhe': 'Reajustes só podem ser feitos a cada 12 meses no mínimo.'
                    },
                    {
                        'regex': r'reajuste.*sem.*índice.*oficial|reajuste.*livre|reajuste.*conforme.*mercado|reajuste.*acordo|índice.*livre|reajuste.*negociado',
                        'descricao': '🚨 REAJUSTE SEM ÍNDICE OFICIAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices oficiais (IGPM, INCC, IPCA).'
                    },
                    {
                        'regex': r'reajuste.*dólar|reajuste.*variação.*dólar|reajuste.*câmbio|reajuste.*dolar|variação.*cambial',
                        'descricao': '🚨🚨 REAJUSTE PELO DÓLAR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices brasileiros, NÃO o dólar.'
                    },
                    {
                        'regex': r'aumento.*fixo.*20%.*ano|20%.*ao.*ano.*fixo|percentual.*fixo.*20%|aumento.*15%.*fixo|aumento.*10%.*fixo',
                        'descricao': '🚨 AUMENTO FIXO ANUAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Percentuais fixos não seguem inflação oficial.'
                    },
                    
                    # VISITAS E PRIVACIDADE - CRÍTICOS
                    {
                        'regex': r'visitas.*qualquer.*tempo.*sem.*aviso|visitas.*sem.*aviso.*prévio|visitas.*a.*qualquer.*momento|entrar.*qualquer.*hora.*sem.*aviso|ingresso.*imediato.*imóvel|acesso.*livre.*imóvel',
                        'descricao': '🚨🚨 VISITAS SEM AVISO - VIOLAÇÃO DE DOMICÍLIO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991 Art. 23 + Código Penal Art. 150',
                        'detalhe': 'Locador deve avisar com antecedência mínima de 12 horas.'
                    },
                    {
                        'regex': r'ingressar.*imóvel.*qualquer.*momento.*sem.*aviso|acesso.*livre.*imóvel|chave.*disponível.*locador|chave.*entregue.*locador',
                        'descricao': '🚨 INGRESSO LIVRE NO IMÓVEL - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Penal Art. 150 + CDC Art. 51',
                        'detalhe': 'Locatário tem direito à intimidade. Acesso livre é crime!'
                    },
                    {
                        'regex': r'vistorias.*surpresa|vistorias.*sem.*aviso|inspeção.*surpresa|visita.*surpresa',
                        'descricao': '⚠️ VISTORIAS SURPRESA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991',
                        'detalhe': 'Vistorias exigem aviso prévio mínimo de 12 horas.'
                    },
                    
                    # BENFEITORIAS - CRÍTICAS
                    {
                        'regex': r'renúncia.*indenização.*benfeitorias.*necessárias|benfeitorias.*necessárias.*sem.*indenização|renúncia.*retensão.*benfeitorias|abrir.*mão.*benfeitorias|nenhuma.*indenização.*benfeitorias',
                        'descricao': '🚨🚨 RENÚNCIA A BENFEITORIAS NECESSÁRIAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 35 + Lei 8.245/1991',
                        'detalhe': 'Locatário tem direito à indenização por benfeitorias necessárias.'
                    },
                    {
                        'regex': r'benfeitorias.*sem.*direito.*indenização|benfeitorias.*não.*indenizáveis|improvements.*não.*pagos|nenhuma.*benfeitoria.*indenizável',
                        'descricao': '🚨 BENFEITORIAS SEM INDENIZAÇÃO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 35',
                        'detalhe': 'Benfeitorias úteis e necessárias devem ser indenizadas.'
                    },
                    
                    # ANIMAIS - ALTO
                    {
                        'regex': r'vedada.*permanência.*animais|proibido.*animais.*estimação|não.*permitido.*animais|animais.*proibidos|pets.*não.*permitidos|nenhum.*animal|proibição.*total.*animais',
                        'descricao': '⚠️ PROIBIÇÃO DE ANIMAIS - CLAUSULA ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51: Cláusulas abusivas são nulas',
                        'detalhe': 'Proibição total de animais pode ser considerada abusiva.'
                    },
                    
                    # VENDA DO IMÓVEL - ALTO
                    {
                        'regex': r'contrato.*automaticamente.*resciso.*venda|venda.*imóvel.*contrato.*rescindido|retomada.*48.*horas.*venda|venda.*fim.*contrato|venda.*rescisão.*imediata',
                        'descricao': '⚠️ RESCISÃO AUTOMÁTICA POR VENDA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 9º: Contrato segue para novo proprietário',
                        'detalhe': 'Na venda do imóvel, o contrato continua com o novo proprietário.'
                    },
                    {
                        'regex': r'desocupação.*imediata.*venda|despejo.*imediato.*venda|saída.*30.*dias.*venda|desocupação.*15.*dias|desocupação.*7.*dias',
                        'descricao': '🚨 PRAZO DE DESOCUPAÇÃO INFERIOR A 30 DIAS - ILEGAL',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 9º',
                        'detalhe': 'Prazo mínimo para desocupação em caso de venda é 30 dias.'
                    },
                    
                    # RESPONSABILIDADE ESTRUTURAL - CRÍTICA
                    {
                        'regex': r'locatário.*assume.*responsabilidade.*estrutural|dano.*estrutural.*locatário|reparos.*estruturais.*locatário|fundação.*locatário|telhado.*locatário|estrutura.*locatário',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR ESTRUTURA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22: Despesas com estrutura são do locador',
                        'detalhe': 'Telhado, fundação, fiação central e tubulações são responsabilidade do LOCADOR!'
                    },
                    {
                        'regex': r'locatário.*responsável.*vícios.*construção|vícios.*ocultos.*locatário|defeitos.*estrutura.*locatário|problemas.*estrutura.*locatário',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR VÍCIOS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22',
                        'detalhe': 'Vícios construtivos e defeitos ocultos são responsabilidade do locador.'
                    },
                    
                    # PAGAMENTO ANTECIPADO - ALTO
                    {
                        'regex': r'pagamento.*antecipado.*mês.*vencer|aluguel.*primeiro.*dia.*mês|pagamento.*adiantado.*obrigatório|pagamento.*adiantado.*exigido',
                        'descricao': '⚠️ PAGAMENTO ANTECIPADO OBRIGATÓRIO - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 3º',
                        'detalhe': 'Pagamento antecipado só é permitido em locações SEM garantia.'
                    },
                    
                    # IMPOSTO DE RENDA - CRÍTICO
                    {
                        'regex': r'locatário.*pagar.*imposto.*renda.*locador|imposto.*renda.*locatário.*pagar|IR.*locatário.*responsável|locatário.*responsável.*IR',
                        'descricao': '🚨🚨 LOCATÁRIO PAGANDO IR DO LOCADOR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Lei Tributária',
                        'detalhe': 'Imposto de Renda é encargo PESSOAL do contribuinte (locador).'
                    },
                    
                    # DESPEJO - CRÍTICO
                    {
                        'regex': r'despejo.*imediato.*atrasar.*1.*dia|trocar.*fechaduras.*atraso|despejo.*24.*horas|despejo.*48.*horas|despejo.*72.*horas',
                        'descricao': '🚨🚨 DESPEJO IMEDIATO POR 1 DIA DE ATRASO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Código de Processo Civil',
                        'detalhe': 'Despejo só pode ser determinado por ORDEM JUDICIAL após processo legal.'
                    },
                    {
                        'regex': r'multa.*atraso.*10%.*dia|multa.*diária.*excessiva|penalidade.*diária.*atraso|multa.*5%.*dia|multa.*diária.*5%',
                        'descricao': '⚠️ MULTA DIÁRIA EXCESSIVA - ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51',
                        'detalhe': 'Multa diária excessiva pode ser considerada abusiva.'
                    },
                    
                    # CUMULAÇÃO DE GARANTIAS - ALTO
                    {
                        'regex': r'cumulação.*modalidades.*garantia|caução.*E.*fiador|seguro.*E.*caução|múltiplas.*garantias|garantias.*cumulativas',
                        'descricao': '⚠️ CUMULAÇÃO DE GARANTIAS - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 37',
                        'detalhe': 'É proibida a cumulação de modalidades de garantia.'
                    }
                ]
            },
            'CONTRATO_TRABALHO': {
                'nome': 'Contrato de Trabalho',
                'padroes': [
                    # SALÁRIO - CRÍTICOS
                    {
                        'regex': r'salário.*mensal.*bruto.*R\$\s*900|R\$\s*900[,\.]00|900.*reais|novecentos.*reais|salário.*R\$\s*800|800.*reais|salário.*R\$\s*1000|1000.*reais|salário.*R\$\s*1100|1100.*reais|salário.*R\$\s*1200|1200.*reais|salário.*R\$\s*1300|1300.*reais',
                        'descricao': '🚨🚨🚨 SALÁRIO ABAIXO DO MÍNIMO - TRABALHO ESCRAVO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º IV',
                        'detalhe': 'Salário mínimo atual (2024): R$ 1.412,00. Valores abaixo disso são CRIME!'
                    },
                    {
                        'regex': r'salário.*inferior.*mínimo|salário.*abaixo.*mínimo|remuneração.*abaixo.*mínimo|salário.*menor.*mínimo',
                        'descricao': '🚨🚨 SALÁRIO INFERIOR AO MÍNIMO CONSTITUCIONAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º IV',
                        'detalhe': 'Nenhum trabalhador pode receber menos que o salário mínimo.'
                    },
                    {
                        'regex': r'salário.*base.*menor.*mínimo|salário.*comissão.*sem.*fixo|remuneração.*variável.*sem.*garantia|salário.*apenas.*comissão',
                        'descricao': '🚨 SALÁRIO SEM GARANTIA MÍNIMA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º VII + CLT Art. 458',
                        'detalhe': 'Salário deve ter valor fixo nunca inferior ao mínimo.'
                    },
                    
                    # JORNADA - CRÍTICAS
                    {
                        'regex': r'jornada.*das\s*08:00.*às\s*20:00|08:00.*20:00|das\s*08.*às\s*20|jornada.*60.*horas.*semanais|60.*horas.*semanais|12.*horas.*diárias|jornada.*13.*horas|jornada.*14.*horas',
                        'descricao': '🚨🚨 JORNADA EXCESSIVA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58: Máximo 8h diárias / 44h semanais',
                        'detalhe': '12h+ diárias = 50%+ ACIMA do limite! 60h semanais = 36% ACIMA!'
                    },
                    {
                        'regex': r'jornada.*superior.*8.*horas|jornada.*acima.*8.*horas|trabalhar.*mais.*8.*horas|carga.*horária.*excessiva|jornada.*9.*horas|jornada.*10.*horas',
                        'descricao': '🚨 JORNADA ACIMA DE 8 HORAS DIÁRIAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58',
                        'detalhe': 'Jornada normal não pode exceder 8 horas diárias.'
                    },
                    {
                        'regex': r'jornada.*semanal.*superior.*44.*horas|44.*horas.*semanais.*ultrapassada|carga.*horária.*semanal.*excessiva|jornada.*45.*horas|jornada.*50.*horas',
                        'descricao': '🚨 JORNADA SEMANAL ACIMA DE 44 HORAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58',
                        'detalhe': 'Limite semanal é 44 horas. Acima disso só com horas extras.'
                    },
                    
                    # HORAS EXTRAS - CRÍTICAS
                    {
                        'regex': r'não.*haverá.*pagamento.*horas.*extras|sem.*pagamento.*horas.*extras|sem.*direito.*horas.*extras|horas.*extras.*não.*remuneradas|horas.*extras.*gratuitas',
                        'descricao': '🚨🚨 SEM PAGAMENTO DE HORAS EXTRAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 59: Horas extras obrigatórias após 8h/dia',
                        'detalhe': 'Horas extras são DIREITO do trabalhador e DEVEM ser pagas!'
                    },
                    {
                        'regex': r'horas.*extras.*sem.*adicional|horas.*extras.*50%|adicional.*horas.*extras.*negado|horas.*extras.*sem.*adicional',
                        'descricao': '🚨 HORAS EXTRAS SEM ADICIONAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 59: Adicional mínimo de 50%',
                        'detalhe': 'Horas extras devem ter adicional mínimo de 50% sobre hora normal.'
                    },
                    
                    # INTERVALOS - CRÍTICOS
                    {
                        'regex': r'23:00.*retornar.*06:00|encerrar.*23:00.*retornar.*06:00|intervalo.*interjornada.*7.*horas|7.*horas.*descanso|intervalo.*8.*horas|intervalo.*6.*horas',
                        'descricao': '🚨🚨 INTERVALO INTERJORNADA DE 7 HORAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 66: Mínimo 11 horas entre jornadas',
                        'detalhe': '7-8 horas entre jornadas = 36%+ ABAIXO do mínimo de 11h!'
                    },
                    {
                        'regex': r'intervalo.*refeição.*30.*minutos|30.*minutos.*refeição|intervalo.*10.*minutos|10.*minutos.*almoço|intervalo.*inferior.*1.*hora|intervalo.*45.*minutos',
                        'descricao': '🚨 INTERVALO INSUFICIENTE PARA REFEIÇÃO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 71: Mínimo 1 hora para jornada >6h',
                        'detalhe': '30-45 minutos = 50%+ ABAIXO do mínimo! 10 minutos = VIOLAÇÃO!'
                    },
                    {
                        'regex': r'intervalo.*descanso.*15.*minutos|15.*minutos.*descanso|intervalo.*reduzido|intervalo.*20.*minutos',
                        'descricao': '⚠️ INTERVALO REDUZIDO ILEGALMENTE',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 71',
                        'detalhe': 'Intervalo mínimo de 15 minutos só para jornadas até 4 horas.'
                    },
                    
                    # FGTS - CRÍTICOS
                    {
                        'regex': r'renúncia.*FGTS|renúncia.*Fundo.*Garantia|Vale.*Cultura.*substituição.*FGTS|FGTS.*descontado.*folha.*pagamento|não.*terá.*FGTS|sem.*FGTS',
                        'descricao': '🚨🚨🚨 RENÚNCIA AO FGTS - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.036/1990 Art. 15: FGTS é OBRIGATÓRIO',
                        'detalhe': 'FGTS é DIREITO IRRENUNCIÁVEL! "Vale Cultura" NÃO substitui FGTS!'
                    },
                    {
                        'regex': r'FGTS.*opcional|FGTS.*não.*obrigatório|dispensa.*FGTS|FGTS.*facultativo',
                        'descricao': '🚨🚨 FGTS TRATADO COMO OPCIONAL - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.036/1990',
                        'detalhe': 'FGTS é obrigatório por lei. Não pode ser opcional.'
                    },
                    
                    # FÉRIAS - CRÍTICAS
                    {
                        'regex': r'renúncia.*férias.*remuneradas|renúncia.*férias.*24.*meses|férias.*não.*remuneradas|sem.*direito.*férias|férias.*renunciadas',
                        'descricao': '🚨 RENÚNCIA A FÉRIAS REMUNERADAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 130: Férias são direito irrenunciável',
                        'detalhe': 'Férias remuneradas são DIREITO IRRENUNCIÁVEL do trabalhador!'
                    },
                    {
                        'regex': r'férias.*proporcionais.*negadas|férias.*vencidas.*não.*pagas|férias.*acumuladas|férias.*não.*pagas',
                        'descricao': '🚨 FÉRIAS NÃO PAGAS OU NEGADAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 129 a 145',
                        'detalhe': 'Férias vencidas devem ser pagas em dobro.'
                    },
                    
                    # DISCRIMINAÇÃO - CRÍTICAS
                    {
                        'regex': r'gravidez.*contrato.*resciso|gravidez.*demissão.*sem.*ônus|demissão.*gestante|rescisão.*gravidez|gestante.*demissão',
                        'descricao': '🚨🚨 DISCRIMINAÇÃO POR GRAVIDEZ - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 391-A + Lei 9.029/1995',
                        'detalhe': 'Estabilidade provisória da gestante é GARANTIDA. Rescisão é DISCRIMINAÇÃO!'
                    },
                    {
                        'regex': r'discriminação.*gênero|discriminação.*raça|discriminação.*religião|discriminação.*orientação.*sexual|discriminação.*idade',
                        'descricao': '🚨🚨 CLÁUSULA DISCRIMINATÓRIA - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 3º + Lei 9.029/1995',
                        'detalhe': 'Discriminação em contrato de trabalho é crime inafiançável!'
                    },
                    
                    # CTPS - CRÍTICAS
                    {
                        'regex': r'CTPS.*retida.*empresa|retenção.*CTPS|Carteira.*Trabalho.*retida|não.*entregar.*CTPS|CTPS.*empregador',
                        'descricao': '🚨 RETENÇÃO DE CTPS - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 29 + Lei 5.553/1968',
                        'detalhe': 'Retenção de CTPS é CRIME e contravenção penal!'
                    },
                    
                    # DESCONTOS ILEGAIS - ALTOS
                    {
                        'regex': r'custo.*manutenção.*descontado.*salário|equipamentos.*descontado.*salário|uniforme.*descontado|ferramentas.*descontadas|material.*descontado',
                        'descricao': '⚠️ DESCONTO ILEGAL POR EQUIPAMENTOS',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 462',
                        'detalhe': 'Risco do negócio é do empregador. Custo de equipamentos não pode ser descontado.'
                    },
                    {
                        'regex': r'desconto.*atraso.*excessivo|multa.*atraso.*salário|desconto.*falta.*excessivo|multa.*5%.*dia|multa.*10%.*dia',
                        'descricao': '⚠️ DESCONTO POR ATRASO EXCESSIVO - ABUSIVO',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 462 + Súmula 18 TST',
                        'detalhe': 'Desconto por atraso não pode exceder 5% do salário.'
                    },
                    
                    # JUSTA CAUSA - ALTOS
                    {
                        'regex': r'erro.*técnico.*justa.*causa|justa.*causa.*imediata.*erro|falta.*grave.*justa.*causa|pequeno.*erro.*justa.*causa',
                        'descricao': '⚠️ JUSTA CAUSA ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 482',
                        'detalhe': 'Rigor excessivo e falta de gradação de pena.'
                    },
                    {
                        'regex': r'justa.*causa.*vaga|justa.*causa.*genérica|qualquer.*falta.*justa.*causa|justa.*causa.*discricionária',
                        'descricao': '⚠️ JUSTA CAUSA GENÉRICA - ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 482',
                        'detalhe': 'Justa causa deve ser específica e comprovada.'
                    },
                    
                    # RESPONSABILIDADE CIVIL - CRÍTICOS
                    {
                        'regex': r'funcionário.*responde.*patrimônio.*pessoal|responsabilidade.*civil.*patrimônio.*pessoal|bens.*pessoais.*garantia|patrimônio.*pessoal.*responsável',
                        'descricao': '🚨 RESPONSABILIDADE CIVIL ABUSIVA',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil + Jurisprudência trabalhista',
                        'detalhe': 'Responsabilidade civil objetiva abusiva. Empregado não responde com patrimônio pessoal.'
                    },
                    {
                        'regex': r'danos.*lucros.*cessantes.*ilimitados|responsabilidade.*integral.*danos|indenização.*ilimitada|responsabilidade.*total.*danos',
                        'descricao': '🚨 RESPONSABILIDADE ILIMITADA POR DANOS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 462',
                        'detalhe': 'Responsabilidade por danos deve ser limitada e comprovada o dolo.'
                    },
                    
                    # CLÁUSULAS ABUSIVAS - CRÍTICOS
                    {
                        'regex': r'Cláusula.*Abusiva|cláusula.*abusiva|contrato.*contém.*abusividade|cláusula.*excessivamente.*onerosa',
                        'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO ABUSIVA PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51',
                        'detalhe': 'O próprio contrato reconhece que contém cláusulas abusivas!'
                    },
                    {
                        'regex': r'Cláusula.*Ilegal|cláusula.*ilegal|contrato.*ilegalidade|cláusula.*contrária.*lei',
                        'descricao': '🚨🚨 CLÁUSULA IDENTIFICADA COMO ILEGAL PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação trabalhista',
                        'detalhe': 'O contrato ADMITE conter cláusulas ilegais!'
                    },
                    {
                        'regex': r'Cláusula.*Nula|cláusula.*nula|nulidade.*cláusula|cláusula.*sem.*efeito',
                        'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO NULA PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação aplicável',
                        'detalhe': 'O contrato reconhece que possui cláusulas sem valor jurídico!'
                    }
                ]
            },
            'NOTA_FISCAL': {
                'nome': 'Nota Fiscal',
                'padroes': [
                    # DATA DE EMISSÃO - CRÍTICAS
                    {
                        'regex': r'data.*emissão.*futura|data.*emissão.*posterior|nota.*fiscal.*futura|emissão.*futura|data.*futura|data.*posterior',
                        'descricao': '🚨🚨 NOTA FISCAL COM DATA FUTURA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 5.172/1966 + Convênio SINIEF',
                        'detalhe': 'Nota fiscal não pode ter data de emissão futura. É crime tributário!'
                    },
                    {
                        'regex': r'data.*emissão.*anterior.*prestação|data.*emissão.*retroativa|emissão.*retroativa|nota.*fiscal.*retroativa',
                        'descricao': '🚨 NOTA FISCAL COM DATA RETROATIVA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Data de emissão deve ser contemporânea à prestação do serviço.'
                    },
                    
                    # CANCELAMENTO - CRÍTICAS
                    {
                        'regex': r'nota.*fiscal.*cancelada|cancelamento.*indevido|duplo.*cancelamento|cancelada.*sem.*justificativa|cancelamento.*abuso',
                        'descricao': '🚨 NOTA FISCAL CANCELADA - VERIFICAR!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Nota cancelada não tem validade fiscal. Verificar se cancelamento foi legítimo.'
                    },
                    {
                        'regex': r'cancelamento.*posterior.*30.*dias|cancelamento.*tardia|cancelamento.*fora.*prazo|cancelamento.*indevido.*prazo',
                        'descricao': '⚠️ CANCELAMENTO FORA DO PRAZO LEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Cancelamento deve ocorrer dentro do prazo legal.'
                    },
                    
                    # DADOS DO EMITENTE - ALTOS
                    {
                        'regex': r'CNPJ.*inválido|CNPJ.*inexistente|inscrição.*municipal.*inválida|emitente.*não.*habilitado|emitente.*irregular',
                        'descricao': '⚠️ DADOS DO EMITENTE IRREGULARES',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Emitente deve ter CNPJ e inscrição municipal válidos.'
                    },
                    {
                        'regex': r'nome.*emitente.*diferente|razão.*social.*diferente|emitente.*não.*corresponde|dados.*emitente.*incorretos',
                        'descricao': '⚠️ DADOS DO EMITENTE INCORRETOS',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Dados do emitente devem corresponder ao prestador real do serviço.'
                    },
                    
                    # VALORES - CRÍTICOS
                    {
                        'regex': r'valor.*zero.*serviço|R\$\s*0,00|valor.*nulo|sem.*valor|valor.*inexistente|grátis.*nota.*fiscal',
                        'descricao': '🚨 NOTA FISCAL COM VALOR ZERO - SUSPEITA!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Nota fiscal com valor zero pode indicar fraude fiscal.'
                    },
                    {
                        'regex': r'valor.*diferente.*contrato|valor.*divergente|valor.*incompatível|valor.*excessivo|valor.*subfaturado',
                        'descricao': '⚠️ VALOR INCOMPATÍVEL COM SERVIÇO PRESTADO',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Valor da nota deve corresponder ao serviço efetivamente prestado.'
                    },
                    {
                        'regex': r'base.*cálculo.*zero|base.*cálculo.*inexistente|sem.*base.*cálculo|base.*cálculo.*negativa',
                        'descricao': '🚨 BASE DE CÁLCULO ZERO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Base de cálculo não pode ser zero para serviços prestados.'
                    },
                    
                    # TRIBUTAÇÃO - CRÍTICAS
                    {
                        'regex': r'alíquota.*zero|alíquota.*inexistente|sem.*alíquota|alíquota.*negativa|alíquota.*indevida',
                        'descricao': '🚨 ALÍQUOTA ILEGAL OU INEXISTENTE',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária municipal',
                        'detalhe': 'Alíquota deve seguir tabela oficial do município.'
                    },
                    {
                        'regex': r'ISS.*não.*recolhido|ISS.*retido.*indevidamente|ISS.*sonegado|tributo.*não.*pago|sonegação.*fiscal',
                        'descricao': '🚨🚨 TRIBUTO NÃO RECOLHIDO - CRIME FISCAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 5.172/1966 + Lei 8.137/1990',
                        'detalhe': 'Não recolher ISS é crime de sonegação fiscal!'
                    },
                    {
                        'regex': r'ISSQN.*fora.*município|ISS.*município.*errado|tributação.*município.*incorreto|local.*prestação.*diferente',
                        'descricao': '🚨 ISS RECOLHIDO PARA MUNICÍPIO ERRADO',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei Complementar 116/2003',
                        'detalhe': 'ISS deve ser recolhido para o município da prestação do serviço.'
                    },
                    
                    # DESCRIÇÃO DOS SERVIÇOS - ALTOS
                    {
                        'regex': r'serviço.*não.*descrito|descrição.*vazia|sem.*descrição|descrição.*inexistente|serviço.*genérico',
                        'descricao': '⚠️ DESCRIÇÃO DE SERVIÇO INSUFICIENTE',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Descrição do serviço deve ser clara e detalhada.'
                    },
                    {
                        'regex': r'descrição.*genérica.*"serviços"|descrição.*"outros"|descrição.*"diversos"|descrição.*padrão',
                        'descricao': '⚠️ DESCRIÇÃO GENÉRICA DE SERVIÇOS',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Descrições genéricas podem indicar irregularidade.'
                    },
                    {
                        'regex': r'código.*serviço.*inválido|código.*serviço.*inexistente|código.*serviço.*errado|LC.*116.*errado',
                        'descricao': '⚠️ CÓDIGO DE SERVIÇO INCORRETO',
                        'gravidade': 'ALTA',
                        'lei': 'Lei Complementar 116/2003',
                        'detalhe': 'Código do serviço deve seguir tabela LC 116/2003.'
                    },
                    
                    # VERIFICAÇÃO DE AUTENTICIDADE - CRÍTICAS
                    {
                        'regex': r'número.*nota.*duplicado|número.*duplicado|nota.*fiscal.*duplicada|mesmo.*número.*emitente',
                        'descricao': '🚨 NÚMERO DE NOTA FISCAL DUPLICADO',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Cada nota fiscal deve ter número único por emitente.'
                    },
                    {
                        'regex': r'nota.*fiscal.*não.*verificada|não.*encontrada.*sistema|autenticidade.*não.*confirmada|validação.*falhou',
                        'descricao': '🚨 NOTA FISCAL NÃO ENCONTRADA NO SISTEMA',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Nota fiscal deve ser registrada e verificável no sistema oficial.'
                    },
                    
                    # FORMATO E EMISSÃO - ALTOS
                    {
                        'regex': r'nota.*fiscal.*manual|emissão.*manual|sem.*sistema|fora.*sistema|emissão.*papel',
                        'descricao': '⚠️ NOTA FISCAL EMITIDA MANUALMENTE',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Notas fiscais devem ser emitidas por sistema eletrônico.'
                    },
                    {
                        'regex': r'nota.*fiscal.*sem.*assinatura|sem.*carimbo|sem.*autenticação|sem.*validação',
                        'descricao': '⚠️ NOTA FISCAL SEM ASSINATURA/AUTENTICAÇÃO',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Nota fiscal deve ser devidamente assinada/autenticada.'
                    },
                    
                    # REGULARIDADE FISCAL - CRÍTICAS
                    {
                        'regex': r'emitente.*débito.*fiscal|emitente.*irregular|emitente.*não.*habilitado|empresa.*suspensa|empresa.*baixada',
                        'descricao': '🚨🚨 EMITENTE COM DÉBITO FISCAL OU IRREGULAR',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Emitente deve estar regular com o fisco municipal.'
                    },
                    {
                        'regex': r'inscrição.*municipal.*cancelada|inscrição.*suspensa|inscrição.*baixada|empresa.*inapta',
                        'descricao': '🚨 EMITENTE COM INSCRIÇÃO MUNICIPAL CANCELADA',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Inscrição municipal cancelada indica irregularidade grave.'
                    },
                    
                    # COMPETÊNCIA TRIBUTÁRIA - ALTOS
                    {
                        'regex': r'competência.*errada|período.*competência.*incorreto|mês.*competência.*diferente|ano.*competência.*errado',
                        'descricao': '⚠️ COMPETÊNCIA TRIBUTÁRIA INCORRETA',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Período de competência deve corresponder à prestação do serviço.'
                    },
                    {
                        'regex': r'local.*prestação.*diferente.*serviço|local.*incorreto|município.*errado|endereço.*prestação.*diferente',
                        'descricao': '⚠️ LOCAL DE PRESTAÇÃO DE SERVIÇO INCORRETO',
                        'gravidade': 'ALTA',
                        'lei': 'Lei Complementar 116/2003',
                        'detalhe': 'Local da prestação deve ser corretamente informado.'
                    },
                    
                    # RETENÇÕES - ALTOS
                    {
                        'regex': r'retenção.*indevida|retenção.*excessiva|retenção.*sem.*fundamento|IRRF.*retido.*indevidamente|PIS.*COFINS.*retenção',
                        'descricao': '⚠️ RETENÇÃO TRIBUTÁRIA INDEVIDA',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Retenções devem seguir legislação específica.'
                    },
                    {
                        'regex': r'alíquota.*retenção.*errada|percentual.*retenção.*incorreto|retenção.*maior.*devido|retenção.*menor.*devido',
                        'descricao': '⚠️ ALÍQUOTA DE RETENÇÃO INCORRETA',
                        'gravidade': 'ALTA',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Alíquotas de retenção devem seguir tabelas oficiais.'
                    }
                ]
            }
        }
        
        # Análise genérica SUPER avançada - COBERTURA MÁXIMA (SEM DUPLICAÇÃO)
        # Padrões genéricos que NÃO estão cobertos na análise específica
        self.padroes_genericos = [
            # SALÁRIO - CRÍTICOS (VALORES EXTREMAMENTE BAIXOS NÃO COBERTOS NA ANÁLISE ESPECÍFICA)
            (r'\b500\b.*reais|\bR\$\s*500\b|\b600\b.*reais|\bR\$\s*600\b|\b700\b.*reais|\bR\$\s*700\b|\b750\b.*reais|\bR\$\s*750\b', 'SALARIO_EXTREMO_BAIXO', '🚨🚨 SALÁRIO EXTREMAMENTE BAIXO - CRIME', 'CRÍTICA'),
            
            # MULTAS - CRÍTICAS (VARIAÇÕES ESPECÍFICAS NÃO COBERTAS)
            (r'multa.*6.*meses|multa.*8.*meses|multa.*9.*meses|multa.*10.*meses', 'MULTA_ACIMA_PERMITIDA', '🚨 MULTA ACIMA DE 2 MESES - ILEGAL', 'CRÍTICA'),
            (r'multa.*integral.*independentemente|multa.*fixa.*sem.*proporcionalidade', 'MULTA_SEM_PROPORCIONALIDADE', '🚨 MULTA SEM PROPORCIONALIDADE', 'CRÍTICA'),
            
            # CAUÇÃO ESPECÍFICA - CRÍTICAS
            (r'caução.*2.*meses|caução.*4.*meses|caução.*5.*meses|caução.*6.*meses', 'CAUCAO_ACIMA_PERMITIDA', '🚨 CAUÇÃO ACIMA DE 1 MÊS - ILEGAL', 'CRÍTICA'),
            
            # REAJUSTE ESPECÍFICO - CRÍTICOS
            (r'reajuste.*a.*cada.*2.*meses|reajuste.*a.*cada.*3.*meses|reajuste.*a.*cada.*6.*meses', 'REAJUSTE_PERIODO_CURTO', '🚨 REAJUSTE COM PERÍODO CURTO - ILEGAL', 'CRÍTICA'),
            (r'aumento.*fixo.*10%.*ano|aumento.*fixo.*15%.*ano|aumento.*fixo.*20%.*ano', 'AUMENTO_FIXO_ANUAL', '🚨 AUMENTO FIXO ANUAL - ILEGAL', 'CRÍTICA'),
            
            # JORNADA ESPECÍFICA - CRÍTICAS (EXTREMAS)
            (r'\b24\b.*horas.*trabalho|24.*horas.*diárias|trabalhar.*24.*horas', 'JORNADA_24_HORAS', '🚨 JORNADA DE 24 HORAS - IMPOSSÍVEL/ILEGAL', 'CRÍTICA'),
            (r'\b18\b.*horas.*trabalho|18.*horas.*diárias|trabalhar.*18.*horas', 'JORNADA_18_HORAS', '🚨 JORNADA DE 18 HORAS - EXTREMAMENTE ILEGAL', 'CRÍTICA'),
            (r'\b16\b.*horas.*trabalho|16.*horas.*diárias|trabalhar.*16.*horas', 'JORNADA_16_HORAS', '🚨 JORNADA DE 16 HORAS - EXTREMAMENTE ILEGAL', 'CRÍTICA'),
            
            # INTERVALO ESPECÍFICO - CRÍTICOS
            (r'intervalo.*20.*minutos|intervalo.*25.*minutos|intervalo.*35.*minutos', 'INTERVALO_REFEICAO_MUITO_CURTO', '🚨 INTERVALO DE REFEIÇÃO MUITO CURTO', 'CRÍTICA'),
            (r'intervalo.*9.*horas|intervalo.*10.*horas|intervalo.*5.*horas|intervalo.*6.*horas', 'INTERVALO_INTERJORNADA_MUITO_CURTO', '🚨 INTERVALO INTERJORNADA MUITO CURTO', 'CRÍTICA'),
            
            # TRIBUTAÇÃO ESPECÍFICA - CRÍTICAS
            (r'alíquota.*zero|alíquota.*inexistente|sem.*alíquota|alíquota.*negativa', 'ALIQUOTA_ILEGAL', '🚨 ALÍQUOTA ILEGAL OU INEXISTENTE', 'CRÍTICA'),
            (r'ISSQN.*fora.*município|ISS.*município.*errado|tributação.*municipal.*incorreto', 'ISS_MUNICIPIO_ERRADO', '🚨 ISS RECOLHIDO PARA MUNICÍPIO ERRADO', 'CRÍTICA'),
            
            # CLÁUSULAS ABUSIVAS - CRÍTICAS
            (r'Cláusula.*Abusiva|cláusula.*abusiva|contrato.*contém.*abusividade', 'CLAUSULA_ABUSIVA', '🚨 CLÁUSULA IDENTIFICADA COMO ABUSIVA', 'CRÍTICA'),
            (r'Cláusula.*Ilegal|cláusula.*ilegal|contrato.*ilegalidade|cláusula.*contrária.*lei', 'CLAUSULA_ILEGAL', '🚨🚨 CLÁUSULA IDENTIFICADA COMO ILEGAL', 'CRÍTICA'),
            (r'Cláusula.*Nula|cláusula.*nula|nulidade.*cláusula|cláusula.*sem.*efeito', 'CLAUSULA_NULA', '🚨 CLÁUSULA IDENTIFICADA COMO NULA', 'CRÍTICA'),
            
            # RETENÇÕES ESPECÍFICAS - ALTOS
            (r'retenção.*indevida|retenção.*excessiva|retenção.*sem.*fundamento', 'RETENCAO_INDEVIDA', '⚠️ RETENÇÃO TRIBUTÁRIA INDEVIDA', 'ALTA'),
            (r'alíquota.*retenção.*errada|percentual.*retenção.*incorreto', 'ALIQUOTA_RETENCAO_ERRADA', '⚠️ ALÍQUOTA DE RETENÇÃO INCORRETA', 'ALTA'),
            
            # CLÁUSULAS ESPECÍFICAS - CRÍTICAS
            (r'cláusula.*excessivamente.*onerosa|cláusula.*onerosa.*excessivo', 'CLAUSULA_EXCESSIVAMENTE_ONEROSA', '🚨 CLÁUSULA EXCESSIVAMENTE ONEROSA', 'CRÍTICA'),
            (r'cláusula.*limita.*direitos|cláusula.*restringe.*direitos', 'CLAUSULA_LIMITA_DIREITOS', '🚨 CLÁUSULA QUE LIMITA DIREITOS', 'CRÍTICA'),
            
            # DETECÇÃO DE PADRÕES ABUSIVOS - CRÍTICOS
            (r'obrigação.*excessiva|ônus.*excessivo|encargo.*excessivo|dever.*excessivo', 'ONUS_EXCESSIVO', '🚨 ÔNUS EXCESSIVO - CLÁUSULA ABUSIVA', 'CRÍTICA'),
            (r'desvantagem.*excessiva|prejuízo.*excessivo|sacrifício.*excessivo', 'DESVANTAGEM_EXCESSIVA', '🚨 DESVANTAGEM EXCESSIVA - CLÁUSULA ABUSIVA', 'CRÍTICA'),
            
            # DETECÇÃO DE VIOLAÇÕES DIRETAS - CRÍTICAS
            (r'violação.*direito|violação.*garantia|violação.*constituição|violação.*lei', 'VIOLACAO_DIREITO', '🚨 VIOLAÇÃO DIRETA DE DIREITOS', 'CRÍTICA'),
            (r'contrário.*lei|contrária.*constituição|ilegal.*expressamente', 'CONTRARIO_LEI', '🚨 CLÁUSULA CONTRÁRIA À LEI', 'CRÍTICA'),
            
            # DETECÇÃO DE RISCOS - ALTOS
            (r'risco.*excessivo|perigo.*excessivo|dano.*potencial.*grave', 'RISCO_EXCESSIVO', '⚠️ RISCO EXCESSIVO - CLÁUSULA PERIGOSA', 'ALTA'),
            (r'prejudica.*direito|prejudica.*garantia|prejudica.*interesse', 'PREJUDICA_DIREITO', '⚠️ CLÁUSULA QUE PREJUDICA DIREITOS', 'ALTA')
        ]
    
    def detectar_tipo_documento(self, texto):
        """Detecção ULTRA precisa do tipo de documento"""
        if not texto:
            return 'DESCONHECIDO'
        
        texto_limpo = limpar_texto(texto).lower()
        
        # Verificação direta por termos chave - PRIORIDADE MÁXIMA
        if 'nota fiscal' in texto_limpo or 'nfse' in texto_limpo or 'nfe' in texto_limpo:
            return 'NOTA_FISCAL'
        
        if 'empregador' in texto_limpo and 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        
        if 'locação' in texto_limpo or ('locador' in texto_limpo and 'locatário' in texto_limpo):
            return 'CONTRATO_LOCACAO'
        
        # Contagem de termos para documentos específicos
        scores = {
            'CONTRATO_LOCACAO': 0,
            'CONTRATO_TRABALHO': 0,
            'NOTA_FISCAL': 0
        }
        
        # Termos para contratos de locação
        termos_locacao = ['locação', 'aluguel', 'locador', 'locatário', 'imóvel', 'caução', 'fiador', 'benfeitorias', 'multa rescisória', 'inquilino', 'proprietário', 'Lei 8.245/1991', 'contrato de aluguel', 'imóvel residencial']
        for termo in termos_locacao:
            if termo in texto_limpo:
                scores['CONTRATO_LOCACAO'] += 1
        
        # Termos para contratos de trabalho
        termos_trabalho = ['empregador', 'empregado', 'CLT', 'salário', 'jornada', 'horas extras', 'FGTS', 'férias', '13º salário', 'funcionário', 'trabalhador', 'contrato de trabalho', 'carteira de trabalho', 'holerite', 'CAGED', 'PIS']
        for termo in termos_trabalho:
            if termo in texto_limpo:
                scores['CONTRATO_TRABALHO'] += 1
        
        # Termos para notas fiscais
        termos_nota = ['nota fiscal', 'nfse', 'nfe', 'prefeitura municipal', 'prestador de serviços', 'tomador de serviços', 'iss', 'imposto', 'CNPJ', 'inscrição municipal', 'base de cálculo', 'alíquota', 'competência', 'autenticação', 'verificação']
        for termo in termos_nota:
            if termo in texto_limpo:
                scores['NOTA_FISCAL'] += 1
        
        # Retornar tipo com maior score (se houver score > 0)
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return 'DESCONHECIDO'
    
    def analisar_documento(self, texto):
        """Análise SUPER avançada do documento"""
        if not texto:
            return self._resultado_vazio()
        
        texto_limpo = limpar_texto(texto)
        tipo_documento = self.detectar_tipo_documento(texto)
        
        problemas = []
        score = 100
        
        # Análise específica por tipo
        if tipo_documento in self.padroes:
            for padrao in self.padroes[tipo_documento]['padroes']:
                if re.search(padrao['regex'], texto_limpo, re.IGNORECASE):
                    problemas.append({
                        'descricao': padrao['descricao'],
                        'gravidade': padrao['gravidade'],
                        'lei': padrao['lei'],
                        'detalhe': padrao['detalhe'],
                        'tipo': tipo_documento
                    })
                    
                    # Reduzir score conforme gravidade
                    if padrao['gravidade'] == 'CRÍTICA':
                        score -= 25
                    elif padrao['gravidade'] == 'ALTA':
                        score -= 15
                    elif padrao['gravidade'] == 'MÉDIA':
                        score -= 10
                    else:
                        score -= 5
        
        # Análise genérica SUPER avançada - COBERTURA MÁXIMA
        for regex, tipo, desc, gravidade in self.padroes_genericos:
            if re.search(regex, texto_limpo, re.IGNORECASE):
                # Evitar duplicação de problemas
                problema_existente = False
                for problema in problemas:
                    if desc == problema['descricao']:
                        problema_existente = True
                        break
                
                if not problema_existente:
                    problemas.append({
                        'descricao': desc,
                        'gravidade': gravidade,
                        'lei': 'Legislação aplicável',
                        'detalhe': 'Detectado através de análise de padrões avançados',
                        'tipo': 'Geral'
                    })
                    
                    if gravidade == 'CRÍTICA':
                        score -= 20
                    elif gravidade == 'ALTA':
                        score -= 10
                    elif gravidade == 'MÉDIA':
                        score -= 5
                    else:
                        score -= 2
        
        # Garantir que score não seja negativo
        score = max(0, score)
        
        # Classificar problemas
        criticos = len([p for p in problemas if p['gravidade'] == 'CRÍTICA'])
        altos = len([p for p in problemas if p['gravidade'] == 'ALTA'])
        medios = len([p for p in problemas if p['gravidade'] == 'MÉDIA'])
        info = len([p for p in problemas if p['gravidade'] == 'BAIXA'])
        
        total = len(problemas)
        
        # Determinar status com base na gravidade
        if criticos >= 3:
            status = '🚨🚨🚨 GRAVÍSSIMO - MÚLTIPLAS VIOLAÇÕES CRÍTICAS!'
            cor = '#8B0000'
            nivel_risco = 'RISCO CRÍTICO'
        elif criticos >= 1:
            status = '🚨 VIOLAÇÕES SÉRIAS - CONSULTE UM ADVOGADO!'
            cor = '#FF4500'
            nivel_risco = 'RISCO ELEVADO'
        elif altos >= 3:
            status = '⚠️ MÚLTIPLOS PROBLEMAS - REVISÃO URGENTE!'
            cor = '#FF8C00'
            nivel_risco = 'RISCO ALTO'
        elif total > 0:
            status = '⚠️ PROBLEMAS DETECTADOS - REVISE COM CUIDADO'
            cor = '#FFD700'
            nivel_risco = 'RISCO MODERADO'
        else:
            status = '✅ DOCUMENTO APARENTEMENTE REGULAR'
            cor = '#27AE60'
            nivel_risco = 'BAIXO RISCO'
        
        # Adicionar recomendações específicas
        recomendacoes = []
        
        if criticos > 0:
            recomendacoes.append('🚨 PROCURE UM ADVOGADO IMEDIATAMENTE!')
        
        if tipo_documento == 'CONTRATO_LOCACAO':
            if criticos > 0:
                recomendacoes.append('📋 Não assine o contrato sem revisão jurídica')
            if altos > 0:
                recomendacoes.append('🏠 Negocie as cláusulas problemáticas antes de assinar')
        
        elif tipo_documento == 'CONTRATO_TRABALHO':
            if criticos > 0:
                recomendacoes.append('👷 Não aceite o contrato nas condições atuais')
            if 'salário' in texto_limpo and criticos > 0:
                recomendacoes.append('💰 Salário abaixo do mínimo é crime - denuncie!')
        
        elif tipo_documento == 'NOTA_FISCAL':
            if criticos > 0:
                recomendacoes.append('🧾 Não utilize esta nota fiscal - pode ser fraude')
            if 'cancelada' in texto_limpo:
                recomendacoes.append('❌ Nota cancelada não tem validade fiscal')
        
        return {
            'total': total,
            'criticos': criticos,
            'altos': altos,
            'medios': medios,
            'info': info,
            'score': round(score, 1),
            'status': status,
            'cor': cor,
            'nivel_risco': nivel_risco,
            'tipo_documento': tipo_documento,
            'problemas': problemas,
            'recomendacoes': recomendacoes
        }
    
    def _resultado_vazio(self):
        """Retorna resultado vazio para análise sem texto"""
        return {
            'total': 0,
            'criticos': 0,
            'altos': 0,
            'medios': 0,
            'info': 0,
            'score': 100,
            'status': '❌ Nenhum texto fornecido para análise',
            'cor': '#95A5A6',
            'nivel_risco': 'SEM DADOS',
            'tipo_documento': 'DESCONHECIDO',
            'problemas': []
        }
