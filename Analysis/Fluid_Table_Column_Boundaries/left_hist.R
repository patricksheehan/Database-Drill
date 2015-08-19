# Author: Patrick Sheehan
# Purpose: Prove or disprove that the boundaries of columns in the Frac Focus
#          Fluid tables do not overlap for any files
# Input: "left.txt" which is a file containing all of the left alignments of the
#        cells in all of the fluid tables
# Output(s): Histogram and counts for each of the intervals which shows mostly
#            seperate columns with some discrepencies which will need to be
#            handled specially

left.data <- read.table("left.txt", header=FALSE)$V1
pdf("Suspected_column_boundaries.pdf")
opar=par(ps=8)
left.hist <- hist(left.data,
                  main="Histogram of fluid data left alignment",
                  xlab="Left alignment",
                  breaks=c(0,20,        # Non-cell
                           60,80,       # Trade name
                           180,200,     # Supplier
                           305,325,     # Purpose
                           430,450,     # Ingredient
                           530,550,     # ?
                           610,630,     # CAS
                           775,805,     # Concentration in additive
                           880,905,     # Concentration in HF fluid / Comments
                           930,950),    # Comments   
                  labels=c("N/A","",
                           "Trade Name","",
                           "Supplier","",
                           "Purpose","",
                           "Ingredient","",
                           "?","",
                           "CAS#","",
                           "Concentration 1","",
                           "Concentration 2","",
                           "Comments"),
                  col="gray",
                  freq=FALSE)
opar
dev.off()
print(left.hist$counts)
