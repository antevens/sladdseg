VENV ?= .venv
PY ?= $(abspath $(VENV))/bin/python
CAD = cad/build123d

# OrcaSlicer: pinned Linux AppImage, fetched + verified by `make slicer`.
# Override with SLICER=/path/to/OrcaSlicer.AppImage (or squashfs-root/AppRun).
ORCA_VERSION ?= 2.4.2
ORCA_SHA256 ?= d12fb8c8eac1aecd2dfb6377acd48f994f8fa439ed5292fa532dd82880f029fd
ORCA_URL = https://github.com/OrcaSlicer/OrcaSlicer/releases/download/v$(ORCA_VERSION)/OrcaSlicer_Linux_AppImage_Ubuntu2404_V$(ORCA_VERSION).AppImage
ORCA_APPIMAGE = .tools/OrcaSlicer_$(ORCA_VERSION).AppImage
SLICER ?= $(abspath $(ORCA_APPIMAGE))

.PHONY: setup system-deps slicer cad check print pcb renders check-renders eu order stock order-push all clean
system-deps:    ## apt packages: KiCad 9, python venv, headless libs for OrcaSlicer (Ubuntu 24.04, sudo)
	tools/install-system-deps.sh

setup: slicer   ## python venv + requirements, OrcaSlicer AppImage
	python3 -m venv $(VENV) && $(VENV)/bin/pip install -r $(CAD)/requirements.txt

slicer: $(ORCA_APPIMAGE)

$(ORCA_APPIMAGE):
	mkdir -p $(dir $@)
	curl -fL --retry 3 -o $@.part $(ORCA_URL)
	echo "$(ORCA_SHA256)  $@.part" | sha256sum -c -
	chmod +x $@.part && mv $@.part $@

cad:            ## STEP/STL of insert + trim, print-oriented STLs (build/print), assembly, replacement back cover
	cd $(CAD) && $(PY) export.py && $(PY) assembly.py && $(PY) backcover.py

check:          ## geometry, barrier, wiring-board fit and printability checks, render inventory - must pass
	cd $(CAD) && $(PY) checks.py
	$(PY) cad/tools/check_renders.py

print: $(if $(filter $(abspath $(ORCA_APPIMAGE)),$(SLICER)),$(ORCA_APPIMAGE))  ## OrcaSlicer projects (print/*.3mf) + G-code (build/print/gcode)
	SLICER="$(SLICER)" $(PY) print/slice.py

pcb:            ## KiCad: wiring board (pcb/), ring board, riser, cover flex, EU cap board (pcb/sensor/), EU boards (pcb/eu/): ERC + DRC, fab packs
	pcb/tools/build.sh
	pcb/sensor/tools/build.sh
	pcb/eu/tools/build.sh

WB_PCB = pcb/kicad/wiring_board.kicad_pcb
RING_PCB = pcb/sensor/kicad/ring_board.kicad_pcb
EU_MB = pcb/eu/kicad/eu_mains_board.kicad_pcb
EU_LV = pcb/eu/kicad/eu_5v_board.kicad_pcb
RENDER_PCB = kicad-cli pcb render --quality high --width 1600 --height 1200

# Render groups: each stamp depends on the sources its renders are drawn from, so `make renders` redraws
# exactly the out-of-date groups and `make -q renders` (check-renders) reports any render older than its model.
STAMP = build/stamps
CAD_SRC = $(wildcard $(CAD)/*.py) cad/tools/sections.py
EU_SRC = $(CAD_SRC) $(wildcard $(CAD)/eu/*.py)
XVFB = $(if $(DISPLAY),,xvfb-run -a)
BARE = python3 pcb/tools/render_bare.py
BOARD_RENDERS = $(STAMP)/wiring_board $(STAMP)/ring_board $(STAMP)/riser_board \
                $(STAMP)/cover_flex $(STAMP)/eu_cap_board \
                $(STAMP)/eu_mains_board $(STAMP)/eu_5v_board
RENDER_STAMPS = $(STAMP)/sections $(STAMP)/views $(STAMP)/backcover $(STAMP)/eu $(BOARD_RENDERS)

renders: $(RENDER_STAMPS)  ## docs/renders/*.png, every group whose sources changed (3D needs xvfb-run headless)

check-renders: ## renders current (none older than its sources), every render used by a doc, every used one present
	@$(MAKE) -q renders || { echo "FAIL renders out of date: run make renders"; exit 1; }
	$(PY) cad/tools/check_renders.py

$(STAMP):
	mkdir -p $@

$(STAMP)/sections: $(CAD_SRC) $(WB_PCB) | $(STAMP)
	cd $(CAD) && $(PY) renders.py
	touch $@

$(STAMP)/views: $(CAD_SRC) $(WB_PCB) | $(STAMP)
	cd $(CAD) && $(XVFB) $(PY) render3d.py
	touch $@

$(STAMP)/backcover: $(EU_SRC) | $(STAMP)
	cd $(CAD) && $(XVFB) $(PY) render_backcover.py
	touch $@

$(STAMP)/eu: $(EU_SRC) $(EU_MB) $(EU_LV) | $(STAMP)
	cd $(CAD)/eu && $(XVFB) $(PY) render_eu.py
	touch $@

$(STAMP)/wiring_board: $(WB_PCB) pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/wiring_board_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/wiring_board_back.png $<
	$(RENDER_PCB) --side top --rotate "-40,0,30" -o docs/renders/wiring_board_iso_front.png $<
	$(RENDER_PCB) --side bottom --rotate "40,0,-30" -o docs/renders/wiring_board_iso_back.png $<
	$(BARE) $<
	touch $@

$(STAMP)/ring_board: $(RING_PCB) pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/ring_board_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/ring_board_back.png $<
	$(BARE) $< ring_board
	touch $@

$(STAMP)/riser_board $(STAMP)/cover_flex $(STAMP)/eu_cap_board: $(STAMP)/%: pcb/sensor/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/$*_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/$*_back.png $<
	$(BARE) $< $*
	touch $@

$(STAMP)/eu_mains_board $(STAMP)/eu_5v_board: $(STAMP)/%: pcb/eu/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/$*_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/$*_back.png $<
	$(BARE) $< $*
	touch $@

DEVKIT_SETS ?= 5
KICAD_PYTHON ?= python3
order:          ## DigiKey / Mouser lists (pcb/order/): one NA plate, one EU plate, a devkit of DEVKIT_SETS (5) of each; PCBWay devkit packs
	python3 pcb/tools/order_bom.py $(DEVKIT_SETS)
	$(KICAD_PYTHON) pcb/tools/order_pcbway.py $(DEVKIT_SETS)
	@if [ -n "$$DIGIKEY_CLIENT_ID$$MOUSER_SEARCH_KEY" ]; then python3 pcb/tools/distributors.py stock; \
	else echo "stock not checked: no DigiKey / Mouser keys in the environment (pcb/order/README.md)"; fi

PRIMARY ?= digikey
VARIANT ?= na
PLATES ?= 1
stock:          ## live DigiKey / Mouser stock and lifecycle of every listed part (build/stock.md); fails on the parts rule (D-84)
	python3 pcb/tools/distributors.py stock

order-push:     ## DigiKey myLists link + Mouser cart for PLATES plates (default 1) of VARIANT=na|eu|both, -plain (battery-free) or -switch (switch only) (default na); PRIMARY=digikey|mouser
	python3 pcb/tools/distributors.py push $(VARIANT) $(PLATES) --primary=$(PRIMARY)

eu:             ## EU variant (D-30, cad/build123d/eu/): STEP/STL to build/eu, checks, its renders (docs/renders/eu_*.png)
	cd $(CAD)/eu && $(PY) cap_eu.py && $(PY) trim_eu.py && $(PY) checks_eu.py
	$(MAKE) $(STAMP)/eu

all: pcb cad check print renders check-renders

clean:
	rm -rf build
