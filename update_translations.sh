#!/bin/bash

# Originally from the Cine Video Player by diegopvlk

OUTPUT="po/Exhibit.pot"
PACKAGE_NAME="Exhibit"
ENCODING="UTF-8"
LANGUAGE_BLP="--language=JavaScript"
LINGUAS_FILE="po/LINGUAS"

grep -v '\.blp$' po/POTFILES > /tmp/TEMP_POTFILES
grep '\.blp$' po/POTFILES > /tmp/TEMP_POTFILES.blp

# Creates pot
xgettext --files-from=/tmp/TEMP_POTFILES \
       	 --output="$OUTPUT" --package-name="$PACKAGE_NAME" \
       	 --from-code="$ENCODING" --add-comments \
       	 --keyword=_ --keyword=C_:1c,2

# Joins pot
xgettext --files-from=/tmp/TEMP_POTFILES.blp \
    	 --output="$OUTPUT" --package-name="$PACKAGE_NAME" \
    	 --from-code="$ENCODING" --add-comments \
    	 --keyword=_ --keyword=C_:1c,2 \
    	 $LANGUAGE_BLP \
    	 --join-existing


rm /tmp/TEMP_POTFILES /tmp/TEMP_POTFILES.blp

sed -i 's/charset=CHARSET/charset=UTF-8/g' $OUTPUT

grep -v '^#' "$LINGUAS_FILE" | while read -r lang_file; do
    msgmerge --previous --backup=none --update "po/${lang_file}.po" "$OUTPUT" \
    || echo "Error with : $lang_file" >&2
done
