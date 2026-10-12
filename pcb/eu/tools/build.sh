#!/bin/bash
#
# Regenerate the EU boards (docs/DESIGN.md D-30, D-36): the mains board and the pin board (gen_eu.py) and the sensor
# board (pcb/shared/tools/gen_lv.py eu); libraries, projects, schematics and boards, then run ERC and DRC (all
# severities, schematic parity) and write the mains and pin boards' PCBWay packs into pcb/eu/fab/<board>/ (review
# pcb/eu/fab/README.md before ordering). The sensor board's fab files are withheld while the CN2 mate and contact map
# are placeholders.
#
# Usage: pcb/eu/tools/build.sh
# Environment: KICAD_PYTHON (python with pcbnew, default python3),
#              CAD_PYTHON (python with build123d, default .venv/bin/python; 3D models).

set -euo pipefail

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TOOLS
EU_DIR="$(dirname "${TOOLS}")"
readonly EU_DIR
REPO="$(cd "${EU_DIR}/../.." && pwd)"
readonly REPO
readonly PRJ="${EU_DIR}/kicad"
readonly OUT="${REPO}/build"
readonly FAB="${EU_DIR}/fab"
readonly BOARDS=(eu_mains_board eu_pin_board eu_sensor_board)
readonly FAB_BOARDS=(eu_mains_board eu_pin_board)

function err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

function kicad_python() {
  echo "${KICAD_PYTHON:-python3}"
}

function check() {
  local status=0
  local board

  mkdir -p "${OUT}"
  for board in "${BOARDS[@]}"; do
    kicad-cli sch erc --severity-all --exit-code-violations \
      -o "${OUT}/${board}_erc.rpt" "${PRJ}/${board}.kicad_sch" 2>/dev/null || status=1
    kicad-cli pcb drc --severity-all --schematic-parity --exit-code-violations \
      -o "${OUT}/${board}_drc.rpt" "${PRJ}/${board}.kicad_pcb" 2>/dev/null || status=1
    echo "${board}:"
    grep -h "^ \?\*\* \(Found\|ERC messages\)" "${OUT}/${board}_erc.rpt" "${OUT}/${board}_drc.rpt" || true
  done
  return "${status}"
}

function export_fab() {
  local board="$1"
  local pcb="${PRJ}/${board}.kicad_pcb"
  local dir="${FAB}/${board}"
  local rev

  rev="$("$(kicad_python)" -c "import sys; sys.path.insert(0, '${TOOLS}'); import parts_eu; print(parts_eu.REV)")"
  rm -rf "${dir}"
  mkdir -p "${dir}/gerbers"
  # board-centre (aux) origin for Gerbers, drill and centroid alike
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin \
    --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts \
    --subtract-soldermask --no-x2 "${pcb}" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${pcb}" >/dev/null
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${board}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pos -o "${OUT}/${board}_pos.csv" --format csv --units mm \
    --side both --use-drill-file-origin "${pcb}" >/dev/null
  "$(kicad_python)" "${TOOLS}/gen_fab_eu.py" "${board}" "${OUT}/${board}_pos.csv"
  kicad-cli pcb export pdf -o "${dir}/${board}_${rev}_assembly_front.pdf" --mode-single \
    --layers F.Fab,F.Silkscreen,F.Courtyard,Edge.Cuts --include-border-title "${pcb}" >/dev/null
  kicad-cli pcb export pdf -o "${dir}/${board}_${rev}_assembly_back.pdf" --mode-single \
    --mirror --layers B.Fab,B.Silkscreen,B.Courtyard,Edge.Cuts --include-border-title \
    "${pcb}" >/dev/null
  kicad-cli sch export pdf -o "${dir}/${board}_${rev}_schematic.pdf" \
    "${PRJ}/${board}.kicad_sch" >/dev/null
  cp "${OUT}/${board}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${board}_drc.rpt" "${dir}/drc.rpt"
  echo "fab pack in ${dir}"
}

function rev_of() {
  local module="$1"
  local dir="$2"

  "$(kicad_python)" -c "import sys; sys.path[0:0] = ['${dir}', '${REPO}/pcb/tools', '${REPO}/pcb/shared/tools']; \
import ${module} as m; print(m.REV)"
}

function export_gerbers() {
  local board="$1"
  local dir="${FAB}/${board}"
  local lv_layers="F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  local rev

  rev="$(rev_of lv_parts "${REPO}/pcb/shared/tools")"
  rm -rf "${dir}"
  mkdir -p "${dir}/gerbers"
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin --layers "${lv_layers}" \
    --subtract-soldermask --no-x2 "${PRJ}/${board}.kicad_pcb" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${PRJ}/${board}.kicad_pcb" >/dev/null
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${board}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pdf -o "${dir}/${board}_${rev}_fab.pdf" --mode-single \
    --layers "${lv_layers},Cmts.User,User.1" --include-border-title "${PRJ}/${board}.kicad_pcb" >/dev/null
  cp "${OUT}/${board}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${board}_drc.rpt" "${dir}/drc.rpt"
  echo "fab files in ${dir}"
}

function main() {
  local board

  "${CAD_PYTHON:-${REPO}/.venv/bin/python}" "${REPO}/pcb/tools/gen_3d.py"
  "$(kicad_python)" "${TOOLS}/gen_eu.py"
  "$(kicad_python)" "${REPO}/pcb/shared/tools/gen_lv.py" eu
  if ! check; then
    err "ERC or DRC reported violations; see ${OUT}/eu_*_erc.rpt and eu_*_drc.rpt"
    exit 1
  fi
  for board in "${FAB_BOARDS[@]}"; do
    export_fab "${board}"
  done
  if "$(kicad_python)" -c "import sys; sys.path[0:0] = ['${REPO}/pcb/shared/tools', '${REPO}/pcb/tools']; \
import lv_parts as p; sys.exit(0 if p.CN2_CONFIRMED else 1)"; then
    export_gerbers eu_sensor_board
  else
    rm -rf "${FAB}/eu_sensor_board"
    err "eu_sensor_board: CN2 mate and contact map are placeholders (lv_parts.CN2_CONFIRMED); no fab files written"
  fi
}

main "$@"
