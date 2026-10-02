# tt — тайм-трекер у терміналі

Capstone · fwdays Crash Course: Agentic Engineering · Василь Дмитрук

Один файл на Python (stdlib), щоб фіксувати, над чим працюю, і бачити звіт за день. Дані — один JSON.

```
$ tt start write spec      ▶ started: write spec
$ tt start other           error: already running: write spec   (exit 1)
$ tt stop                  ■ stopped: write spec (25m)
$ tt report                write spec  25m
                           total  25m
```

## Запуск і перевірка

```bash
cd submissions/vasyl-dmytruk
python3 -m unittest -v          # 18 тестів, без залежностей
python3 tt.py start docs        # дані в $TT_FILE або ~/.tt.json
./loop.sh                       # цикл: claude -p, поки тести не зелені
```

## Що де лежить

| Файл | Навіщо |
|---|---|
| [spec.md](spec.md) | специфікація до коду + розділ «Зміни специфікації» (3 зміни) |
| [AGENTS.md](AGENTS.md) / [CLAUDE.md](CLAUDE.md) | правила для агента |
| [test_tt.py](test_tt.py) / [tt.py](tt.py) | тести / код |
| [loop.sh](loop.sh) + `loop-run*.log` | цикл і логи всіх 5 прогонів, зокрема двох провальних |
| [.claude/agents/reviewer.md](.claude/agents/reviewer.md) + [review.md](review.md) | агент-рецензент і його звіт |
| [autonomy-log.md](autonomy-log.md) | журнал рівнів довіри, який вівся під час роботи |

## Історія — порядок комітів і є доказ

| Коміт | Що |
|---|---|
| `4fdc64a` | spec — до будь-якого коду |
| `426f86c` | AGENTS.md / CLAUDE.md |
| `b06e461` | spec змінено: дві дірки, знайдені під час написання тестів |
| `c960856` | 🔴 14 тестів, `tt.py` ще не існує |
| `38719de` | 🟢 `tt.py` від агента в `loop.sh` (після двох провалів самого циклу) |
| `59d554f` | 🔴 `--date 20261002` — дірка, яку агент знайшов і не закрив сам |
| `4f7f63f` | 🟢 агент позеленив |
| `40451a4` | рев'ю окремим агентом: 5 знахідок при зелених тестах |
| `09ad69b` | 🔴 мої рішення по рев'ю → spec + 4 тести |
| `aa39ce6` | 🟢 атомарний запис, перевірка структури, OSError, `0m` |
