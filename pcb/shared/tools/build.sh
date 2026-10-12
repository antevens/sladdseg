#!/bin/bash
#
# Regenerate the board both variants share (docs/DESIGN.md D-35, D-50): the replacement back cover's flex
# (gen_lv.py shared); library, project, schematic and board, then run ERC and DRC and write the PCBWay fab files into
# pcb/shared/fab/cover_flex/. The fab files are withheld while its positions are REF / MEASURE.
#
# Usage: pcb/shared/tools/build.sh
# Environment: KICAD_PYTHON (python with pcbnew, default python3),
#              CAD_PYTHON (python with build123d, default .venv/bin/python; 3D models).

set -euo pipefail

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TOOLS
SHARED_DIR="$(dirname "${TOOLS}")"
readonly SHARED_DIR
REPO="$(cd "${SHARED_DIR}/../.." && pwd)"
readonly REPO
readonly PRJ="${SHARED_DIR}/kicad"
readonly FAB="${SHARED_DIR}/fab"
readonly OUT="${REPO}/build"
readonly BOARD="cover_flex"
readonly LAYERS="F.Cu,F.Mask,F.Paste,F.Silkscreen,Edge.Cuts,User.1"

function err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

function kicad_python() {
  echo "${KICAD_PYTHON:-python3}"
}

function lv_value() {
  "$(kicad_python)" -c "import sys; sys.path[0:0] = ['${TOOLS}', '${REPO}/pcb/tools']; import lv_parts as p; $1"
}

function check() {
  local status=0

  mkdir -p "${OUT}"
  kicad-cli sch erc --severity-all --exit-code-violations \
    -o "${OUT}/${BOARD}_erc.rpt" "${PRJ}/${BOARD}.kicad_sch" 2>/dev/null || status=1
  kicad-cli pcb drc --severity-all --schematic-parity --exit-code-violations \
    -o "${OUT}/${BOARD}_drc.rpt" "${PRJ}/${BOARD}.kicad_pcb" 2>/dev/null || status=1
  echo "${BOARD}:"
  grep -h "^ \?\*\* \(Found\|ERC messages\)" "${OUT}/${BOARD}_erc.rpt" "${OUT}/${BOARD}_drc.rpt" || true
  return "${status}"
}

function export_gerbers() {
  local dir="${FAB}/${BOARD}"
  local rev

  rev="$(lv_value "print(p.REV)")"
  rm -rf "${dir}"
  mkdir -p "${dir}/gerbers"
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin --layers "${LAYERS}" \
    --subtract-soldermask --no-x2 "${PRJ}/${BOARD}.kicad_pcb" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${PRJ}/${BOARD}.kicad_pcb" >/dev/null
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${BOARD}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pdf -o "${dir}/${BOARD}_${rev}_fab.pdf" --mode-single \
    --layers "${LAYERS},Cmts.User" --include-border-title "${PRJ}/${BOARD}.kicad_pcb" >/dev/null
  cp "${OUT}/${BOARD}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${BOARD}_drc.rpt" "${dir}/drc.rpt"
  echo "fab files in ${dir}"
}

function main() {
  "${CAD_PYTHON:-${REPO}/.venv/bin/python}" "${REPO}/pcb/tools/gen_3d.py"
  "$(kicad_python)" "${TOOLS}/gen_lv.py" shared
  if ! check; then
    err "ERC or DRC reported violations; see ${OUT}/${BOARD}_erc.rpt and ${BOARD}_drc.rpt"
    exit 1
  fi
  if lv_value "sys.exit(0 if p.COVER_CONFIRMED else 1)"; then
    export_gerbers
  else
    rm -rf "${FAB}/${BOARD}"
    err "${BOARD}: positions are REF / MEASURE (lv_parts.COVER_CONFIRMED); no fab files written"
  fi
}

main "$@"
