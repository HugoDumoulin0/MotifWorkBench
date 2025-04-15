# Timothée Premat and Hugo Dumoulin
# 28/03/2025

#Load/install packages, input file and set variables
ipak <- function(pkg){
new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg))
    install.packages(new.pkg, dependencies = TRUE)
sapply(pkg, require, character.only = TRUE)
}

# usage
packages <- c('FactoMineR',
	'ggrepel',
	'factoextra')
ipak(packages)

default_folder <- "../Patterns_results/Specifs_noZero"
print(default_folder)

input_suffix <- "_AFC_R_df"

files <- list.files(default_folder, full.name = TRUE)
matching_files <- files[grep(paste0(input_suffix, ".tsv", "$"), files)]

for (file in matching_files) {
    base_name <- basename(file)
    input_file <- file
    df <- read.csv(input_file, sep="\t", row.names = "motifs_str")
    var_name <- sub("\\.tsv$", "", input_file)



# input_file <- paste0(default_folder, "/10_AFC_R_df.tsv")
# df <- read.csv(input_file, sep="\t")


# var_name <- "random"
#---------------------------------
# Define functions
#---------------------------------
#General plot
AFC_plot <- function(AFC){
  filename <- paste(var_name, "_AFC.bmp", sep = "")
  bmp(filename = filename, width = 2048, height = 2048, res = 200)
  plot_obj <- fviz_ca_col(AFC,
                          shape.col = 16,
                          labelsize = 4,
                          repel = TRUE,
                          col.col = "red") +
              theme_classic()
  print(plot_obj)
  dev.off()
}

#General plot with cos2 representing contribution
	#the value of the cos2 is between 0 and 1. A cos2 closed to 1 corresponds
	#to a column/row variables that are well represented on the factor map.
AFC_plot_cos2 <- function(AFC){
  filename <- paste(var_name, "_AFC_cos2.bmp", sep = "")
  bmp(filename = filename, width = 2048, height = 2048, res = 200)
  plot_obj <- fviz_ca_col(AFC,
  	col.col = "cos2",
  	shape.col=16,
  	labelsize=4,
  	repel=T,
  	gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07")) +
  	theme_classic() +
  	guides(colour = guide_colourbar(position = "inside")) +
  	theme(legend.margin = margin(0, 0, 0, 0),
  		legend.position.inside = c(0.01, 1),
  		legend.justification.top = "left",
  		legend.justification.left = "top",
  		legend.justification.bottom = "left",
  		legend.justification.inside = c(0, 1),
  		legend.location = "plot")
  print(plot_obj)
  dev.off()
}

#-----------------------------------
# Functions to filter according to treshold
#-----------------------------------


#---------------------------------
# Apply
#---------------------------------

# Compute CA
AFC = CA(df[,-c(1,2)], graph=F)

# Plot and measures for 2 dims with no contrib threshold
# source("plots_func.R")
print("1")
AFC_plot(AFC)
print("2")
AFC_plot_cos2(AFC)
print("3")
#-----------------------------------
# Check accuracy/explanatory power
#-----------------------------------

#Plot degree of variance explanation per axis
bmp(filename=paste(var_name, "_var_expl_per_axis.bmp", sep=""),
	width=1536, height=1536, res=200)
plot_obj <- fviz_screeplot(AFC,
	addlabels = TRUE) +
	theme_classic()
print(plot_obj)
dev.off()

#Take a look at representation accuracy
	#Get rows (MSE)
	row <- get_ca_row(AFC)

	#Get the 10 heaviest contributing rows
	contrib_10_rows <- head(row$contrib, 10)
	write.table(contrib_10_rows,
		file = paste(var_name, "_contrib_10_patterns.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Get cols (texts/subcorpora)
	col <- get_ca_col(AFC)

	#Get the 10 heaviest contributing cols
	contrib_10_cols <- head(col$contrib, 10)
	write.table(contrib_10_cols,
		file = paste(var_name, "_contrib_10_texts.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Plot it
	bmp(filename=paste(var_name, "_contrib_dim_1.bmp", sep=""),
		width=2048, height=2048, res=200)
	plot_obj <- fviz_contrib(AFC,
		choice ="col",
		axes = 1)
	print(plot_obj)
	dev.off()

	bmp(filename=paste(var_name, "_contrib_dim_2.bmp", sep=""),
		width=2048, height=2048, res=200)
	plot_obj <- fviz_contrib(AFC,
		choice ="col",
		axes = 2)
	print(plot_obj)
	dev.off()


# # Plot and measures for 2 dims with contrib threshold
# # source("plots_threshold.R")

# # Plot and measures for accuracy/explanatory power
# source("accuracy.R")
# # var_per_axis(AFC)

bmp(filename=paste(var_name, "_contrib10.bmp"),
    width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=10),col.var="contrib", 
    gradient.cols=c("#ffc2ca", "#ff0000"), shape.col=19)
	print(plot_obj)
dev.off()

bmp(filename=paste(var_name, "_ind_contrib10.bmp"),
    width=2048, height=2048, res=200)
plot_obj <- fviz_ca_row(AFC, select.row=list(contrib=10),col.var="contrib", gradient.rows=c("#ffc2ca", "#ff0000"), shape.col=19)
    print(plot_obj)
dev.off()

# bmp(filename=paste(var_name, "AFC_fviz2.bmp"),
#     width=2048, height=2048, res=200)
# plot_obj <- fviz_ca_col(AFC, shape.col=1, labelsize=4, repel=T, col.var="contrib", gradient.cols="#c30000", col.quali.sup="darkgreen")
#     print(plot_obj)
# dev.off()
# Redundant with AFC.bmp





######éléments script R HD local#####

#------AFC various viz-------#
bmp(filename="AFC_screeplot.bmp", width=2048, height=2048, res=200)
fviz_screeplot(AFC)
dev.off()

bmp(filename="AFC_fviz.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, select.col=list(contrib=10),col.var="contrib", gradient.cols=c("#ffc2ca", "#ff0000"), shape.col=19)
dev.off()

bmp(filename="AFC_fviz_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=10),col.var="contrib", gradient.rows=c("#ffc2ca", "#ff0000"), shape.col=19)
dev.off()

bmp(filename="AFC_fviz2.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, shape.col=1, labelsize=4, repel=T, col.var="contrib", gradient.cols="#c30000", col.quali.sup="darkgreen")
dev.off()

bmp(filename="AFC_fviz3.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, select.col=list(contrib=10),pointsize="contrib", shape.col=19, repel=T)
dev.off()

bmp(filename="AFC_fviz3+.bmp", width=2048, height=2048, res=200)
fviz_ca_col(AFC, select.col=list(contrib=20),pointsize="contrib", shape.col=19, repel=T)
dev.off()

bmp(filename="AFC_fviz3_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=10),pointsize="contrib", shape.row=19, repel=T)
dev.off()

bmp(filename="AFC_fviz3+_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=20),pointsize="contrib", shape.col=19, repel=T)
dev.off()

bmp(filename="AFC_fviz4_ind.bmp", width=2048, height=2048, res=200)
fviz_ca_row(AFC, select.row=list(contrib=30),pointsize="contrib", shape.row=19, repel=T)
dev.off()

#------hierarchical clustering------#
hclust = HCPC(AFC, nb.clust=-1, graph=F)

bmp(filename="hclust_map.bmp", width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="map")
dev.off()

bmp(filename="hclust_map_light.bmp", width=2048, height=2048, res=200)
plot(hclust, choice="map", ind.names = FALSE)
dev.off()

bmp(filename="hclust_chute.bmp", width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="bar")
dev.off()

capture.output(hclust$desc.var, file="hclust_desc_var.txt")
capture.output(hclust$desc.ind, file="hclust_desc_ind.txt")


#----IMPORTANT ! création du rep "motifs_cluster" dans lequel le script interpret_association_motif.py vient chercher ses motifs----#
dir.create("motifs_cluster")
for (cluster in 1:hclust$call$t$nb.clust) {
	nom = glue("motifs_cluster/{cluster}.csv")
	write.csv(hclust$desc.ind$para[cluster], file=nom, row.names=TRUE)
}

#--force 2 clusters : optionnal--#
hclust_force2 = HCPC(AFC, nb.clust=2, graph=F)
bmp(filename="hclust_force2_map.bmp", width=2048, height=2048, res=200)
plot.HCPC(hclust_force2, choice="map")
dev.off()
bmp(filename="hclust_force2_chute.bmp", width=2048, height=2048, res=200)
plot.HCPC(hclust_force2, choice="bar")
dev.off()
capture.output(hclust_force2$desc.var, file="hclust_force2_desc_var.txt")
capture.output(hclust_force2$desc.ind, file="hclust_force2_desc_ind.txt")



















