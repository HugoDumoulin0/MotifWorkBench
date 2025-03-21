# Timothée Premat and Hugo Dumoulin
# 27/02/2025

# This script must be run in interactive mode! If your setup does not
# do it on its own, do not run the code but enter source("main.R") in your R
# console.

#Load/install packages, input file and set variables
source("setup.R")

# Compute CA (fr. AFC)
AFC = CA(table[,-c(1,2)], graph=F)

# Plot and measures for 2 dims with no contrib threshold
source("plots_func.R")
AFC_plot(AFC)
AFC_plot_cos2(AFC)

# Plot and measures for 2 dims with contrib threshold
# source("plots_threshold.R")

# Plot and measures for accuracy/explanatory power
source("accuracy.R")
# var_per_axis(AFC)

bmp(filename="../graphs/AFC_fviz.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, select.col=list(contrib=10),col.var="contrib", gradient.cols=c("#ffc2ca", "#ff0000"), shape.col=19)
dev.off()

bmp(filename="../graphs/AFC_fviz_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=10),col.var="contrib", gradient.rows=c("#ffc2ca", "#ff0000"), shape.col=19)
dev.off()

bmp(filename="../graphs/AFC_fviz2.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, shape.col=1, labelsize=4, repel=T, col.var="contrib", gradient.cols="#c30000", col.quali.sup="darkgreen")
dev.off()

bmp(filename="../graphs/AFC_fviz3.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, select.col=list(contrib=10),pointsize="contrib", shape.col=19, repel=T)
dev.off()

bmp(filename="../graphs/AFC_fviz3_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=10),pointsize="contrib", shape.row=19, repel=T)
dev.off()

bmp(filename="../graphs/AFC_var_4.bmp", width=2048, height=2048, res=300)
plot.CA(AFC, invisible=c("row"), repel=T)
dev.off()

bmp(filename="../graphs/AFC_fviz4_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=30),pointsize="contrib", shape.row=19, repel=T)
dev.off()
