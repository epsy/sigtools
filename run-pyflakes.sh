#!/bin/sh

PAT=$(grep -Hrn --binary-files=without-match 'pyflakes: silence' $1 |
    sed -e ':a' -e 'N' -e '$!ba' -e 's/\([^:]*:[^:]*:\)[^\n]*\n\?/\1|/g' -e 's/.$//')

if [ -n "$PAT" ]
then
    OUT=$(python3.5 -m pyflakes $1 | grep -Pv "$PAT")
    if [ -n "$OUT" ]; then
        echo $OUT; false
    else
        true
    fi
else
    python3.5 -m pyflakes $1
fi
