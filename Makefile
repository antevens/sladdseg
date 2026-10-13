VENV ?= .venv
PY ?= $(abspath $(VENV))/bin/python
CAD = cad/build123d

# ElegooSlicer (OrcaSlicer fork): pinned Linux AppImage, fetched + verified by `make slicer`; its projects open in
# ElegooSlicer without the compatibility warning. Override with SLICER=/path/to/<OrcaSlicer fork>.AppImage.
SLICER_VERSION ?= 1.5.3.5
SLICER_SHA256 ?= 7b3b3f08e0d0d51bb472c85865d1be9b0c28385423daba1cb0c3b225d0101afc
SLICER_URL = https://github.com/elegooofficial/ElegooSlicer/releases/download/v$(SLICER_VERSION)/ElegooSlicer_Linux_V$(SLICER_VERSION).AppImage
SLICER_APPIMAGE = .tools/ElegooSlicer_$(SLICER_VERSION).AppImage
SLICER ?= $(abspath $(SLICER_APPIMAGE))

.PHONY: setup system-deps slicer cad check print pcb renders check-renders na eu order stock order-push all clean
system-deps:    ## apt packages: KiCad 9, python venv, headless libs for the slicer (Ubuntu 24.04, sudo)
	tools/install-system-deps.sh

setup: slicer   ## python venv + requirements, ElegooSlicer AppImage
	python3 -m venv $(VENV) && $(VENV)/bin/pip install -r $(CAD)/requirements.txt

slicer: $(SLICER_APPIMAGE)

$(SLICER_APPIMAGE):
	mkdir -p $(dir $@)
	curl -fL --retry 3 -o $@.part $(SLICER_URL)
	echo "$(SLICER_SHA256)  $@.part" | sha256sum -c -
	chmod +x $@.part && mv $@.part $@

cad:            ## STEP/STL of every printed part, print-oriented STLs (build/print), the NA assembly, the back cover
	cd $(CAD) && $(PY) export.py && $(PY) backcover.py
	cd $(CAD)/na && $(PY) assembly_na.py

check:          ## shared parts, NA and EU: geometry, barrier, board fit, printability; render inventory - must pass
	cd $(CAD) && $(PY) checks.py
	cd $(CAD)/na && $(PY) checks_na.py
	cd $(CAD)/eu && $(PY) checks_eu.py
	$(PY) cad/tools/check_renders.py

print: $(if $(filter $(abspath $(SLICER_APPIMAGE)),$(SLICER)),$(SLICER_APPIMAGE))  ## ElegooSlicer projects (print/*.3mf) + G-code (build/print/gcode)
	SLICER="$(SLICER)" $(PY) print/slice.py

pcb:            ## KiCad, NA (pcb/na/), EU (pcb/eu/) and shared (pcb/shared/) boards: ERC + DRC, fab packs
	pcb/na/tools/build.sh
	pcb/eu/tools/build.sh
	pcb/shared/tools/build.sh

NA_MB = pcb/na/kicad/na_mains_board.kicad_pcb
EU_MB = pcb/eu/kicad/eu_mains_board.kicad_pcb
EU_PB = pcb/eu/kicad/eu_pin_board.kicad_pcb
RENDER_PCB = kicad-cli pcb render --quality high --width 1600 --height 1200

# Render groups: each stamp depends on the sources its renders are drawn from, so `make renders` redraws
# exactly the out-of-date groups and `make -q renders` (check-renders) reports any render older than its model.
STAMP = build/stamps
SHARED_SRC = $(wildcard $(CAD)/*.py) cad/tools/sections.py
NA_SRC = $(SHARED_SRC) $(wildcard $(CAD)/na/*.py)
EU_SRC = $(SHARED_SRC) $(wildcard $(CAD)/eu/*.py)
XVFB = $(if $(DISPLAY),,xvfb-run -a)
BARE = python3 pcb/tools/render_bare.py
NA_BOARDS = na_mains_board na_sensor_board na_pin_board
EU_BOARDS = eu_mains_board eu_pin_board eu_sensor_board
SHARED_BOARDS = cover_flex
BOARD_RENDERS = $(addprefix $(STAMP)/,$(NA_BOARDS) $(EU_BOARDS) $(SHARED_BOARDS))
RENDER_STAMPS = $(STAMP)/na_sections $(STAMP)/na_views $(STAMP)/eu_views $(STAMP)/shared_views $(BOARD_RENDERS)

renders: $(RENDER_STAMPS)  ## docs/renders/*.png, every group whose sources changed (3D needs xvfb-run headless)

check-renders: ## renders current (none older than its sources), every render used by a doc, every used one present
	@$(MAKE) -q renders || { echo "FAIL renders out of date: run make renders"; exit 1; }
	$(PY) cad/tools/check_renders.py

$(STAMP):
	mkdir -p $@

$(STAMP)/na_sections: $(NA_SRC) $(NA_MB) | $(STAMP)
	cd $(CAD)/na && $(PY) sections_na.py
	touch $@

$(STAMP)/na_views: $(NA_SRC) $(NA_MB) | $(STAMP)
	cd $(CAD)/na && $(XVFB) $(PY) render_na.py
	touch $@

$(STAMP)/shared_views: $(NA_SRC) $(EU_SRC) | $(STAMP)
	cd $(CAD) && $(XVFB) $(PY) render_shared.py
	touch $@

$(STAMP)/eu_views: $(EU_SRC) $(EU_MB) $(EU_PB) | $(STAMP)
	cd $(CAD)/eu && $(XVFB) $(PY) render_eu.py
	touch $@

$(STAMP)/na_mains_board: $(NA_MB) pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/na_mains_board_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/na_mains_board_back.png $<
	$(RENDER_PCB) --side top --rotate "-40,0,30" -o docs/renders/na_mains_board_iso_front.png $<
	$(RENDER_PCB) --side bottom --rotate "40,0,-30" -o docs/renders/na_mains_board_iso_back.png $<
	$(BARE) $< na_mains_board
	touch $@

$(addprefix $(STAMP)/,$(filter-out na_mains_board,$(NA_BOARDS))): $(STAMP)/%: pcb/na/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/$*_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/$*_back.png $<
	$(BARE) $< $*
	touch $@

$(addprefix $(STAMP)/,$(EU_BOARDS)): $(STAMP)/%: pcb/eu/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
	$(RENDER_PCB) --side top -o docs/renders/$*_front.png $<
	$(RENDER_PCB) --side bottom -o docs/renders/$*_back.png $<
	$(BARE) $< $*
	touch $@

$(addprefix $(STAMP)/,$(SHARED_BOARDS)): $(STAMP)/%: pcb/shared/kicad/%.kicad_pcb pcb/tools/render_bare.py | $(STAMP)
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

na:             ## NA variant (cad/build123d/na/): STEP/STL to build/na, checks, its renders (docs/renders/na_*.png)
	cd $(CAD)/na && $(PY) barrier_na.py && $(PY) face_plate_na.py && $(PY) checks_na.py
	$(MAKE) $(STAMP)/na_sections $(STAMP)/na_views

eu:             ## EU variant (cad/build123d/eu/): STEP/STL to build/eu, checks, its renders (docs/renders/eu_*.png)
	cd $(CAD)/eu && $(PY) barrier_eu.py && $(PY) face_plate_eu.py && $(PY) checks_eu.py
	$(MAKE) $(STAMP)/eu_views

all: pcb cad check print renders check-renders

clean:
	rm -rf build
