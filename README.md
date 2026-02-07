# ⚖️ Burocrata de Bolso

IA de Análise Documental Jurídica

## 🚀 Sobre o Projeto

O **Burocrata de Bolso** é uma aplicação web desenvolvida com Streamlit que utiliza inteligência artificial para analisar documentos jurídicos e identificar potenciais problemas legais em contratos de locação, contratos de trabalho e outros documentos importantes.

## 📋 Funcionalidades

### 🔍 Análise Documental
- **Contratos de Locação**: Identifica cláusulas abusivas, multas ilegais, problemas com caução e reajustes
- **Contratos de Trabalho**: Detecta violações à CLT, salários abaixo do mínimo, jornadas excessivas
- **Notas Fiscais**: Validação de documentos fiscais

### 👤 Sistema de Usuários
- Autenticação segura com hash SHA-256
- Sistema de créditos (BuroCreds)
- Histórico de análises
- Conta especial com créditos ilimitados para desenvolvimento

### 🎨 Interface Profissional
- Design moderno com tema azul escuro e dourado
- Interface responsiva e intuitiva
- Resultados detalhados com base legal

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit
- **Backend**: Python
- **Banco de Dados**: SQLite
- **Processamento de PDF**: pdfplumber
- **Processamento de Texto**: regex, unicodedata

## 📦 Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd burocrata-de-bolso
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run app.py
```

## 🔧 Estrutura do Projeto

```
burocrata-de-bolso/
├── app.py              # Aplicação principal
├── database.py         # Funções do banco de dados
├── detection.py        # Sistema de detecção de problemas
├── utils.py            # Funções utilitárias
├── ui.py               # Interface do usuário
├── requirements.txt    # Dependências do projeto
└── README.md          # Documentação
```

## 🎯 Como Usar

1. **Acesse a aplicação**: Abra o navegador no endereço fornecido pelo Streamlit
2. **Crie uma conta** ou faça login com credenciais existentes
3. **Adquira BuroCreds** para realizar análises (contato: contatoburocrata@outlook.com)
4. **Envie seu documento** em formato PDF
5. **Receba a análise** detalhada com problemas identificados e recomendações

## 👤 Conta Especial de Desenvolvimento

Para testes, use a conta especial:
- **Email**: pedrohenriquemarques720@gmail.com
- **Senha**: Liz1808#
- **Benefícios**: Créditos ilimitados para testes

## ⚖️ Tipos de Análise

### Contratos de Locação
- ✅ Multas rescisórias acima de 2 meses
- ✅ Caução superior a 1 mês de aluguel
- ✅ Reajustes com período inferior a 12 meses
- ✅ Visitas sem aviso prévio
- ✅ Cláusulas de renúncia a direitos

### Contratos de Trabalho
- ✅ Salários abaixo do mínimo legal
- ✅ Jornadas excessivas (>8h diárias, >44h semanais)
- ✅ Ausência de pagamento de horas extras
- ✅ Intervalos insuficientes
- ✅ Renúncia a direitos trabalhistas

## 🔒 Segurança

- Senhas criptografadas com SHA-256
- Banco de dados SQLite seguro
- Validação de entrada de dados
- Proteção contra injeção SQL

## 📞 Suporte

- **Email**: contatoburocrata@outlook.com
- **Instagram**: @burocratadebolso
- Resposta em até 24 horas

## 📝 Licença

© 2026 Burocrata de Bolso. Todos os direitos reservados.

---

**Aviso Legal**: Esta aplicação fornece análise preliminar e não substitui a consulta com um advogado qualificado. Para orientação jurídica completa, consulte um profissional da área.
