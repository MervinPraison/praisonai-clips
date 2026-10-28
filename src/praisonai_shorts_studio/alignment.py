"""Restore transcript punctuation without changing any provider word timestamps."""
import difflib
import re
import unicodedata


def normalized(token):
    return ''.join(c for c in unicodedata.normalize('NFKC', token).casefold() if c.isalnum())


def punctuate(words, text):
    tokens = text.split()
    result = [dict(w) for w in words]
    matcher = difflib.SequenceMatcher(a=[normalized(w['word']) for w in words],
                                      b=[normalized(t) for t in tokens], autojunk=False)
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            index = block.a + offset
            token = tokens[block.b + offset]
            suffix = re.search(r'''[.!?,;:]+["'”’\)\]]*$''', token)
            if suffix:
                # Keep the measured lexical token; append only punctuation from the API text.
                result[index]['word'] = result[index]['word'].rstrip('.,!?;:') + suffix.group()
    return result
