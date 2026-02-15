SHELL := /bin/bash

NPM_GLOBAL := .npm-global
export NPM_CONFIG_PREFIX := $(PWD)/$(NPM_GLOBAL)
export PATH := $(PWD)/$(NPM_GLOBAL)/bin:$(PATH)
export PORT := 4000

.PHONY: dev setup install clean

dev: setup install
	pnpm run dev

setup:
	mkdir -p "$(NPM_GLOBAL)"
	command -v pnpm >/dev/null 2>&1 || npm install -g pnpm

install:
	pnpm install

clean:
	rm -rf node_modules
