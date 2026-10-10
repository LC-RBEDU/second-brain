#!/usr/bin/env bash
set -u
S="scripts/md_fingerprint.py"; F="scripts/fixtures"; T="$(mktemp -d)"
run() {
  desc="$1"; want="$2"; shift 2
  "$@" 2>/dev/null; got=$?
  [ "$got" = "$want" ] && echo "OK    $desc (exit $got)" || echo "FAIL  $desc (čekáno $want, je $got)"
}
run "capture valid-full"               0 python3 $S capture --md $F/valid-full.md --out $T/fp.json
run "compare identický"                0 python3 $S compare --before $T/fp.json --md $F/valid-full.md
run "capture broken-highlights"        2 python3 $S capture --md $F/broken-highlights.md --out $T/fp2.json
sed 's/tisíc Kč\./tisíc korun./' $F/valid-full.md > $T/ok.md
run "jazyková úprava uvnitř odrážky"   0 python3 $S compare --before $T/fp.json --md $T/ok.md
grep -v "Termín je konec října" $F/valid-full.md > $T/bullet.md
run "smazaná odrážka Co zaznělo"       1 python3 $S compare --before $T/fp.json --md $T/bullet.md
sed 's/\*\*owner:\*\* Lukáš Cypra/**owner:** Lukas Cypra/' $F/valid-full.md > $T/owner.md
run "změněný owner"                    1 python3 $S compare --before $T/fp.json --md $T/owner.md
sed 's/^variant: full/varianta: full/' $F/valid-full.md > $T/yaml.md
run "přejmenovaný YAML klíč"           1 python3 $S compare --before $T/fp.json --md $T/yaml.md
sed 's/strop 100 tisíc/strop 1000 tisíc/' $F/valid-full.md > $T/num.md
run "změněné číslo (známá limitace)"   0 python3 $S compare --before $T/fp.json --md $T/num.md
