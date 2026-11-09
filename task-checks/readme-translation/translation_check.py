"""Offline checks for the pinned README translation tasks (stdlib only)."""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent


def load_task(name):
    tasks = json.loads((HERE / 'tasks.json').read_text(encoding='utf-8'))
    assert name in tasks, f'Unknown BOUNTY_TASK: {name}; choose {", ".join(tasks)}'
    config = tasks[name]
    baseline = (HERE / config['baseline']).read_bytes()
    assert hashlib.sha256(baseline).hexdigest() == config['sha256'], 'Pinned baseline hash mismatch'
    return config, baseline


def parse(text):
    """Parse the block forms used by these baselines, preserving raw fence bytes.

    Prose blocks retain section order, table rows, list items and blockquotes so
    a translated heading cannot conceal a missing caveat paragraph. Preserve
    those boundaries; line wrapping inside a paragraph can change freely.
    """
    blocks, fences, headings = [], [], []
    paragraph = []
    fence = None
    raw = []

    def flush():
        if paragraph:
            blocks.append(('paragraph', '\n'.join(paragraph)))
            paragraph.clear()

    for line in text.splitlines(keepends=True):
        if fence:
            raw.append(line)
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + r'{' + str(fence[1]) + r',}[ \t]*\r?\n?', line):
                fences.append(''.join(raw))
                fence, raw = None, []
            continue
        match = re.match(r' {0,3}(`{3,}|~{3,})([^\r\n]*)', line)
        if match:
            flush()
            fence = (match[1][0], len(match[1]))
            raw = [line]
            blocks.append(('fence', ''))
            continue
        # Hidden HTML/comment text cannot supply the measured language content.
        assert not re.search(r'<!--|<!\[CDATA\[|</?[A-Za-z][\w-]*(?:\s|/?>)', re.sub(r'(`+).*?\1', '', line)), 'Raw HTML is outside these translation tasks'
        assert not re.search(r'(?:^|[ \t>])\[[^\]]+\]:', re.sub(r'(`+).*?\1', '', line)), 'Reference definitions can hide prose; use inline links as in the pinned baselines'
        if not line.strip():
            flush()
            continue
        heading = re.match(r' {0,3}(#{1,6})[ \t]+(.+?)\s*#*\s*$', line)
        if heading:
            flush()
            headings.append(len(heading[1]))
            blocks.append(('heading', heading[2]))
        elif line.lstrip().startswith('|'):
            flush()
            if not re.fullmatch(r'[\s|:-]+', line):
                blocks.append(('table', line.strip()))
        elif re.match(r'\s*(?:[-+*]|\d+[.)])\s+', line):
            flush()
            blocks.append(('list', re.sub(r'^\s*(?:[-+*]|\d+[.)])\s+', '', line).strip()))
        elif line.lstrip().startswith('>'):
            flush()
            blocks.append(('quote', line.lstrip()[1:].strip()))
        elif not paragraph and blocks and blocks[-1][0] in ('list', 'quote') and line.startswith('  '):
            kind, value = blocks[-1]
            blocks[-1] = (kind, value + ' ' + line.strip())
        else:
            paragraph.append(line.strip())
    flush()
    assert fence is None, 'Unclosed fenced code block'
    return headings, fences, blocks


def link_targets(text):
    # Mask inline destinations before finding bare URLs: punctuation that is
    # part of an explicit destination must never be trimmed as sentence prose.
    matches = list(re.finditer(r'\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\s*\)', text))
    targets = {match[1].strip('<>') for match in matches}
    visible = list(text)
    for match in matches:
        visible[match.start():match.end()] = ' ' * (match.end() - match.start())
    bare = re.findall(r'https?://[^\s<>`"\[\]{}\u3000-\u303f\uff00-\uffef]+', ''.join(visible))
    targets.update(target.rstrip('.,;:)') for target in bare)
    return targets


def technical_terms(source):
    return {word for word in re.findall(r'[A-Za-z][A-Za-z0-9_.-]*', source)
            if any(char.isupper() for char in word) or '.' in word}


def prose(text, source=None):
    known_code = set(re.findall(r'(`+)(.*?)\1', source or ''))
    technical = technical_terms(source or '')

    def inline(match):
        if source is None or (match[1], match[2]) in known_code:
            return ''
        words = re.findall(r'[A-Za-z][A-Za-z0-9_.-]*', match[2])
        if words and all(word in technical for word in words):
            return ''
        # Newly wrapping English sentences in backticks must not exempt them.
        return match[2]

    text = re.sub(r'(`+)(.*?)\1', inline, text)
    text = re.sub(r'!?\[([^\]]*)\]\([^\n]*?\)', r'\1', text)
    text = re.sub(r'https?://[^\s<>]+|<[^>]+>', '', text)
    return text


def language_prose(text, source):
    technical = technical_terms(source)
    return re.sub(r'[A-Za-z][A-Za-z0-9_.-]*',
                  lambda match: '' if match[0] in technical else match[0],
                  prose(text, source))



# Language ID is deliberately lightweight; review still checks translated meaning.
LATIN_WORDS = {
    'es': set('el la los las un una y o de del en por para con sin que es son su sus no antes puede pueden debe consulte nunca todavía ambas ambos'.split()),
    'fr': set('le la les un une et ou de des du dans pour avec sans qui que est sont votre vos ne pas avant peut peuvent doit voir jamais encore'.split()),
    'de': set('der die das den dem des ein eine einen einem eines und oder von im in für mit ohne ist sind ihr ihre ihren ihres nicht vor kann können muss siehe niemals noch beide namens'.split()),
    'pt-BR': set('o a os as um uma e ou de do da em para com sem que é são seu sua não antes pode podem deve veja nunca ainda'.split()),
    'vi': set('và các những một của trong cho với không là được bạn trước khi có thể phải xem chưa bao giờ'.split()),
    'id': set('dan atau yang ini itu sebuah dalam untuk dengan tanpa adalah anda sebelum dapat bisa harus lihat jangan belum tidak'.split()),
    'tr': set('ve veya bir bu için ile olmadan olan sizin önce sonra olabilir gerekir bakın asla henüz değil olarak'.split()),
    'it': set('il lo la gli le un una e o di del della in per con senza che è sono tuo tua non prima può possono deve vedere mai ancora entrambi entrambe'.split()),
    'pl': set('i lub ten ta to te w z do dla bez jest są twoje przed może mogą należy zobacz nigdy jeszcze nie'.split()),
}
DIACRITICS = {'es': 'áéíóúñ¿¡', 'fr': 'àâçéèêëîïôùûüÿœ', 'de': 'äöüß',
              'pt-BR': 'áâãàçéêíóôõú', 'vi': 'ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệịỉọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ',
              'tr': 'çğıöşü', 'it': 'àèéìòù', 'pl': 'ąćęłńóśźż'}
ENGLISH_WORDS = set('the and or a an of in for with without is are your you not before can may must see never yet this that i do to help work people both install command named no'.split())


def check_added_language(text, language, context, source):
    visible = prose(text) if source is None else language_prose(text, source)
    letters = [char for char in visible if char.isalpha()]
    if language in ('ru', 'hi'):
        script = 'CYRILLIC' if language == 'ru' else 'DEVANAGARI'
        localized = [char for char in letters if script in unicodedata.name(char, '')]
        assert letters and len(localized) > len(letters) / 2, f'{context}: target script must be a majority of prose letters'
        assert len(set(localized)) >= min(6, len(localized)), f'{context}: repeated character garbage'
        assert not re.search(r'(.{2,80})\1{3,}', ''.join(localized)), f'{context}: repeated phrase padding'
        return localized
    assert language in LATIN_WORDS, f'Unsupported language: {language}'
    words = re.findall(r"[^\W\d_]+", visible.casefold())
    assert words, f'{context}: missing translated prose'
    counts = {key: sum(word in vocabulary for word in words) for key, vocabulary in LATIN_WORDS.items()}
    score = counts[language]
    if context == 'Document' or len(words) > 7 or score:
        assert score >= max(1, len(words) * .08), f'{context}: insufficient target language stopwords'
        assert any(word in LATIN_WORDS[language] - ENGLISH_WORDS for word in words), f'{context}: missing discriminative target language words'
    # Short imperatives can lack function words. Use the document's language ID,
    # while still rejecting copied English vocabulary in each source block.
    if source is not None:
        source_words = set(re.findall(r"[^\W\d_]+", language_prose(source, source).casefold()))
        copied = sum(word in source_words for word in words)
        assert copied < max(2, len(words) * .5), f'{context}: untranslated English vocabulary'
    # Short natural paragraphs often contain only shared words (un, la, in).
    # Resolve language identity using the complete document's larger sample.
    if context == 'Document':
        assert score >= len(words) * .12, f'{context}: insufficient target language stopwords'
        assert score > max(value for key, value in counts.items() if key != language), f'{context}: wrong or ambiguous language'
    assert sum(word in ENGLISH_WORDS for word in words) <= len(words) * .35, f'{context}: untranslated English stopwords'
    if context == 'Document' and language in DIACRITICS:
        assert any(char in DIACRITICS[language] for char in visible.casefold()), f'{context}: expected target language diacritics'
    localized = [char for char in letters if 'LATIN' in unicodedata.name(char, '')]
    assert len(localized) > len(letters) / 2, f'{context}: target script must be a majority of prose letters'
    assert not re.search(r'(.{2,80})\1{3,}', ''.join(localized)), f'{context}: repeated phrase padding'
    return localized


def check_language_plausibility(localized, language, context):
    # Lightweight grammatical-script checks reject random Unicode sampling.
    # These are broad function characters, never task/caveat keyword matches.
    if len(localized) < 40:
        return
    common = {
        'ko': set('다요는은을를이가에의로와과도서한지할수있없것해합니하주세'),
        'zh-CN': set('的了是在和有与为不这以可将到中个上用者或对从并通过其'),
    }
    if language == 'ja':
        grammatical = sum('HIRAGANA' in unicodedata.name(char, '') for char in localized)
    else:
        grammatical = sum(char in common[language] for char in localized)
    assert grammatical >= len(localized) * 0.05, f'{context}: implausible language (random script garbage)'


def target_letter(char, language):
    name = unicodedata.name(char, '')
    if language == 'ko':
        return 'HANGUL' in name
    han = 'CJK UNIFIED IDEOGRAPH' in name or 'CJK COMPATIBILITY IDEOGRAPH' in name
    if language == 'ja':
        return han or 'HIRAGANA' in name or 'KATAKANA' in name
    assert language == 'zh-CN', f'Unsupported language: {language}'
    return han


def check_language(text, language, context, source=None):
    if language not in ('ko', 'ja', 'zh-CN'):
        return check_added_language(text, language, context, source)
    visible = prose(text) if source is None else language_prose(text, source)
    letters = [char for char in visible if char.isalpha()]
    localized = [char for char in letters if target_letter(char, language)]
    assert letters and len(localized) > len(letters) / 2, f'{context}: target script must be a majority of prose letters'
    if len(localized) >= 20:
        assert len(set(localized)) >= 6, f'{context}: repeated character garbage'
        assert Counter(localized).most_common(1)[0][1] <= len(localized) * 0.4, f'{context}: repeated character padding'
        assert not re.search(r'(.{2,80})\1{3,}', ''.join(localized)), f'{context}: repeated phrase padding'
    check_language_plausibility(localized, language, context)
    return localized


def check_translation(repo, config, baseline):
    repo = Path(repo)
    path = repo / config['translation']
    assert path.is_file(), f'Missing {config["translation"]}'
    english = baseline.decode('utf-8')
    first, rest = english.split('\n', 1)
    expected = first + '\n\n' + config['navigation'] + '\n' + rest
    assert (repo / 'README.md').read_bytes() == expected.encode('utf-8'), 'English README changed beyond the exact added navigation line'
    translated = path.read_bytes().decode('utf-8')
    original_headings, original_fences, original_blocks = parse(english)
    headings, fences, blocks = parse(translated)
    assert headings == original_headings, 'Heading count/levels/order changed'
    assert fences == original_fences, 'Fenced blocks must be byte-identical and in order (including fence markers and final newlines)'
    missing = link_targets(english) - link_targets(translated)
    assert not missing, f'Missing URLs or relative links: {sorted(missing)}'
    assert [kind for kind, _ in original_blocks] == [kind for kind, _ in blocks], 'Preserve every paragraph, list item, table row and code block in section order, including caveats'
    all_prose, seen = [], Counter()
    for index, ((kind, source), (_, actual)) in enumerate(zip(original_blocks, blocks), 1):
        if kind == 'fence':
            continue
        source_prose, actual_prose = prose(source), prose(actual, source)
        source_letters = sum(char.isalpha() for char in source_prose)
        all_prose.append(language_prose(actual, source))
        minimum_length = max(1, int(0.15 * len(source_prose.strip()))) if source_prose.strip() else 0
        assert len(actual_prose.strip()) >= minimum_length, f'Block {index}: missing translated prose'
        # Technical-only/short labels (MIT, Node.js, Pi, etc.) may stay unchanged.
        if len(re.findall(r'[A-Za-z]{2,}', source_prose)) >= 4:
            localized = check_language(actual, config['language'], f'Block {index}', source)
            assert len(localized) >= max(4, source_letters * 0.12), f'Block {index}: insufficient translated coverage'
            normalized_source = ' '.join(source_prose.split()).casefold()
            normalized_actual = ' '.join(actual_prose.split()).casefold()
            source_sentences = re.findall(r'[a-z][a-z ,;’\'-]{35,}[.!?]', normalized_source)
            for sentence in source_sentences:
                assert sentence not in normalized_actual, f'Block {index}: untranslated English sentence'
            source_words = re.findall(r'[a-z]{2,}', language_prose(source, source).casefold())
            actual_words = re.findall(r'[a-z]{2,}', language_prose(actual, source).casefold())
            source_runs = {tuple(source_words[start:start + 6]) for start in range(len(source_words) - 5)}
            assert not any(tuple(actual_words[start:start + 6]) in source_runs for start in range(len(actual_words) - 5)), f'Block {index}: untranslated English word sequence'
            normalized = re.sub(r'\s+', '', ''.join(localized))
            seen[normalized] += 1
            assert seen[normalized] <= 2, f'Block {index}: repeated filler paragraph'
    check_language('\n'.join(all_prose), config['language'], 'Document')
