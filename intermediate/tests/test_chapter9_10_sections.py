"""Section-level regression for chapter 9 (Chan/Poll) and chapter 10 (TCP/UDP).

Static reader/source/runner consistency only. The Intermediate CI performs
Bend typechecking and finite runtime checks; this does not prove scheduler
fairness, timeout cancellation, network delivery, or complete TCP framing.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{[^}\n]+\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}]+)\}")


def chapter_body(source: str, number: int) -> str:
    headers = list(CHAPTER.finditer(source))
    if len(headers) != 23:
        raise AssertionError(f"Expected 23 chapters, got {len(headers)}")
    start = headers[number - 1].end()
    end = headers[number].start() if number < len(headers) else len(source)
    return source[start:end]


def sections(body: str) -> list[tuple[str, str]]:
    headers = list(SECTION.finditer(body))
    return [
        (header.group(1),
         body[header.end():headers[i + 1].start() if i + 1 < len(headers) else len(body)])
        for i, header in enumerate(headers)
    ]


class ConcurrencyNetworkSectionReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "Intermediate_Textbook.tex").read_text(encoding="utf-8")
        cls.chapter9 = sections(chapter_body(source, 9))
        cls.chapter10 = sections(chapter_body(source, 10))

    def test_chapter9_eight_sections_and_samples(self):
        expected = [
            ("「二つの仕事を始める」と「結果を待つ」", ["21_io_fork.bend"]),
            ("Chanは何を受け渡すのか", []),
            ("送る側と受け取る側を一つの例で確認する", ["28_chan_roundtrip.bend"]),
            ("時間内に終わらなかったら", ["29_io_within.bend"]),
            ("時間制限は仕事の中止ではない", []),
            ("Pollは「いま待つ必要がある」を表す", []),
            ("空のチャネルを試して、受信待ちを見分ける", ["53_chan_poll.bend"]),
            ("いつ使うべきか", []),
        ]
        self.assertEqual([(title, SAMPLE.findall(body)) for title, body in self.chapter9],
                         expected)
        for _, samples in expected:
            for name in samples:
                with self.subTest(sample=name):
                    self.assertTrue((ROOT / "src" / name).is_file())

    def test_chapter10_eight_sections_and_samples(self):
        expected = [
            ("通信はファイルと似ているだろうか", []),
            ("TCPは接続を作ってから使う", []),
            ("UDPは何が違うのか", []),
            ("接続できなかった場合の最小例", ["27_tcp_connect.bend"]),
            ("TCPで一文字を届ける", ["47_tcp_loopback.bend"]),
            ("UDPで一つのデータグラムを受け取る", ["48_udp_loopback.bend"]),
            ("安全に試すには", []),
            ("通信データには境界が必要", ["44_message_boundary.bend"]),
        ]
        self.assertEqual([(title, SAMPLE.findall(body)) for title, body in self.chapter10],
                         expected)
        for _, samples in expected:
            for name in samples:
                with self.subTest(sample=name):
                    self.assertTrue((ROOT / "src" / name).is_file())

    def test_chapter9_results_and_unverified_states_are_distinct(self):
        body = dict(self.chapter9)
        self.assertIn("実行結果は7", body["「二つの仕事を始める」と「結果を待つ」"])
        self.assertIn("Chan.close", body["Chanは何を受け渡すのか"])
        timeout = body["時間制限は仕事の中止ではない"]
        for phrase in ("Timed out", "仕事を強制終了した", "重複排除", "Fail"):
            self.assertIn(phrase, timeout)
        poll = body["Pollは「いま待つ必要がある」を表す"]
        for phrase in ("Ready{Some{v}}", "Ready{None{}}", "Wait{Unit{}}",
                       "まだ送れていない値"):
            self.assertIn(phrase, poll)
        observed = body["空のチャネルを試して、受信待ちを見分ける"]
        for phrase in ("0\n9\n", "0はPollの返り値そのものではありません",
                       "閉じた後の受信を試していません", "送信側の待機"):
            self.assertIn(phrase, observed)
        self.assertIn(r"\exercise{", body["いつ使うべきか"])

    def test_chapter10_results_and_network_boundaries(self):
        body = dict(self.chapter10)
        self.assertIn("失敗を保証する例ではありません",
                      body["接続できなかった場合の最小例"])
        tcp = body["TCPで一文字を届ける"]
        for phrase in ("24候補", "TCP.recv", "一バイト",
                       "ネットワークが禁止された実行環境"):
            self.assertIn(phrase, tcp)
        udp = body["UDPで一つのデータグラムを受け取る"]
        for phrase in ("BEND-UDP", "UDP.recv_from", "UDPが常に届くわけではありません"):
            self.assertIn(phrase, udp)
        framing = body["通信データには境界が必要"]
        for phrase in ("2n", "String.split", "未完了の部分を保持",
                       "ソケットの受信や未完了データの蓄積は実装していません"):
            self.assertIn(phrase, framing)
        self.assertIn("127.0.0.1", body["安全に試すには"])

    def test_reader_bend_code_matches_taught_operations(self):
        def source(name: str) -> str:
            return (ROOT / "src" / name).read_text(encoding="utf-8")

        fork = source("21_io_fork.bend")
        self.assertIn("IO.fork(U32, IO.pure(U32, 7))", fork)
        self.assertIn("IO.join(U32, chan)", fork)
        roundtrip = source("28_chan_roundtrip.bend")
        self.assertIn("Chan.send(U32, chan, 9)", roundtrip)
        self.assertIn("Chan.recv(U32, chan)", roundtrip)
        self.assertIn("Chan.close(U32, chan)", roundtrip)
        self.assertIn("IO.within(U32, 1000, IO.pure(U32, 7))",
                      source("29_io_within.bend"))
        poll = source("53_chan_poll.bend")
        self.assertEqual(poll.count("Chan.try_recv(U32, chan, 0)"), 2)
        self.assertIn("Chan.send(U32, chan, 9)", poll)
        self.assertIn("case None{}:", poll)  # Branch exists, but is not exercised.
        self.assertLess(poll.index("full: Poll"), poll.index("Chan.close(U32, chan)"))
        tcp = source("47_tcp_loopback.bend")
        for phrase in ('TCP.send(client, "B")', "TCP.recv(server, 1)",
                       "listen_any(24n", '"127.0.0.1"'):
            self.assertIn(phrase, tcp)
        udp = source("48_udp_loopback.bend")
        for phrase in ('"BEND-UDP"', "UDP.recv_from(socket, 64)", "bind_any(24n"):
            self.assertIn(phrase, udp)
        self.assertIn('String.split("ABC|DEF", Chr{124})',
                      source("44_message_boundary.bend"))
        self.assertIn('TCP.connect("127.0.0.1", 1)',
                      source("27_tcp_connect.bend"))

    def test_existing_runtime_runner_covers_finite_exercise_variants(self):
        runner = (ROOT / "scripts" / "test_examples.py").read_text(encoding="utf-8")
        for phrase in ('poll_output.splitlines() != ["0", "9"]',
                       '("47_tcp_loopback.bend", "B")',
                       '("48_udp_loopback.bend", "BEND-UDP")',
                       'TCP.send(client, "7")',
                       'TCP.send(client, "BEND")',
                       'UDP.send_to(socket, "127.0.0.1", port, "HELLO")',
                       'String.split("ABCDEF", Chr{124})',
                       'String.split("A|B|C", Chr{124})',
                       'run("bend", str(copy), "--check-only")'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner)


    def test_exercise_substitution_baselines_are_unique(self):
        """Exercise mutations must change one exact Bend expression each."""
        variants = (
            ("47_tcp_loopback.bend", 'TCP.send(client, "B")'),
            ("48_udp_loopback.bend",
             'UDP.send_to(socket, "127.0.0.1", port, "BEND-UDP")'),
            ("44_message_boundary.bend", 'String.split("ABC|DEF", Chr{124})'),
        )
        for name, baseline in variants:
            with self.subTest(sample=name):
                source = (ROOT / "src" / name).read_text(encoding="utf-8")
                self.assertEqual(source.count(baseline), 1)


if __name__ == "__main__":
    unittest.main()
