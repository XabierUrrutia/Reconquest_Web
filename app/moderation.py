import re
import unicodedata


PROFANITY_WORDS = {
    "puta", "putas", "puto", "putos",
    "mierda", "mierdas",
    "cabron", "cabrones", "cabrona", "cabronas",
    "gilipollas", "gilipolla",
    "coño", "cono", "coñazo", "conazo",
    "joder", "jodete", "jodanse",
    "hostia", "hostias",
    "maricon", "maricones", "mariconazo",
    "zorra", "zorras", "zorron",
    "hijoputa", "hijoputas", "hijueputa", "hijueputas", "hijoeputa",
    "polla", "pollas",
    "verga", "vergas",
    "pendejo", "pendeja", "pendejos", "pendejas",
    "chingar", "chinga", "chingado", "chingada",
    "pinche", "pinches",
    "mamon", "mamones", "mamonazo",
    "follar", "follate", "follame",
    "cojones", "cojonudo",
    "cagar", "cagon", "cagona",
    "subnormal", "subnormales",
    "retrasado", "retrasada", "retrasados",
    "nazi", "nazis",
    "perra", "perras",
}

PROFANITY_PHRASES = [
    "hijo de puta", "hijos de puta", "hija de puta", "hijas de puta",
    "me cago en", "vete a la mierda", "vete a tomar por culo",
    "que te follen", "que te jodan",
    "tu puta madre", "tu madre",
]


def _normalize(text):
    """Pasa a minúsculas y elimina acentos para comparar."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


_WORD_RE = re.compile(r"\b(" + "|".join(re.escape(_normalize(w)) for w in PROFANITY_WORDS) + r")\b")


def contains_profanity(text):
    """Devuelve (True, palabra_detectada) si el texto contiene palabrotas obvias, o (False, None)."""
    if not text:
        return False, None
    norm = _normalize(text)

    for phrase in PROFANITY_PHRASES:
        if _normalize(phrase) in norm:
            return True, phrase

    m = _WORD_RE.search(norm)
    if m:
        return True, m.group(1)

    return False, None
