import pandas as pd
import stanza
import os
from tqdm import tqdm

def initialize_stanza():
    """Ініціалізація Stanza."""
    stanza.download('uk')
    return stanza.Pipeline(
        lang='uk', 
        processors='tokenize,pos,lemma', 
        use_gpu=False, 
        download_method='reuse_resources'
    )

def get_ling_data(text, nlp):
    """Отримує леми та POS-теги для тексту."""
    if not isinstance(text, str) or text.strip() == "":
        return "", ""
    
    doc = nlp(text)
    lemmas = []
    pos_tags = []
    
    for sent in doc.sentences:
        for word in sent.words:
            if word.text.startswith('<') and word.text.endswith('>'):
                lemmas.append(word.text)
                pos_tags.append('SYM')
            else:
                l = word.lemma.lower() if word.lemma else word.text.lower()
                lemmas.append(l)
                pos_tags.append(word.upos)
            
    return " ".join(lemmas), " ".join(pos_tags)

def process_dataset():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'data', 'processed_v2.csv') 
    output_file = os.path.join(base_dir, 'data', 'processed_v3.csv')

    if not os.path.exists(input_file):
        print(f"Помилка: Файл {input_file} не знайдено!")
        return

    print("--- Завантаження processed_v2.csv ---")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    text_col = 'text_v2' 
    if text_col not in df.columns:
        print(f"Колонка {text_col} не знайдена. Доступні: {df.columns.tolist()}")
        return

    nlp = initialize_stanza()
    
    print(f"Початок обробки {len(df)} рядків...")
    lemmas_list = []
    pos_list = []
    
    for text in tqdm(df[text_col]):
        l, p = get_ling_data(text, nlp)
        lemmas_list.append(l)
        pos_list.append(p)
    
    df['lemma_text'] = lemmas_list
    df['pos_seq'] = pos_list

    df.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')
    print(f"Успіх! Файл збережено: {output_file}")

if __name__ == "__main__":
    process_dataset()
    