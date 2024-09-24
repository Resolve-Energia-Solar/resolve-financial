import PyPDF2
import re

def extract_data_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()

    data = {
        'name': extract_name(text),
        'account': account_number(text),
        'type': extract_type(text),
        'uc' : uc_number(text)
    }
    return data


def extract_type(text):
    match = re.search(r'Tipo de Fornecimento:\s*([^\n]+)', text, re.IGNORECASE)
    if match:
      return match.group(1)
    return "Tipo de Fornecimento não disponível"
  

def extract_name(text):
    name_match = re.search(r'(?<=\n)[A-Z\s]+(?=\nINSTALAÇÃO:)', text, re.IGNORECASE)
    if name_match:
        return name_match.group(0).strip()
    else:
        return 'Nome não disponível'


def account_number(text):
    match = re.search(r'Conta Contrato\s*([0-9]{6,10})', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return "Número da Conta Contrato não disponível"


def uc_number(text):
    match = re.search(r'([0-9]+)\s+Consumo', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return "Número não encontrado"