#!/usr/bin/env bash
# Цикл: ганяє `claude -p`, поки `python3 -m unittest` не зелений. Лог — loop.log.
# Стоп: зелено · MAX ітерацій · агент змінив test_tt.py (правило AGENTS.md).
set -u
cd "$(dirname "$0")"
MAX=${MAX:-5}
LOG=loop.log
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

: > "$LOG"
i=0
until out=$(python3 -m unittest 2>&1); do
  i=$((i + 1))
  if [ "$i" -gt "$MAX" ]; then log "STOP: $MAX ітерацій, досі червоно"; exit 1; fi
  log "iter $i: RED — $(echo "$out" | tail -1)"

  # промпт — через stdin: --allowedTools варіадичний і ковтає позиційний аргумент
  if ! printf 'Тести червоні. Дотримуйся AGENTS.md і spec.md. Зроби тести зеленими, змінюючи лише tt.py.\nВивід python3 -m unittest:\n%s\n' \
      "$(echo "$out" | tail -40)" \
      | claude -p --allowedTools "Read,Edit,Write,Bash(python3 -m unittest:*)" >> "$LOG" 2>&1; then
    log "STOP: claude завершився з помилкою — див. вище"; exit 1
  fi

  if ! git diff --quiet -- test_tt.py; then log "STOP: агент змінив test_tt.py — потрібна людина"; exit 1; fi
done
log "GREEN після $i ітерацій агента — $(echo "$out" | tail -1)"
