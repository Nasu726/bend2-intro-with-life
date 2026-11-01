#!/usr/bin/env python3
"""Inventory TeX teaching signals; structural presence is not editorial approval."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = re.compile(r"^\\chapter\{([^}\n]+)\}", re.MULTILINE)
SECTION = re.compile(r"^\\section\{([^}\n]+)\}", re.MULTILINE)
SAMPLE = re.compile(r"\\sample\{([^}\n]+)\}")
CODE = re.compile(r"\\begin\{lstlisting\}")
OUTPUT = re.compile(r"実行結果|出力|表示され|表示します")


def blocks(text, pattern):
    marks = list(pattern.finditer(text))
    return [(m.group(1), text[m.end():marks[i+1].start() if i+1 < len(marks) else len(text)])
            for i, m in enumerate(marks)]


def command_bodies(text, command):
    needle = "\\" + command + "{"
    bodies = []
    pos = 0
    while (at := text.find(needle, pos)) != -1:
        start = at + len(needle)
        end = start
        depth = 1
        while end < len(text) and depth:
            if text[end] in "{}" and (end == 0 or text[end-1] != "\\"):
                depth += 1 if text[end] == "{" else -1
            end += 1
        if depth:
            raise ValueError(f"Unclosed {command} at {at}")
        bodies.append(text[start:end-1].strip())
        pos = end
    return bodies


def target_ending(text):
    return bool(re.search(r"[てで]みましょう[。！？!?]?\s*$", text))


def inventory(text, filenames):
    result, referenced = [], []
    for number, (title, body) in enumerate(blocks(text, CHAPTER), 1):
        sections = blocks(body, SECTION)
        samples = SAMPLE.findall(body)
        exercises = command_bodies(body, "exercise")
        referenced.extend(samples)
        result.append({
            "number": number, "title": title, "sections": len(sections),
            "sample_refs": len(samples),
            "code_sections": sum(bool(SAMPLE.search(s) or CODE.search(s)) for _, s in sections),
            "exercise_sections": sum(bool(command_bodies(s, "exercise")) for _, s in sections),
            "exercises": len(exercises),
            "ending_review": sum(not target_ending(e) for e in exercises),
            "output_sections": sum(bool(OUTPUT.search(s)) for _, s in sections)
        })
    return result, sorted(set(referenced) - filenames)



def review_details(text):
    """Return actionable locations; these are editorial hints, not failures."""
    chapters = list(CHAPTER.finditer(text))
    sections = list(SECTION.finditer(text))

    def location(offset):
        chapter = next((m for m in reversed(chapters) if m.start() <= offset), None)
        section = next((m for m in reversed(sections)
                        if m.start() <= offset and
                        (chapter is None or m.start() > chapter.start())), None)
        return {
            "chapter": chapters.index(chapter) + 1 if chapter else None,
            "section": section.group(1) if section else None,
            "line": text.count("\n", 0, offset) + 1,
        }

    details = []
    needle = r"\exercise{"
    pos = 0
    while (at := text.find(needle, pos)) >= 0:
        start = at + len(needle)
        depth = 1
        end = start
        while end < len(text) and depth:
            if text[end] in "{}" and (end == 0 or text[end-1] != "\\"):
                depth += 1 if text[end] == "{" else -1
            end += 1
        if depth:
            raise ValueError(f"Unclosed exercise at {at}")
        body = text[start:end-1].strip()
        if not target_ending(body):
            details.append({**location(at), "kind": "exercise_ending",
                            "excerpt": body[-90:]})
        pos = end

    # A historical statement now conflicts with the later verified X11 GUI.
    phrase = "GUIはまだ統合していません。"
    pos = 0
    while (at := text.find(phrase, pos)) >= 0:
        details.append({**location(at), "kind": "stale_gui_status",
                        "excerpt": phrase})
        pos = at + len(phrase)
    return sorted(details, key=lambda x: x["line"])

def main():
    import json
    text = (ROOT / "Intermediate_Textbook.tex").read_text(encoding="utf-8")
    filenames = {p.name for p in (ROOT / "src").glob("*.bend")}
    rows, missing = inventory(text, filenames)
    print("chapter,sections,code_sections,exercise_sections,exercises,ending_review,output_word_sections")
    for r in rows:
        print(",".join(map(str, [r["number"], r["sections"], r["code_sections"],
                                r["exercise_sections"], r["exercises"], r["ending_review"],
                                r["output_sections"]])))
    print(f"total chapters={len(rows)} sections={sum(x['sections'] for x in rows)} "
          f"exercises={sum(x['exercises'] for x in rows)} "
          f"ending_review={sum(x['ending_review'] for x in rows)}")
    print(f"missing samples={missing}")
    if "--details" in sys.argv[1:]:
        for item in review_details(text):
            print(json.dumps(item, ensure_ascii=False))
    # Only actual missing sample references or a changed chapter count fail.
    # Lexical code/output/exercise signals are review hints, not acceptance.
    return 0 if len(rows) == 23 and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
