# Author: Patrick Sheehan
# Purpose: Figure out a safe height value to determine where the tables have split
# Input: "table_separation.txt" which has values for where a string which
#        divides the two tables in each PDF is located
# Output(s): Histogram and counts of the "top" value for where the string
#             "Hydraulic Fracturing Fluid Composition:" appears in each file

separation.data <- read.table("table_separation.txt", header=FALSE)$V1
pdf("Histogram_of_Separation_Heights.pdf")
opar=par(ps=8)
separation.hist <- hist(separation.data,
                  main="Histogramm of position of separation string",
                  xlab="String top position",
                  col="gray",
                  freq=FALSE)
opar
dev.off()
print(separation.hist$counts)
