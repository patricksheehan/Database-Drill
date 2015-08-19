comm -3 <(cd Sautinsoft_created && for x in *; do printf '%s\n' "${x%.*}"; done | sort) \
 <(cd PDFs_converted/Sautinsoft_converted && for x in *; do printf '%s\n' "${x%.*}"; done | sort)
