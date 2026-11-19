# Edit Master Skill — developer tasks.
# Recipes are indented with real tabs. Spaces break make.

VERSION ?= $(shell git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
ifeq ($(strip $(VERSION)),)
VERSION := 1.0.0
endif
REPO      := https://github.com/Dani-Devlop/edit-master-skill
SKILL_DIR := $(HOME)/.claude/skills/edit-master

.DEFAULT_GOAL := help
.PHONY: help install lint docs test clean release

help:
	@echo "edit-master-skill — make targets"
	@echo "  help     show this list (default)"
	@echo "  install  clone (if needed) and copy the skill to $(SKILL_DIR)"
	@echo "  lint     run markdownlint-cli2 over all markdown"
	@echo "  docs     list the documentation set"
	@echo "  test     explain the 25-video protocol; check scores.csv"
	@echo "  clean    remove build artifacts (*.bak, site/, dist/)"
	@echo "  release  create the annotated tag v$(VERSION)"

install:
	@if test -f SKILL.md; then \
		src=.; \
	elif test -d edit-master-skill; then \
		src=edit-master-skill; \
	else \
		echo "Cloning $(REPO)"; \
		git clone $(REPO).git; \
		src=edit-master-skill; \
	fi; \
	mkdir -p $(HOME)/.claude/skills; \
	rm -rf $(SKILL_DIR); \
	cp -r $$src $(SKILL_DIR); \
	echo "Installed: $(SKILL_DIR)"; \
	echo "Verify inside Claude Code with /skills, or ask the agent."

lint:
	@if command -v markdownlint-cli2 >/dev/null 2>&1; then \
		markdownlint-cli2 '**/*.md'; \
	else \
		echo "markdownlint-cli2 not found."; \
		echo "Install: npm install -g markdownlint-cli2"; \
		echo "Config:  .markdownlint.jsonc"; \
	fi

docs:
	@echo "Documentation set:"
	@ls docs/
	@echo "Start with docs/INSTALLATION.md, then docs/WORKFLOWS.md."

test:
	@echo "Test protocol: tests/README.md"
	@echo "25 videos across 16 categories, scored 1-10 on six dimensions."
	@echo "Overall is the average; any dimension at 3 or lower is a FAIL."
	@echo "Honest reporting: never fabricate an edited video."
	@if test -f test-results/scores.csv; then \
		rows=$$(wc -l < test-results/scores.csv | tr -d ' '); \
		echo "test-results/scores.csv: $$rows lines (header + 25 expected)"; \
		head -n 1 test-results/scores.csv; \
	else \
		echo "test-results/scores.csv not found yet. Run the matrix first."; \
	fi

clean:
	@rm -f *.bak
	@rm -rf site dist
	@echo "Cleaned: *.bak, site/, dist/"

release:
	@echo "NOTE: releases are unsigned by policy (Verified-or-nothing badge rule)."
	git tag -a v$(VERSION) -m "v$(VERSION)"
	@echo "Tagged v$(VERSION). Push it with: git push origin v$(VERSION)"
