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

.PHONY: setup system-deps slicer cad check print pcb renders check-renders eu order all clean
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

pcb:            ## KiCad: wiring board (pcb/), ring board, mic carrier, riser, cover flex, EU flex (pcb/sensor/), EU boards (pcb/eu/): ERC + DRC, fab packs
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
BOARD_RENDERS = $(STAMP)/wiring_board $(STAMP)/ring_board $(STAMP)/mic_carrier $(STAMP)/riser_board \
                $(STAMP)/cover_flex $(STAMP)/eu_cap_board \
                $(STAMP)/eu_mains_board $(STAMP)/eu_5v_board
RENDER_STAMPS = $(STAMP)/sections $(STAMP)/views $(STAMP)/backcover $(STAMP)/tape $(STAMP)/eu $(BOARD_RENDERS)

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

$(STAMP)/tape: $(EU_SRC) | $(STAMP)
	cd $(CAD) && $(XVFB) $(PY) render_tape.py
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
	$(BARE) $< ring_board --copper-only
	touch $@

$(STAMP)/mic_carrier $(STAMP)/riser_board $(STAMP)/cover_flex $(STAMP)/eu_cap_board: $(STAMP)/%: pcb/sensor/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(BARE) $< $* --copper-only
	touch $@

$(STAMP)/eu_mains_board $(STAMP)/eu_5v_board: $(STAMP)/%: pcb/eu/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/$*_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/$*_back.png $<
	$(BARE) $< $* --copper-only
	touch $@

NA_PLATES ?= 3
EU_PLATES ?= 2
order:          ## DigiKey / Mouser order lists for hand-soldered test plates (pcb/order/), NA_PLATES / EU_PLATES
	python3 pcb/tools/order_bom.py $(NA_PLATES) $(EU_PLATES)

eu:             ## EU variant (D-30, cad/build123d/eu/): STEP/STL to build/eu, checks, its renders (docs/renders/eu_*.png)
	cd $(CAD)/eu && $(PY) cap_eu.py && $(PY) trim_eu.py && $(PY) checks_eu.py
	$(MAKE) $(STAMP)/eu

all: pcb cad check print renders check-renders

clean:
	rm -rf build
