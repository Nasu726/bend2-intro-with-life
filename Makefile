.PHONY: pdf test oracle check bend-check help

help:
	@echo 'make pdf        - rebuild PDF (XeLaTeX, three passes)'
	@echo 'make test       - test the independent Python oracle'
	@echo 'make check      - compare Bend Life output to Python oracle'
	@echo 'make bend-check - Bend typecheck each example except INVALID (requires bend)'

pdf:
	mkdir -p build
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build Bend2_Life_Textbook.tex
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build Bend2_Life_Textbook.tex
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=build Bend2_Life_Textbook.tex
	cp build/Bend2_Life_Textbook.pdf ライフゲームで学ぶ_はじめてのBend2.pdf

test:
	python3 -m unittest discover -s tests -v

oracle:
	python3 scripts/reference.py

check:
	python3 scripts/check_bend.py

bend-check:
	@command -v bend >/dev/null || { echo 'ERROR: bend command not installed'; exit 2; }
	@set -e; for f in src/*.bend; do case "$$f" in *INVALID*) echo "SKIP $$f";; *) echo "CHECK $$f"; bend "$$f" --check-only;; esac; done

.PHONY: bend-test
bend-test:
	python3 scripts/test_bend_runtime.py
