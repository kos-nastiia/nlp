import re

class TextPreprocess:
    def __init__(self):
        self.url_pattern = r'https?://\S+|www\.\S+'
        self.email_pattern = r'\S+@\S+'
        self.phone_pattern = r'\+?\d{10,12}'

    def clean_text(self, text: str) -> str:
        """Базова технічна чистка: пробіли, лапки, юнікод."""
        if not isinstance(text, str): return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r"['’‘`]", "'", text)
        return text

    def mask_pii(self, text: str) -> str:
        """Заміна персональних даних на токени-заглушки."""
        if not isinstance(text, str): return ""
        text = re.sub(self.url_pattern, '<URL>', text)
        text = re.sub(self.email_pattern, '<EMAIL>', text)
        text = re.sub(self.phone_pattern, '<PHONE>', text)
        return text

    def normalize_text(self, text: str) -> str:
        """Нормалізація: нижній регістр та видалення пунктуації."""
        if not isinstance(text, str): return ""
        text = text.lower()
        text = re.sub(r'(?<!<)[^\w\s<>](?!>)', '', text)
        return " ".join(text.split())

    def sentence_split(self, text: str) -> list:
        """Розбиття тексту на речення за крапкою, окликом або питанням."""
        if not isinstance(text, str): return []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def preprocess(self, text: str) -> dict:
        """Повний пайплайн обробки."""
        cleaned = self.clean_text(text)
        masked = self.mask_pii(cleaned)
        sentences = self.sentence_split(masked)
        normalized_sentences = [self.normalize_text(s) for s in sentences]
        
        return {
            "original": text,
            "clean": masked,
            "sentences": normalized_sentences,
            "final": " | ".join(normalized_sentences) 
        }