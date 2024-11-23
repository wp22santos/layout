# Banco de Horas v1.0

Sistema de gerenciamento de banco de horas desenvolvido com Flask e Tailwind CSS.

## Funcionalidades

- Visualização por trimestres
- Gestão de turnos de trabalho
- Registro de dias não contábeis
- Interface responsiva e moderna
- Visualização de saldo de horas por mês e trimestre

## Requisitos

- Python 3.8+
- Flask 3.0.0
- Demais dependências listadas em requirements.txt

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd banco-de-horas
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

## Estrutura do Projeto

```
banco-de-horas/
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências do projeto
└── templates/         # Templates HTML
    ├── index.html     # Página inicial
    └── mes.html       # Detalhes do mês
```

## Versão 1.0

- Interface inicial completa
- Gestão de turnos e dias não contábeis
- Visualização por trimestres
- Cálculo de saldos

## Próximas Atualizações Planejadas

- Sistema de autenticação
- Persistência de dados em banco de dados
- Exportação de relatórios
- Configurações personalizadas por usuário
