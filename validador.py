import streamlit as st
import pdfplumber
import pandas as pd
import re

# Função para identificar e extrair dados do PDF
def identify_and_extract_data_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        all_text = ""
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"

        # Verificar se é o PDF correto
        if "LARROUDE COMERCIO E EXPORTACAO DE CALCAD" in all_text and "Adiantamento" in all_text:
            st.write("PDF identificado como arquivo da empresa LARROUDE.")
            return process_text_to_dataframe(all_text)
        else:
            st.write("Este não parece ser o PDF correto.")
            return None

# Função para processar o texto extraído do PDF e criar um DataFrame
def process_text_to_dataframe(text):
    lines = text.split('\n')
    data = []
    pattern = re.compile(r"(\d+)\s+([\w\s]+)\s+([\d,.]+)")

    for line in lines:
        match = pattern.match(line)
        if match:
            id_, name, value = match.groups()
            value = value.replace('.', '').replace(',', '.')  # Converte valor para float
            data.append([id_, name.strip(), float(value)])

    # Criar DataFrame com as colunas filtradas (ID, Name e Value)
    df = pd.DataFrame(data, columns=['ID', 'Name', 'Value'])
    return df

# Função para extrair nome e salário do TXT
def extract_name_and_salary_from_txt(txt_file):
    data = []
    
    # Ler o arquivo linha por linha
    for line in txt_file:
        line = line.decode('utf-8')  # Decodificar a linha de bytes para string
        # Nome começa na posição 43 e vai até encontrar o primeiro '0'
        name = line[43:].split('0', 1)[0].strip()
        
        # Salário está na posição 120 a 137 (extrair e converter para decimal)
        salary_str = line[120:137].strip()
        if salary_str.isdigit():
            salary = int(salary_str) / 100  # Convertendo de centavos para reais
            data.append([name, salary])
    
    # Criar um DataFrame com os dados
    df = pd.DataFrame(data, columns=['Name', 'Salary'])
    return df

# Função para verificar se os nomes e salários do PDF correspondem aos do TXT
def compare_pdf_and_txt(pdf_df, txt_df):
    # Mesclar os DataFrames com base no nome
    merged_df = pd.merge(pdf_df, txt_df, on='Name', how='inner', suffixes=('_pdf', '_txt'))
    
    # Adicionar uma coluna que verifica se os salários são iguais
    merged_df['Salary Match'] = merged_df.apply(lambda row: 'Yes' if row['Value'] == row['Salary'] else 'No', axis=1)
    
    return merged_df

# Configuração do Streamlit
st.title("Comparação de PDF e TXT de Salários")

# Upload dos arquivos
uploaded_pdf = st.file_uploader("Faça upload do arquivo PDF", type=["pdf"])
uploaded_txt = st.file_uploader("Faça upload do arquivo TXT", type=["txt"])

# Se ambos os arquivos forem enviados, iniciar o processamento
if uploaded_pdf and uploaded_txt:
    # Processar o PDF
    df_pdf = identify_and_extract_data_from_pdf(uploaded_pdf)
    
    # Processar o TXT
    txt_file_lines = uploaded_txt.readlines()  # Lê as linhas do arquivo TXT
    df_txt = extract_name_and_salary_from_txt(txt_file_lines)
    
    # Comparar os dados entre PDF e TXT
    if df_pdf is not None and not df_txt.empty:
        df_comparison = compare_pdf_and_txt(df_pdf, df_txt)
        st.write("Comparação entre PDF e TXT:")
        st.dataframe(df_comparison)
    else:
        st.write("Erro na extração de dados do PDF ou TXT.")
