#!/bin/bash
#
# Regenerate the low-voltage boards (docs/DESIGN.md D-50, D-56, D-70): ring board, riser board, back cover flex
# and the EU cap board: libraries, projects, schematics and boards, then run ERC and DRC on each and
# write the PCBWay fab files. The ring board's and the EU cap board's fab files are withheld while the CN2 mate and
# contact map are placeholders; the cover flex's while its positions are REF / MEASURE.
#
# Usage: pcb/sensor/tools/build.sh
# Environment: KICAD_PYTHON (python with pcbnew, default python3),
#              CAD_PYTHON (python with build123d, default .venv/bin/python; 3D models).

set -euo pipefail

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TOOLS
SENSOR_DIR="$(dirname "${TOOLS}")"
readonly SENSOR_DIR
REPO="$(cd "${SENSOR_DIR}/../.." && pwd)"
readonly REPO
readonly PRJ="${SENSOR_DIR}/kicad"
readonly FAB="${SENSOR_DIR}/fab"
readonly OUT="${REPO}/build"
readonly BOARDS=(ring_board riser_board cover_flex eu_cap_board)

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

function cn2_confirmed() {
  "$(kicad_python)" -c "import sys; sys.path.insert(0, '${TOOLS}'); import sensor_parts as p; \
sys.exit(0 if p.CN2_CONFIRMED else 1)"
}

function cover_confirmed() {
  "$(kicad_python)" -c "import sys; sys.path.insert(0, '${TOOLS}'); import sensor_parts as p; \
sys.exit(0 if p.COVER_CONFIRMED else 1)"
}

function export_gerbers() {
  local board="$1"
  local layers="$2"
  local dir="${FAB}/${board}"
  local rev

  rev="$("$(kicad_python)" -c "import sys; sys.path.insert(0, '${TOOLS}'); import sensor_parts as p; print(p.REV)")"
  rm -rf "${dir}"
  mkdir -p "${dir}/gerbers"
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin --layers "${layers}" \
    --subtract-soldermask --no-x2 "${PRJ}/${board}.kicad_pcb" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${PRJ}/${board}.kicad_pcb" >/dev/null
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${board}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pdf -o "${dir}/${board}_${rev}_fab.pdf" --mode-single \
    --layers "${layers},Cmts.User,User.1" --include-border-title "${PRJ}/${board}.kicad_pcb" >/dev/null
  cp "${OUT}/${board}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${board}_drc.rpt" "${dir}/drc.rpt"
  echo "fab files in ${dir}"
}

function main() {
  "${CAD_PYTHON:-${REPO}/.venv/bin/python}" "${REPO}/pcb/tools/gen_3d.py"
  "$(kicad_python)" "${TOOLS}/gen_sensor.py"
  if ! check; then
    err "ERC or DRC reported violations; see ${OUT}/<board>_erc.rpt and <board>_drc.rpt"
    exit 1
  fi
  export_gerbers riser_board "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  if cover_confirmed; then
    export_gerbers cover_flex "F.Cu,F.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  else
    rm -rf "${FAB}/cover_flex"
    err "cover_flex: positions are REF / MEASURE (sensor_parts.COVER_CONFIRMED); no fab files written"
  fi
  if cn2_confirmed; then
    export_gerbers ring_board "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
    export_gerbers eu_cap_board "F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"
  else
    rm -rf "${FAB}/ring_board" "${FAB}/eu_cap_board"
    err "ring_board, eu_cap_board: CN2 mate and contact map are placeholders (sensor_parts.CN2_CONFIRMED);" \
      "no fab files written"
  fi
}

main "$@"
