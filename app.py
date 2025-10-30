from flask import Flask, request, send_file, render_template_string
import pandas as pd
import traceback
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Gerar Inserts PRECO_AMB</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container py-5">
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <h2 class="card-title text-center mb-3">Gerar Inserts PRECO_AMB</h2>
                <p class="text-center text-muted">Faça o upload da planilha Rol de Procedimentos Médicos (.xlsx). <br>
                Recomenda-se remover outras planilhas do arquivo para deixar o processo mais leve.</p>
                <form action="/" method="post" enctype="multipart/form-data" class="d-flex justify-content-center mb-3">
                    <input type="file" name="file" accept=".xlsx" class="form-control w-50 me-2" required>
                    <button type="submit" class="btn btn-primary">Processar</button>
                </form>
                {% if error %}
                    <div class="alert alert-danger mt-3" role="alert">
                        <strong>Erro:</strong>
                        <pre>{{ error }}</pre>
                    </div>
                {% endif %}
                {% if link %}
                    <div class="alert alert-success mt-3 text-center" role="alert">
                        <h5>Download pronto!</h5>
                        <a href="{{ link }}" class="btn btn-success">Baixar arquivo SQL</a>
                    </div>
                {% endif %}
            </div>
        </div>

        <div class="card shadow-sm">
            <div class="card-body">
                <h4 class="card-title">Instruções para ajustar a sequência PRECO_AMB_seq no Oracle caso necessário:</h4>
                <ul>
                    <li>Comando para saber a sequência atual: <code>SELECT PRECO_AMB_seq.CURRVAL FROM dual;</code></li>
                    <li>Comando para saber a próxima sequência: <code>SELECT PRECO_AMB_seq.NEXTVAL FROM dual;</code></li>
                    <li>Comando para saber a última sequência: <code>SELECT MAX(nr_sequencia) FROM PRECO_AMB;</code></li>
                </ul>
                <p>Para ajustar a sequência corretamente, execute o comando e ajuste o incremento com a diferença existente entre a sequência máxima e a sequência atual armazenada no banco:</p>
                <pre>
ALTER SEQUENCE PRECO_AMB_seq INCREMENT BY 63;
SELECT PRECO_AMB_seq.NEXTVAL FROM dual;

ALTER SEQUENCE PRECO_AMB_seq INCREMENT BY 1;
SELECT PRECO_AMB_seq.CURRVAL FROM dual - SELECT MAX(nr_sequencia) FROM PRECO_AMB;
                </pre>
            </div>
        </div>
    </div>
    <!-- Bootstrap JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        try:
            file = request.files["file"]
            file_path = os.path.join("/tmp", file.filename)
            file.save(file_path)
            print(f"[INFO] Arquivo recebido: {file_path}")

            # Lê o Excel completo sem cabeçalho fixo
            df_raw = pd.read_excel(file_path, header=None)
            print(f"[INFO] Linhas totais: {len(df_raw)}")

            # Localiza linhas com cabeçalho “Codigo”
            header_indices = df_raw.index[df_raw.iloc[:, 0] == "Codigo"].tolist()
            print(f"[INFO] Cabeçalhos encontrados: {header_indices}")

            dataframes = []
            for i, start in enumerate(header_indices):
                end = header_indices[i + 1] if i + 1 < len(header_indices) else len(df_raw)
                temp_df = df_raw.iloc[start + 1:end].copy()
                temp_df.columns = df_raw.iloc[start]
                if "Codigo" in temp_df.columns:
                    temp_df = temp_df.dropna(subset=["Codigo"])
                    dataframes.append(temp_df)

            if not dataframes:
                raise ValueError("Nenhum bloco de dados encontrado com o cabeçalho 'Codigo'.")

            df = pd.concat(dataframes, ignore_index=True)
            print(f"[INFO] Linhas consolidadas: {len(df)}")

            # Seleciona e limpa as colunas necessárias
            colunas_necessarias = [
                "Codigo",
                "Valor Total (HM + CO)",
                "Valor HM",
                "Nº Auxiliares",
                "Porte Anestesico",
                "Valor Porte Anestesico",
                "Valor CO",
                "Valor Filme"
            ]
            df = df[colunas_necessarias]
            df = df.dropna(subset=["Codigo"])

            # Função segura para converter valores numéricos
            def parse_num(val):
                if pd.isna(val):
                    return 0.0
                val = str(val).strip().replace(",", ".")
                try:
                    return float(val)
                except ValueError:
                    return 0.0

            # Função para validar código (apenas números)
            def is_valid_codigo(codigo):
                return str(codigo).replace(".", "").isdigit()

            inserts = []
            for _, row in df.iterrows():
                codigo = str(row["Codigo"]).strip()
                
                # Ignora títulos e capítulos
                if not is_valid_codigo(codigo):
                    continue

                # Converte e limita para 4 casas decimais
                valor_total = round(parse_num(row["Valor Total (HM + CO)"]), 4)
                valor_hm = round(parse_num(row["Valor HM"]), 4)
                nr_aux = int(parse_num(row["Nº Auxiliares"]))
                porte_an = int(parse_num(row["Porte Anestesico"]))
                valor_porte = round(parse_num(row["Valor Porte Anestesico"]), 4)
                vl_custo_operacional = round(parse_num(row.get("Valor CO", 0.0)), 4)
                
                vl_filme = round(parse_num(row.get("Valor Filme", 0.0)), 4)

                # Formata com 4 casas decimais fixas e ponto decimal (compatível com Oracle)
                sql = (
                    "INSERT INTO PRECO_AMB (cd_edicao_amb,ie_origem_proced,nr_sequencia,cd_moeda,"
                    "nm_usuario,DT_INICIO_VIGENCIA,dt_atualizacao,CD_PROCEDIMENTO,vl_procedimento,"
                    "vl_medico,nr_auxiliares,qt_porte_anestesico,vl_anestesista,vl_custo_operacional,"
                    "vl_filme) "
                    f"VALUES (4,5,PRECO_AMB_seq.nextval,1,'lester',SYSDATE,SYSDATE,'{codigo}',"
                    f"{valor_total:.4f},{valor_hm:.4f},{nr_aux},{porte_an},{valor_porte:.4f},"
                    f"{vl_custo_operacional:.4f},{vl_filme:.4f}); COMMIT;"
                )
                inserts.append(sql)

            output_path = "/tmp/inserts_preco_amb.sql"
            with open(output_path, "w") as f:
                f.write("\n".join(inserts))

            print(f"[INFO] Arquivo gerado: {output_path}")
            return render_template_string(HTML, link="/download")

        except Exception as e:
            tb = traceback.format_exc()
            print(f"[ERRO] {tb}")
            return render_template_string(HTML, error=tb)

    return render_template_string(HTML)

@app.route("/download")
def download_file():
    return send_file("/tmp/inserts_preco_amb.sql", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
