"""Transparent screening indicators, not validated error/ISO-compliance labels."""
import re

PREAMBLE = re.compile(r"\A\s*(?:[#*\s]*)(?:here(?:\s+is|\s+are|['’]s)\b|sure\s*[,!:]|(?:the\s+)?(?:simplified|rewritten|revised)\s+(?:text|version|passage)\s*:)", re.I)
ACRONYM = re.compile(r'\b[A-Z]{2,8}s?\b')
WORD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")
LIST_LINE = re.compile(r'(?m)^\s*(?:[-*•]|\d+[.)])\s+')


def initials_match(phrase, acronym):
    words = WORD.findall(phrase)
    target = acronym.lower()
    if len(words) < 2:
        return False
    variants = [words, [word for word in words if word.lower() not in {'and','of','the','for','in','to'}]]
    return any(''.join(w[0].lower() for w in variant) == target for variant in variants)


def has_parenthetical_expansion(text, token):
    # Prefer an exact uppercase token; matching is case sensitive by design.
    for match in re.finditer(r'\b'+re.escape(token)+r'\s*\(([^()\n]{3,160})\)', text):
        if initials_match(match.group(1), token.rstrip('s')):
            return True
    for match in re.finditer(r'\(\s*'+re.escape(token)+r'\s*\)', text):
        words = WORD.findall(text[max(0, match.start()-200):match.start()])
        if any(initials_match(' '.join(words[-n:]), token.rstrip('s')) for n in range(2, min(12,len(words))+1)):
            return True
    return False


def extra_flags(source, prediction, done_reason):
    text = prediction.strip()
    tokens = sorted(set(ACRONYM.findall(prediction)))
    unexpanded = [token for token in tokens if not has_parenthetical_expansion(prediction, token)]
    new_tokens = [token for token in unexpanded if re.search(r'\b'+re.escape(token)+r'\b', source) is None]
    lines = len(LIST_LINE.findall(prediction))
    no_terminal = bool(text) and done_reason == 'stop' and not text.rstrip('"”’\x27* ').endswith(('.', '!', '?'))
    return dict(preamble_candidate=bool(PREAMBLE.search(prediction)),
        stop_no_terminal_punctuation_candidate=no_terminal,
        acronym_without_detected_expansion_candidate=bool(unexpanded),
        new_acronym_without_detected_expansion_candidate=bool(new_tokens),
        unexpanded_acronyms=unexpanded, new_unexpanded_acronyms=new_tokens,
        list_marker_lines=lines, list_markers_present=lines > 0,
        two_or_more_list_markers=lines >= 2,
        source_copied_verbatim=bool(text) and prediction.split() == source.split())
