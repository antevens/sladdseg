#!/bin/bash
#
# Regenerate the NA boards: the mains board (3D models, libraries, project, schematic, board), the sensor board and
# the pin board (pcb/shared/tools/gen_lv.py na); run ERC and DRC on each, export the mains board's STEP model and
# write the PCBWay packs into pcb/na/fab/<board>/. The sensor board's fab files are withheld while the CN2 mate and
# contact map are placeholders.
#
# Usage: pcb/na/tools/build.sh
# Environment: CAD_PYTHON (python with build123d, default .venv/bin/python),
#              KICAD_PYTHON (python with pcbnew, default python3).

set -euo pipefail

TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TOOLS
VARIANT_DIR="$(dirname "${TOOLS}")"
readonly VARIANT_DIR
REPO="$(cd "${VARIANT_DIR}/../.." && pwd)"
readonly REPO
readonly PRJ="${VARIANT_DIR}/kicad"
readonly FAB="${VARIANT_DIR}/fab"
readonly OUT="${REPO}/build"
readonly MAINS="na_mains_board"
readonly BOARDS=(na_mains_board na_sensor_board na_pin_board)
readonly LAYERS="F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts"

function err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')]: $*" >&2
}

function kicad_python() {
  echo "${KICAD_PYTHON:-python3}"
}

function generate() {
  local script

  "${CAD_PYTHON:-${REPO}/.venv/bin/python}" "${REPO}/pcb/tools/gen_3d.py"
  for script in gen_libs_na gen_project_na gen_schematic_na gen_pcb_na; do
    "$(kicad_python)" "${TOOLS}/${script}.py"
  done
  "$(kicad_python)" "${REPO}/pcb/shared/tools/gen_lv.py" na
}

function check() {
  local status=0
  local board

  mkdir -p "${OUT}"
  # creepage geometry asserts flood stderr; the reports carry the results
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

function export_step() {
  mkdir -p "${OUT}"
  kicad-cli pcb export step --subst-models -f -o "${OUT}/${MAINS}.step" \
    "${PRJ}/${MAINS}.kicad_pcb" >/dev/null 2>&1
}

function rev_of() {
  local module="$1"
  local dir="$2"

  "$(kicad_python)" -c "import sys; sys.path[0:0] = ['${dir}', '${REPO}/pcb/tools', '${REPO}/pcb/shared/tools']; \
import ${module} as m; print(m.REV)"
}

function export_mains() {
  local pcb="${PRJ}/${MAINS}.kicad_pcb"
  local dir="${FAB}/${MAINS}"
  local rev

  rev="$(rev_of parts_na "${TOOLS}")"
  rm -rf "${dir}/gerbers"
  mkdir -p "${dir}/gerbers"
  # board-centre (aux) origin for Gerbers, drill and centroid alike
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin --layers "${LAYERS}" \
    --subtract-soldermask --no-x2 "${pcb}" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${pcb}" >/dev/null
  rm -f "${dir}/${MAINS}"_*_gerbers.zip
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${MAINS}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pos -o "${OUT}/${MAINS}_pos.csv" --format csv --units mm \
    --side both --use-drill-file-origin "${pcb}" >/dev/null
  "$(kicad_python)" "${TOOLS}/gen_fab_na.py" "${OUT}/${MAINS}_pos.csv"
  kicad-cli pcb export pdf -o "${dir}/${MAINS}_${rev}_assembly_front.pdf" --mode-single \
    --layers F.Fab,F.Silkscreen,F.Courtyard,Edge.Cuts --include-border-title "${pcb}" >/dev/null
  kicad-cli pcb export pdf -o "${dir}/${MAINS}_${rev}_assembly_back.pdf" --mode-single \
    --mirror --layers B.Fab,B.Silkscreen,B.Courtyard,Edge.Cuts --include-border-title \
    "${pcb}" >/dev/null
  kicad-cli sch export pdf -o "${dir}/${MAINS}_${rev}_schematic.pdf" \
    "${PRJ}/${MAINS}.kicad_sch" >/dev/null
  cp "${OUT}/${MAINS}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${MAINS}_drc.rpt" "${dir}/drc.rpt"
  echo "fab pack in ${dir}"
}

function export_gerbers() {
  local board="$1"
  local dir="${FAB}/${board}"
  local rev

  rev="$(rev_of lv_parts "${REPO}/pcb/shared/tools")"
  rm -rf "${dir}"
  mkdir -p "${dir}/gerbers"
  kicad-cli pcb export gerbers -o "${dir}/gerbers/" --use-drill-file-origin --layers "${LAYERS}" \
    --subtract-soldermask --no-x2 "${PRJ}/${board}.kicad_pcb" >/dev/null
  kicad-cli pcb export drill -o "${dir}/gerbers/" --format excellon --drill-origin plot \
    --excellon-units mm --excellon-separate-th --generate-map --map-format gerberx2 \
    "${PRJ}/${board}.kicad_pcb" >/dev/null
  (cd "${dir}/gerbers" && zip -q -j "${dir}/${board}_${rev}_gerbers.zip" ./*)
  kicad-cli pcb export pdf -o "${dir}/${board}_${rev}_fab.pdf" --mode-single \
    --layers "${LAYERS},Cmts.User,User.1" --include-border-title "${PRJ}/${board}.kicad_pcb" >/dev/null
  cp "${OUT}/${board}_erc.rpt" "${dir}/erc.rpt"
  cp "${OUT}/${board}_drc.rpt" "${dir}/drc.rpt"
  echo "fab files in ${dir}"
}

function cn2_confirmed() {
  "$(kicad_python)" -c "import sys; sys.path[0:0] = ['${REPO}/pcb/shared/tools', '${REPO}/pcb/tools']; \
import lv_parts as p; sys.exit(0 if p.CN2_CONFIRMED else 1)"
}

function main() {
  generate
  if ! check; then
    err "ERC or DRC reported violations; see ${OUT}/na_*_erc.rpt and na_*_drc.rpt"
    exit 1
  fi
  export_step
  export_mains
  export_gerbers na_pin_board
  if cn2_confirmed; then
    export_gerbers na_sensor_board
  else
    rm -rf "${FAB}/na_sensor_board"
    err "na_sensor_board: CN2 mate and contact map are placeholders (lv_parts.CN2_CONFIRMED); no fab files written"
  fi
}

main "$@"
