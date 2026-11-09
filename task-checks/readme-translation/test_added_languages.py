"""Draft reference translations for the shared structural fixture."""
import pytest
from test_translation_check import ENGLISH
from translation_check import check_translation, load_task, parse

# Each draft preserves authorization, credentials, unpaid work and acceptance caveats.
DRAFTS = {
'es': ('Ejemplo', 'Busque tareas útiles y lea los requisitos antes de contribuir.', 'Autorización y credenciales', 'Elija el trabajo dentro de la autorización de su responsable. Nunca comparta sus credenciales privadas.', 'Límites', 'Las tareas normales pueden ser gratuitas. Los saldos del sitio no pueden convertirse en efectivo todavía. La entrega no es la aceptación.', 'Consulte la [documentación](docs/guide.md) y https://example.org/api.'),
'fr': ('Exemple', 'Trouvez des tâches utiles et lisez les exigences avant de contribuer.', 'Autorisation et identifiants', 'Choisissez le travail dans les limites de votre autorisation humaine. Ne partagez jamais vos identifiants privés.', 'Limites', 'Les tâches ordinaires peuvent être non rémunérées. Les soldes du site ne peuvent pas encore être retirés en espèces. La soumission ne vaut pas acceptation.', 'Voir la [documentation](docs/guide.md) et https://example.org/api.'),
'de': ('Beispiel', 'Suchen Sie nützliche Aufgaben und lesen Sie die Anforderungen vor dem Mitwirken.', 'Berechtigung und Zugangsdaten', 'Wählen Sie die Arbeit im Rahmen der Berechtigung Ihres Menschen. Teilen Sie niemals Ihre privaten Zugangsdaten.', 'Grenzen', 'Die normalen Aufgaben können unbezahlt sein. Das Guthaben der Website kann noch nicht ausgezahlt werden. Die Einreichung ist keine Annahme.', 'Siehe die [Dokumentation](docs/guide.md) und https://example.org/api.'),
'pt-BR': ('Exemplo', 'Encontre tarefas úteis e leia os requisitos antes de contribuir.', 'Autorização e credenciais', 'Escolha o trabalho dentro da autorização da sua pessoa responsável. Nunca compartilhe suas credenciais privadas.', 'Limites', 'As tarefas comuns podem ser gratuitas. Os saldos do site não podem ser sacados ainda. A entrega não é a aceitação.', 'Veja a [documentação](docs/guide.md) e https://example.org/api.'),
'vi': ('Ví dụ', 'Tìm các nhiệm vụ hữu ích và đọc các yêu cầu trước khi đóng góp.', 'Quyền và thông tin xác thực', 'Chọn công việc trong phạm vi được người phụ trách của bạn cho phép. Không bao giờ chia sẻ thông tin xác thực riêng của bạn.', 'Giới hạn', 'Các nhiệm vụ thông thường có thể không được trả tiền. Số dư của trang chưa thể đổi thành tiền mặt. Việc nộp không có nghĩa là được chấp nhận.', 'Xem [tài liệu](docs/guide.md) và https://example.org/api.'),
'id': ('Contoh', 'Cari tugas yang berguna dan baca persyaratan sebelum berkontribusi.', 'Otorisasi dan kredensial', 'Pilih pekerjaan dalam otorisasi manusia anda. Jangan pernah membagikan kredensial pribadi anda.', 'Batasan', 'Tugas biasa bisa tidak dibayar. Saldo situs belum dapat diuangkan. Pengiriman tidak berarti penerimaan.', 'Lihat [dokumentasi](docs/guide.md) dan https://example.org/api.'),
'hi': ('उदाहरण', 'उपयोगी कार्य खोजें और योगदान करने से पहले आवश्यकताएँ पढ़ें।', 'अनुमति और पहचान संबंधी जानकारी', 'अपने मानव की अनुमति के दायरे में कार्य चुनें। अपनी निजी पहचान संबंधी जानकारी कभी साझा न करें।', 'सीमाएँ', 'सामान्य कार्य बिना भुगतान के हो सकते हैं। साइट की शेष राशि अभी नकद नहीं निकाली जा सकती। प्रस्तुत करने का अर्थ स्वीकृति नहीं है।', '[दस्तावेज़](docs/guide.md) और https://example.org/api देखें।'),
'ru': ('Пример', 'Найдите полезные задачи и прочитайте требования перед участием.', 'Разрешение и учётные данные', 'Выбирайте работу в пределах разрешения вашего человека. Никогда не передавайте свои личные учётные данные.', 'Ограничения', 'Обычные задачи могут быть неоплачиваемыми. Средства на сайте пока нельзя обналичить. Отправка не означает принятия.', 'Смотрите [документацию](docs/guide.md) и https://example.org/api.'),
'it': ('Esempio', 'Trova le attività utili e leggi i requisiti prima di contribuire.', 'Autorizzazione e credenziali', 'Scegli il lavoro nei limiti della tua autorizzazione umana. Non condividere mai le tue credenziali private.', 'Limiti', 'Le attività normali possono essere gratuite. I saldi del sito non possono ancora essere convertiti in contanti. La consegna non è accettazione.', 'Vedere la [documentazione](docs/guide.md) e https://example.org/api.'),
'pl': ('Przykład', 'Znajdź przydatne zadania i przeczytaj wymagania przed udziałem.', 'Upoważnienie i dane uwierzytelniające', 'Wybierz pracę w granicach upoważnienia twojego człowieka. Nigdy nie udostępniaj swoich prywatnych danych uwierzytelniających.', 'Ograniczenia', 'Zwykłe zadania mogą być bezpłatne. Środków na stronie nie można jeszcze wypłacić w gotówce. Zgłoszenie nie oznacza akceptacji.', 'Zobacz [dokumentację](docs/guide.md) i https://example.org/api.'),
 'tr': ('Örnek', 'Yararlı görevleri bulun ve katkıda bulunmadan önce gereksinimleri okuyun.', 'Yetki ve kimlik bilgileri', 'İnsanınızın yetkisi içinde olan bir işi seçin. Özel kimlik bilgilerinizi asla paylaşmayın.', 'Sınırlar', 'Normal görevler için ödeme olmayabilir. Sitedeki bakiyeler henüz nakde çevrilemez. Gönderim kabul olarak sayılmaz.', '[Belgelere](docs/guide.md) ve https://example.org/api adresine bakın.'),
}


def draft(language):
    title, intro, auth, credentials, limits, caveat, link = DRAFTS[language]
    return f'# {title}\n\n{intro}\n\n## {auth}\n\n{credentials}\n\n```sh\nexample tasks --limit 3\n```\n\n## {limits}\n\n{caveat}\n\n{link}\n'


@pytest.mark.parametrize('language', DRAFTS)
def test_reference_draft_passes(tmp_path, language):
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': f'English · [{language}](README.{language}.md)'}
    (tmp_path / 'README.md').write_text(ENGLISH.replace('# Example\n', '# Example\n\n' + config['navigation'] + '\n', 1))
    (tmp_path / config['translation']).write_text(draft(language))
    check_translation(tmp_path, config, ENGLISH.encode())


@pytest.mark.parametrize('language', DRAFTS)
@pytest.mark.parametrize('attack', ['english', 'wrong-language', 'truncated', 'dropped-section'])
def test_broken_draft_rejected(tmp_path, language, attack):
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': f'English · [{language}](README.{language}.md)'}
    (tmp_path / 'README.md').write_text(ENGLISH.replace('# Example\n', '# Example\n\n' + config['navigation'] + '\n', 1))
    text = draft(language)
    if attack == 'english':
        text = ENGLISH
    elif attack == 'wrong-language':
        text = draft('fr' if language == 'es' else 'es')
    elif attack == 'truncated':
        text = text[:len(text) // 2]
    else:
        text = text.replace(DRAFTS[language][5] + '\n\n', '')
    (tmp_path / config['translation']).write_text(text)
    with pytest.raises(AssertionError):
        check_translation(tmp_path, config, ENGLISH.encode())


@pytest.mark.parametrize('target', DRAFTS)
@pytest.mark.parametrize('other', DRAFTS)
def test_every_other_language_is_rejected(tmp_path, target, other):
    if target == other:
        return
    config = {'language': target, 'translation': f'README.{target}.md', 'navigation': 'English'}
    (tmp_path / 'README.md').write_text(ENGLISH.replace('# Example\n', '# Example\n\nEnglish\n', 1))
    (tmp_path / config['translation']).write_text(draft(other))
    with pytest.raises(AssertionError):
        check_translation(tmp_path, config, ENGLISH.encode())


@pytest.mark.parametrize('repo', ['mcp', 'cli', 'work-skill', 'remote', 'examples', 'pi'])
@pytest.mark.parametrize('language', DRAFTS)
def test_new_pinned_configuration(repo, language):
    config, baseline = load_task(f'{repo}-{language}')
    assert config['repository'] == f'andrewsiah/agentswarm-{repo}'
    assert config['language'] == language
    assert parse(baseline.decode())[0]


@pytest.mark.parametrize('language,sentence', [
    ('es', 'Ambas versiones instalan un comando llamado `agentswarm`.'),
    ('es', 'Ambas versiones instalan `agentswarm`.'),
    ('it', 'Entrambi installano `agentswarm`.'),
    ('de', 'Beide installieren einen Befehl namens `agentswarm`.'),
])
def test_natural_short_translation_block_passes(tmp_path, language, sentence):
    source = 'Both install a command called `agentswarm`.'
    baseline = ENGLISH.replace(ENGLISH.split('\n\n')[1], source)
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': 'English'}
    (tmp_path / 'README.md').write_text(baseline.replace('# Example\n', '# Example\n\nEnglish\n', 1))
    (tmp_path / config['translation']).write_text(draft(language).replace(DRAFTS[language][1], sentence))
    check_translation(tmp_path, config, baseline.encode())


@pytest.mark.parametrize('language', DRAFTS)
def test_english_paragraph_substitution_fails(tmp_path, language):
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': 'English'}
    (tmp_path / 'README.md').write_text(ENGLISH.replace('# Example\n', '# Example\n\nEnglish\n', 1))
    (tmp_path / config['translation']).write_text(draft(language).replace(DRAFTS[language][1], 'I do work to help people.'))
    with pytest.raises(AssertionError):
        check_translation(tmp_path, config, ENGLISH.encode())


def test_baseline_bytes_match_pinned_git_blobs():
    import hashlib
    import json
    from pathlib import Path
    here = Path(__file__).parent
    for name, expected in json.loads((here / 'baseline_blobs.json').read_text()).items():
        content = (here / name).read_bytes()
        assert hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest() == expected


@pytest.mark.parametrize('language,sentence', [
    ('de', 'Discover useful assignments in public projects before contributing.'),
    ('es', 'No special credentials required; discover suitable assignments before contributing.'),
])
def test_shared_stopwords_cannot_identify_english_as_target(tmp_path, language, sentence):
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': 'English'}
    (tmp_path / 'README.md').write_text(ENGLISH.replace('# Example\n', '# Example\n\nEnglish\n', 1))
    (tmp_path / config['translation']).write_text(draft(language).replace(DRAFTS[language][1], sentence))
    with pytest.raises(AssertionError):
        check_translation(tmp_path, config, ENGLISH.encode())


@pytest.mark.parametrize('language,source,sentence', [
    ('es', 'Then run `/reload` or restart Pi.', 'Luego ejecuta `/reload` o reinicia Pi.'),
    ('id', 'Both install a command called `agentswarm`.', 'Keduanya memasang perintah bernama `agentswarm`.'),
])
def test_short_imperatives_use_document_language_evidence(tmp_path, language, source, sentence):
    baseline = ENGLISH.replace(ENGLISH.split('\n\n')[1], source)
    config = {'language': language, 'translation': f'README.{language}.md', 'navigation': 'English'}
    (tmp_path / 'README.md').write_text(baseline.replace('# Example\n', '# Example\n\nEnglish\n', 1))
    (tmp_path / config['translation']).write_text(draft(language).replace(DRAFTS[language][1], sentence))
    check_translation(tmp_path, config, baseline.encode())
