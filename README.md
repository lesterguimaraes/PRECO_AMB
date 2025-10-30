# Gerador de Inserts PRECO_AMB

Este projeto fornece uma interface web simples para gerar scripts SQL de inserção (`INSERT`) na tabela `PRECO_AMB` a partir de uma planilha Excel (`.xlsx`). Ele trata valores numéricos, formata campos com 4 casas decimais e gera cada insert com `COMMIT;` ao final.

---

## Tecnologias

- **Python 3.11+**
- **Flask** – framework web
- **Pandas** – manipulação de planilhas Excel
- **Bootstrap 5** – interface visual agradável
- **Oracle** – banco de dados de destino

---

## Funcionalidades

1. Upload de planilha Excel contendo os dados de procedimentos médicos.
2. Validação e filtragem de códigos válidos.
3. Conversão de valores numéricos, incluindo casas decimais e substituição de valores ausentes por `0.0000`.
4. Geração automática do script SQL com:
   - `VL_PROCEDIMENTO`, `VL_MEDICO`, `NR_AUXILIARES`, `QT_PORTE_ANESTESICO`, `VL_ANESTESISTA`
   - Novas colunas: `VL_CUSTO_OPERACIONAL`, `VL_FILME`
5. Cada linha de insert finaliza com `COMMIT;`.
6. Layout responsivo e amigável usando Bootstrap.

---

## Estrutura do Projeto

/project
│
├─ app.py # Aplicação Flask principal
├─ requirements.txt # Dependências Python
└─ README.md # Documentação


---

## Instalação

1. Clone o repositório:

```bash
git clone <url_do_repositorio>
cd <pasta_do_projeto>


Estrutura esperada da planilha Excel

A planilha deve conter, no mínimo, as seguintes colunas:

Codigo

Valor Total (HM + CO)

Valor HM

Nº Auxiliares

Porte Anestesico

Valor Porte Anestesico

Valor CO

Valor Filme

Colunas adicionais ausentes serão criadas automaticamente com valor 0.0000.

Observações

Apenas códigos numéricos são processados. Títulos, capítulos ou células de cabeçalho são ignorados.

Cada linha gerada contém o COMMIT; ao final, garantindo que cada insert seja persistido.

Certifique-se de remover planilhas desnecessárias para agilizar o processamento.

