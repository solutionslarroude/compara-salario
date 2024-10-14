import streamlit as st
import pandas as pd
import pdfplumber

# Função para extrair nome, CPF e salário do PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        all_text = ""
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
    
    lines = all_text.split("\n")
    df = pd.DataFrame(lines, columns=['Texto'])
    
    # Filtrar as linhas que começam com número usando regex
    df_filtered = df[df['Texto'].str.match(r'^\d')].copy()  # Usar .copy() para evitar o warning
    
    # Separar as informações do texto para criar as colunas 'Código', 'Nome', 'CPF', e 'Salário'
    df_filtered.loc[:, 'Código'] = df_filtered['Texto'].str.extract(r'^(\d+)')  # Extrai o código (primeiros números)
    df_filtered.loc[:, 'CPF'] = df_filtered['Texto'].str.extract(r'(\d{3}\.\d{3}\.\d{3}-\d{2})')  # Extrai o CPF
    df_filtered.loc[:, 'Salário'] = df_filtered['Texto'].str.extract(r'(\d{1,3}(?:\.\d{3})*,\d{2})$')  # Extrai o salário (formato numérico com vírgula)
    df_filtered.loc[:, 'Nome'] = df_filtered['Texto'].str.extract(r'^\d+\s+(.*)\s+\d{3}\.\d{3}\.\d{3}-\d{2}')  # Extrai o nome entre o código e o CPF
    
    # Convertendo salário para o mesmo formato do TXT (float)
    df_filtered['Salário'] = df_filtered['Salário'].str.replace('.', '').str.replace(',', '.').astype(float)
    
    # Remover "." e "-" dos CPFs
    df_filtered['CPF'] = df_filtered['CPF'].str.replace('.', '').str.replace('-', '')
    
    # Remover a coluna original 'Texto' e qualquer linha onde algum campo esteja ausente
    df_final = df_filtered.drop(columns=['Texto']).dropna()
    
    return df_final

# Função para extrair nome, CPF e salário do TXT
def extract_name_cpf_salary_from_txt(txt_file_lines):
    data = []
    
    # Processar as linhas em pares (uma com nome e salário, outra com CPF)
    for i in range(0, len(txt_file_lines) - 1, 2):  # Itera de 2 em 2 linhas
        line_name_salary = txt_file_lines[i].decode('utf-8')  # Decodificar a linha de bytes para string
        line_cpf = txt_file_lines[i + 1].decode('utf-8')  # Decodificar a linha de bytes para string
        
        # Nome começa na posição 43 e vai até encontrar o primeiro '0'
        name = line_name_salary[43:].split('0', 1)[0].strip()  # Encontrar o primeiro '0' e extrair o nome
        
        # Salário está na posição 120 a 137 (extrair e converter para decimal)
        salary_str = line_name_salary[120:137].strip()
        try:
            salary = int(salary_str) / 100  # Convertendo de centavos para reais
        except ValueError:
            salary = None  # Se não for possível converter, atribuir None

        # CPF está na posição 21 da linha de baixo
        cpf = line_cpf[21:32].strip()  # Extrair o CPF
        
        # Remover "." e "-" do CPF
        cpf = cpf.replace('.', '').replace('-', '')

        # Adicionar os dados extraídos na lista
        if name:  # Somente adicionar se o nome não for vazio
            data.append([name, cpf, salary])
    
    # Criar um DataFrame com os dados extraídos
    df = pd.DataFrame(data, columns=['Nome', 'CPF', 'Salário'])
    
    # Remover linhas onde o nome está vazio
    df = df[df['Nome'] != '']
    
    return df

# Configuração do Streamlit
st.title("Validação de Salário entre TXT e PDF")

# Upload do arquivo PDF
uploaded_pdf = st.file_uploader("Escolha um arquivo PDF", type="pdf")

# Upload do arquivo TXT
uploaded_txt = st.file_uploader("Escolha um arquivo TXT", type="txt")

if uploaded_pdf and uploaded_txt:
    # Processar o PDF e o TXT
    df_pdf = extract_text_from_pdf(uploaded_pdf)
    txt_file_lines = uploaded_txt.readlines()
    df_txt = extract_name_cpf_salary_from_txt(txt_file_lines)
    
    # Exibir o DataFrame do PDF
    st.write("Dados extraídos do PDF:")
    st.dataframe(df_pdf)
    
    # Exibir o DataFrame do TXT
    st.write("Dados extraídos do TXT:")
    st.dataframe(df_txt)
    
    # Realizar o merge dos dois DataFrames com base no CPF (sem "." e "-")
    df_merged = pd.merge(df_txt, df_pdf[['CPF', 'Salário']], on='CPF', suffixes=('_TXT', '_PDF'))
    
    # Verificar se os salários são iguais nos dois arquivos
    df_merged['Salário_igual'] = df_merged['Salário_TXT'] == df_merged['Salário_PDF']
    
    # Exibir o DataFrame com a comparação
    st.write("Comparação de salários entre o TXT e o PDF:")
    st.dataframe(df_merged)

    # Exibir quais CPFs têm salários diferentes
    diferentes = df_merged[df_merged['Salário_igual'] == False]
    if not diferentes.empty:
        st.warning("Salários diferentes encontrados nos seguintes CPFs:")
        st.dataframe(diferentes[['CPF', 'Salário_TXT', 'Salário_PDF']])
    else:
        st.success("Todos os CPFs têm salários iguais no TXT e no PDF.")
