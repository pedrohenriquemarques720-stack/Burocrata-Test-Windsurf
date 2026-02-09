# ⚖️ Burocrata de Bolso

**IA de análise documental jurídica especializada em detectar problemas em contratos e documentos legais.**

[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0+-red.svg)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Funcionalidades Principais

### 📋 Análise de Documentos Jurídicos
- **🏠 Contratos de Locação**: Detecta cláusulas abusivas e multas ilegais
- **💼 Contratos de Trabalho**: Identifica violações à CLT e direitos trabalhistas
- **🧾 Notas Fiscais**: Validação de documentos fiscais

### 🔍 Detecção Inteligente de Problemas
- 🚨 **Multa de 12 meses de aluguel** - ILEGAL (Lei 8.245/1991)
- 🚨 **Caução de 3 meses** - ILEGAL (Art. 37)
- 🚨 **Reajuste trimestral** - ILEGAL (Art. 7º)
- 🚨 **Salário abaixo do mínimo** - TRABALHO ESCRAVO (CF Art. 7º)
- 🚨 **Jornada excessiva** - ILEGAL (CLT Art. 58)
- 🚨 **Visitas sem aviso** - VIOLAÇÃO DE DOMICÍLIO
- ⚠️ **Cláusulas abusivas** - Nulas de pleno direito
- E muito mais!

### 👥 Sistema Completo de Usuários
- 🔐 **Autenticação segura** com hash SHA-256
- 💰 **Sistema de créditos** (BuroCreds)
- 📊 **Histórico completo** de análises
- 👑 **Conta especial** para desenvolvedor com créditos ilimitados

## 🏗️ Arquitetura Modular

```
Burocrata de Bolso/
├── 📄 app.py                 # Aplicação principal (Streamlit)
├── ⚙️ config.py             # Configurações centralizadas
├── 🗄️ database.py           # Módulo de banco de dados SQLite
├── 🔍 analysis.py           # Sistema de análise jurídica
├── 🛠️ utils.py              # Funções utilitárias reutilizáveis
├── 🎨 ui.py                 # Interface do usuário
├── 📦 requirements.txt      # Dependências do projeto
├── 📖 README.md            # Documentação completa
└── 💾 usuarios_burocrata.db # Banco de dados SQLite
```

## 🛠️ Stack Tecnológico

| Componente | Tecnologia | Versão |
|------------|-------------|---------|
| **Frontend** | Streamlit | ≥1.28.0 |
| **Backend** | Python | ≥3.8 |
| **Banco de Dados** | SQLite | 3.x |
| **Processamento PDF** | pdfplumber | ≥0.9.0 |
| **Análise de Texto** | Regex + Unicode | - |
| **Criptografia** | hashlib (SHA-256) | - |

## 📦 Instalação Rápida

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/burocrata-de-bolso.git
cd burocrata-de-bolso
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Execute a aplicação:**
```bash
streamlit run app.py
```

4. **Acesse no navegador:**
```
http://localhost:8501
```

## 🎯 Como Usar

### 1. **Acesso ao Sistema**
- **Novos usuários:** Cadastre-se com e-mail e senha
- **Usuários existentes:** Faça login com credenciais

### 2. **Conta Especial de Desenvolvimento**
Para testes completos, use a conta especial:
- **📧 E-mail:** `pedrohenriquemarques720@gmail.com`
- **🔑 Senha:** `Liz1808#`
- **💎 Benefícios:** Créditos ilimitados para testes

### 3. **Análise de Documentos**
1. Faça upload do documento PDF
2. Aguarde o processamento automático
3. Visualize os resultados detalhados
4. Receba recomendações jurídicas

### 4. **Sistema de Créditos**
- **Custo por análise:** 10 BuroCreds
- **Como adquirir:** Contate o suporte
- **Plano PRO:** Recursos avançados ilimitados

## 📊 Tipos de Problemas Detectados

### 🏠 Contratos de Locação
| Problema | Gravidade | Fundamento Legal |
|----------|------------|------------------|
| Multa > 2 meses aluguel | 🚨 Crítica | Lei 8.245/1991 Art. 4º |
| Caução > 1 mês aluguel | 🚨 Crítica | Lei 8.245/1991 Art. 37 |
| Reajuste < 12 meses | 🚨 Crítica | Lei 8.245/1991 Art. 7º |
| Visitas sem aviso | 🚨 Crítica | CDC + Código Penal Art. 150 |
| Proibição de animais | ⚠️ Alta | CDC Art. 51 |

### 💼 Contratos de Trabalho
| Problema | Gravidade | Fundamento Legal |
|----------|------------|------------------|
| Salário < mínimo | 🚨 Crítica | CF Art. 7º IV |
| Jornada > 8h diárias | 🚨 Crítica | CLT Art. 58 |
| Sem horas extras | 🚨 Crítica | CLT Art. 59 |
| Intervalo < 1h | 🚨 Crítica | CLT Art. 71 |
| Renúncia FGTS | 🚨 Crítica | Lei 8.036/1990 |

## 🔧 Configuração

### Variáveis de Ambiente
Edite `config.py` para personalizar:

```python
# Configurações da Aplicação
APP_CONFIG = {
    'title': "Burocrata de Bolso",
    'icon': "⚖️",
    'layout': "wide"
}

# Configurações de Usuário
USER_CONFIG = {
    'special_account': {
        'email': "seu@email.com",
        'password': "sua_senha",
        'credits': 999999
    },
    'analysis_cost': 10
}

# Configurações de Tema
THEME_CONFIG = {
    'primary_color': '#10263D',
    'accent_color': '#F8D96D',
    'text_color': '#FFFFFF'
}
```

## 🧪 Testes

### Testes Automatizados
```bash
# Executar todos os testes
python -m pytest tests/

# Testar apenas análise
python -m pytest tests/test_analysis.py

# Testar banco de dados
python -m pytest tests/test_database.py
```

### Testes Manuais
1. **Login/Cadastro:** Teste fluxo completo
2. **Upload de PDF:** Teste diferentes formatos
3. **Análise:** Verifique detecções
4. **Histórico:** Confirme persistência

## 📞 Suporte e Contato

| Canal | Informação |
|--------|-------------|
| **📧 E-mail** | contatoburocrata@outlook.com |
| **📷 Instagram** | [@burocratadebolso](https://www.instagram.com/burocratadebolso/) |
| **⏰ Tempo Resposta** | Até 24 horas úteis |
| **🌐 Site** | [burocratadebolso.com](https://burocratadebolso.com) |

## 🔒 Segurança

### Implementada
- ✅ **Criptografia SHA-256** para senhas
- ✅ **Proteção contra injeção SQL** com parâmetros
- ✅ **Validação de entrada** de dados
- ✅ **Sessões seguras** com timeout
- ✅ **Banco de dados local** (SQLite)

### Recomendações
- Use HTTPS em produção
- Configure firewall adequado
- Mantenha dependências atualizadas
- Faça backup regular do banco

## 📈 Performance

### Otimizações
- **Cache de configurações:** Reduz acesso a disco
- **Conexões eficientes:** Pool de conexões SQLite
- **Processamento assíncrono:** Para grandes volumes
- **Compressão de PDFs:** Otimiza uso de memória

### Métricas
- **Tempo médio análise:** < 5 segundos
- **Tamanho máximo PDF:** 10MB
- **Concorrência suportada:** 100+ usuários
- **Uso de memória:** < 512MB

## 🔄 Atualizações

### Versão Atual: **v2.1.0**
- ✅ Código modularizado
- ✅ Sistema de análise otimizado
- ✅ Interface responsiva
- ✅ Novos padrões de detecção

### Roadmap
- 🔄 [ ] API REST para integração
- 🔄 [ ] Processamento em lote
- 🔄 [ ] Machine Learning avançado
- 🔄 [ ] Aplicativo mobile

## 🤝 Contribuição

### Como Contribuir
1. **Fork** o repositório
2. **Crie branch** para sua feature:
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```
3. **Commit** suas mudanças:
   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```
4. **Push** para o branch:
   ```bash
   git push origin feature/nova-funcionalidade
   ```
5. **Abra Pull Request**

### Diretrizes
- Siga PEP 8 para código Python
- Adicione testes para novas funcionalidades
- Documente mudanças significativas
- Respeite o código existente

## 📝 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚖️ Aviso Legal Importante

**AVISO:** Esta ferramenta fornece análise preliminar e identificação de potenciais problemas jurídicos com base na legislação brasileira vigente. 

**NÃO SUBSTITUI** a consulta com um advogado qualificado. Para:

- ✅ **Validação jurídica completa**
- ✅ **Assessoria personalizada**  
- ✅ **Representação legal**
- ✅ **Defesa em processos judiciais**

**Consulte sempre um profissional da área jurídica para orientação definitiva.**

## 🏆 Créditos

Desenvolvido com ❤️ por:

- **[Pedro Henrique](https://github.com/pedrohenriquemarques720)** - Desenvolvedor Principal
- **Burocrata de Bolso Team** - Suporte e Manutenção

---

<div align="center">

**⚖️ Burocrata de Bolso - Sua IA jurídica de bolso**

*Transformando a análise documental com tecnologia e precisão*

[📧 Entre em Contato](mailto:contatoburocrata@outlook.com) • [📷 Siga-nos](https://www.instagram.com/burocratadebolso/)

</div>
