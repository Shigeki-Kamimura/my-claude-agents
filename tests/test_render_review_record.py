"""render_review_record.py の伏せ処理と出力先・台帳の扱いを確認します。伏せる対象は認証情報だけです。"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'render_review_record.py'
spec = importlib.util.spec_from_file_location('render_review_record', SCRIPT)
rrr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rrr)


def redact(text):
    return rrr.Redactor()(text)


class CredentialRedactionTests(unittest.TestCase):
    def assertHidden(self, text, *secrets):
        result = redact(text)
        for secret in secrets:
            self.assertNotIn(secret, result, f'{secret!r} が残っています: {result!r}')
        self.assertIn('[REDACTED]', result)
        return result

    def test_authorization_any_scheme_to_end_of_line(self):
        # N1: Bearer / Basic 以外の方式でも、方式名に関わらず資格情報の本体を伏せる
        for scheme, body in (('Token', 'abc123tokenbody'), ('Digest', 'response=deadbeefcafe'),
                             ('ApiKey', 'key_9876543'), ('Basic', 'dXNlcjpwYXNzd29yZA=='), ('Bearer', 'eyabcdefghijk')):
            with self.subTest(scheme=scheme):
                result = self.assertHidden(f'Authorization: {scheme} {body}\nContent-Type: text/plain', body)
                self.assertIn('Content-Type: text/plain', result)  # 次の行は残す

    def test_authorization_digest_with_inner_quotes_and_rest_of_line(self):
        self.assertHidden('Authorization: Digest username="alice", realm="r", response="c0ffee00c0ffee"', 'c0ffee00', 'alice')

    def test_authorization_quoted_json_and_escaped_quote(self):
        result = self.assertHidden('{"Authorization": "Token ab\\"cdSECRET", "x": 1}', 'cdSECRET', 'abc')
        self.assertIn('"x": 1', result)

    def test_authorization_nested_json_string(self):
        result = self.assertHidden('{\\"Authorization\\": \\"Digest u=\\\\\\"bob\\\\\\" r=SECRETVAL\\", \\"y\\": 1}', 'SECRETVAL', 'bob')
        self.assertIn('\\"y\\": 1', result)

    def test_authorization_stops_at_json_newline_escape(self):
        result = self.assertHidden('Authorization: Token SECRETVAL\\r\\nHost: example.com', 'SECRETVAL')
        self.assertIn('Host: example.com', result)

    def test_basic_body_hidden(self):
        self.assertHidden('authorization=Basic dXNlcjpwYXNzd29yZA==', 'dXNlcjpwYXNz')

    def test_pem_without_end_is_redacted_to_the_end(self):
        result = self.assertHidden('before\n-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\nmore key lines', 'MIIEowIBAAKCAQEA', 'more key lines')
        self.assertTrue(result.startswith('before'))

    def test_pgp_private_key_block(self):
        text = 'x\n-----BEGIN PGP PRIVATE KEY BLOCK-----\nlQdGBF\n-----END PGP PRIVATE KEY BLOCK-----\ny'
        result = self.assertHidden(text, 'lQdGBF')
        self.assertTrue(result.startswith('x') and result.endswith('y'))

    def test_value_with_spaces_when_quoted(self):
        result = self.assertHidden('password="my secret pass" next=1', 'secret', 'pass"')
        self.assertIn('next=1', result)

    def test_json_escaped_quote_in_value(self):
        # N2: 値に \" を含む
        result = self.assertHidden('{"password": "ab\\"cdTAIL", "other": 1}', 'cdTAIL')
        self.assertIn('"other": 1', result)

    def test_value_over_200_chars(self):
        # N2: 200文字を超える値
        secret = 'A' * 300
        result = self.assertHidden('{"api_key": "' + secret + '", "other": 1}', 'AAAA')
        self.assertIn('"other": 1', result)

    def test_unclosed_quote_hides_to_end_of_line(self):
        result = self.assertHidden("token='unclosed value here\nnext line", 'unclosed', 'here')
        self.assertIn('next line', result)

    def test_digits_only_credential(self):
        # N2: 数字だけの認証情報
        self.assertHidden('password=123456789', '123456789')
        self.assertHidden('api_key: 987654321', '987654321')

    def test_non_ascii_unquoted_credential_with_ascii_alnum(self):
        # N2: 非ASCII文字を含む引用符なしの値(英数字を含むものは認証情報として伏せる)
        self.assertHidden('password=パスワード123', 'パスワード123')

    def test_url_credentials_with_at_in_password(self):
        # N2: パスワードに@を含むURL
        result = self.assertHidden('postgres://user:p@ss:w0rd@db.example.com:5432/app', 'p@ss', 'w0rd')
        self.assertIn('@db.example.com:5432/app', result)

    def test_url_credentials_plain(self):
        self.assertHidden('https://user:hunter2@example.com/x', 'hunter2')

    def test_non_credential_values_are_kept(self):
        # 方針: 認証情報だけを伏せる。散文、件数、認証情報でない設定は残す
        text = ('max_tokens: 4096 "input_tokens": 1234 token_count=77 password: required '
                'note: 日本語の説明 password: 必要です https://example.com:8080/path git@github.com:org/repo.git '
                'empty: "" name=alice mode=fast')
        self.assertEqual(text, redact(text))

    def test_counts_are_kept_but_digits_after_other_keys_are_hidden(self):
        result = redact('max_tokens: 4096 secret: 5555555')
        self.assertIn('max_tokens: 4096', result)
        self.assertNotIn('5555555', result)

    def test_already_redacted_authorization_is_not_counted_again(self):
        redactor = rrr.Redactor()
        once = redactor('Authorization: Token abcdefgh')
        redactor.counts.clear()
        self.assertEqual(once, redactor(once))
        self.assertEqual(0, sum(redactor.counts.values()))

    def test_pathological_inputs_finish_quickly(self):
        import time
        started = time.monotonic()
        for text in ('token="' * 50000, '://a:' * 50000, 'Authorization: ' * 20000, 'password="a ' * 20000):
            redact(text)
        self.assertLess(time.monotonic() - started, 10)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='render record ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / 'log.jsonl'
        self.log.write_text(json.dumps({'role': 'user', 'text': 'hello Authorization: Token SECRETVAL'}) + '\n', encoding='utf-8')

    def run_main(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = rrr.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_creates_nested_missing_output_directory(self):
        out = self.root / 'a' / 'b' / 'record.html'
        code, _, err = self.run_main('--out', str(out), str(self.log))
        self.assertEqual(0, code, err)
        html_text = out.read_text(encoding='utf-8')
        self.assertNotIn('SECRETVAL', html_text)
        self.assertIn('[REDACTED]', html_text)

    def test_bad_ledger_has_ledger_message(self):
        ledger = self.root / 'ledger.json'
        ledger.write_text('{"not": "an array"}', encoding='utf-8')
        out = self.root / 'record.html'
        code, _, err = self.run_main('--out', str(out), '--ledger', str(ledger), str(self.log))
        self.assertEqual(2, code)
        self.assertIn('台帳を読めません', err)
        self.assertFalse(out.exists())

    def test_invalid_ledger_json_has_ledger_message(self):
        ledger = self.root / 'ledger.json'
        ledger.write_text('{broken', encoding='utf-8')
        code, _, err = self.run_main('--out', str(self.root / 'record.html'), '--ledger', str(ledger), str(self.log))
        self.assertEqual(2, code)
        self.assertIn('台帳を読めません', err)

    def test_ledger_values_are_redacted(self):
        ledger = self.root / 'ledger.json'
        ledger.write_text(json.dumps([{'id': 'N1', 'summary': 'Authorization: Digest LEDGERSECRET'}]), encoding='utf-8')
        out = self.root / 'record.html'
        code, _, err = self.run_main('--out', str(out), '--ledger', str(ledger), str(self.log))
        self.assertEqual(0, code, err)
        self.assertNotIn('LEDGERSECRET', out.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
