ifneq (,$(wildcard .env))
include .env
endif

PLUGIN_NAME = OpenLigaDB
PACKAGE_NAME = enigma2-plugin-extensions-openligadb
VERSION := $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')

BUILD_DIR = build
IPK_WORK_DIR = $(BUILD_DIR)/ipk
DATA_STAGING = $(IPK_WORK_DIR)/data
CONTROL_STAGING = $(IPK_WORK_DIR)/control

PLUGIN_PATH = usr/lib/enigma2/python/Plugins/Extensions/$(PLUGIN_NAME)
OUTPUT_IPK = $(BUILD_DIR)/$(PACKAGE_NAME)_$(VERSION)_all.ipk

DOS2UNIX_BIN := $(shell command -v dos2unix 2>/dev/null)
MSGFMT_BIN  := $(shell command -v msgfmt 2>/dev/null)

.PHONY: compile-locales all build clean normalize prepare ipk install restart deploy

all: ipk

build: ipk

clean:
	rm -rf $(BUILD_DIR)

normalize:
ifneq ($(DOS2UNIX_BIN),)
	find src control -type f -exec dos2unix {} \;
endif

compile-locales:
ifneq ($(MSGFMT_BIN),)
	@for lang in de en it es; do \
		po=src/$(PLUGIN_NAME)/locale/$$lang/LC_MESSAGES/$(PLUGIN_NAME).po; \
		mo=src/$(PLUGIN_NAME)/locale/$$lang/LC_MESSAGES/$(PLUGIN_NAME).mo; \
		if [ -f "$$po" ]; then \
			$(MSGFMT_BIN) -o "$$mo" "$$po"; \
		fi; \
	done
else
	@echo "msgfmt not found - skipping locale compilation"
endif


prepare: normalize compile-locales
	mkdir -p $(DATA_STAGING)/$(PLUGIN_PATH)
	mkdir -p $(CONTROL_STAGING)
	cp -r src/$(PLUGIN_NAME)/* $(DATA_STAGING)/$(PLUGIN_PATH)/
	cp control/control $(CONTROL_STAGING)/
	sed -i 's/^Version:.*/Version: $(VERSION)/' $(CONTROL_STAGING)/control
	cp control/postinst $(CONTROL_STAGING)/
	cp control/prerm $(CONTROL_STAGING)/
	chmod 755 $(CONTROL_STAGING)/postinst $(CONTROL_STAGING)/prerm

ipk: clean prepare
	cd $(IPK_WORK_DIR) && \
	tar -czf data.tar.gz -C data . && \
	tar -czf control.tar.gz -C control . && \
	echo "2.0" > debian-binary && \
	ar r $(PACKAGE_NAME)_$(VERSION)_all.ipk debian-binary control.tar.gz data.tar.gz
	mv $(IPK_WORK_DIR)/$(PACKAGE_NAME)_$(VERSION)_all.ipk $(OUTPUT_IPK)

install: ipk
	@test -n "$(BOX_HOST)" && test -n "$(BOX_PORT)" && test -n "$(BOX_USER)"
	scp -P $(BOX_PORT) $(OUTPUT_IPK) $(BOX_USER)@$(BOX_HOST):/tmp/
	ssh -p $(BOX_PORT) $(BOX_USER)@$(BOX_HOST) "opkg install --force-reinstall /tmp/$(PACKAGE_NAME)_$(VERSION)_all.ipk"

apply:
	@test -n "$(BOX_HOST)" && test -n "$(BOX_PORT)" && test -n "$(BOX_USER)"
	ssh -p $(BOX_PORT) $(BOX_USER)@$(BOX_HOST) \
	    "init 4 >/dev/null 2>&1 || killall -9 enigma2 >/dev/null 2>&1 || true; sleep 2; init 3 >/dev/null 2>&1 || true"

restart: apply

deploy: install apply