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
	'factoextra', "glue")
ipak(packages)

default_folder <- "./Patterns_results/Specifs_noZero"
print(default_folder)

#input_suffix <- "_AFC_R_df"

#files <- list.files(default_folder, full.name = TRUE)
#matching_files <- files[grep(paste0(input_suffix, ".tsv", "$"), files)]
#print(matching_files)

args <- commandArgs(trailingOnly = TRUE)
file = args[1]
path = args[2]



base_name <- basename(file)
input_file <- file
df <- read.csv(input_file, sep="\t", row.names = 1)
#var_name <- sub("\\.tsv$", "", input_file)

rep_name=path
#rep_name <- sub("./Patterns_results/Specifs_noZero/", "", var_name)
#rep_name <- sub("_df", "", rep_name)
#dir.create(glue("./Patterns_results/R/{rep_name}"))

#var_name <- glue("./Patterns_results/R/{rep_name}/")
	#var_name <- sub("./Patterns_results/Specifs_noZero/25_AFC_R_df", glue("./Patterns_results/R/{rep_name}/"), var_name)
#print(var_name)




# input_file <- paste0(default_folder, "/10_AFC_R_df.tsv")
# df <- read.csv(input_file, sep="\t")


# var_name <- "random"
#---------------------------------
# Define functions
#---------------------------------
#General plot
# <- function(AFC){
 # filename <- paste(var_name, "AFC.bmp", sep = "")
  #bmp(filename = filename, width = 2048, height = 2048, res = 200)
  #plot_obj <- fviz_ca_col(AFC,
   #                       shape.col = 16,
    #                      labelsize = 4,
     #                     repel = TRUE,
      #                    col.col = "red") +
       #       theme_classic()
  #print(plot_obj)
  #dev.off()
#}

#General plot with cos2 representing contribution
	#the value of the cos2 is between 0 and 1. A cos2 closed to 1 corresponds
	#to a column/row variables that are well represented on the factor map.
#AFC_plot_cos2 <- function(AFC){
#  filename <- paste(var_name, "AFC_cos2.bmp", sep = "")
#  bmp(filename = filename, width = 2048, height = 2048, res = 200)
#  plot_obj <- fviz_ca_col(AFC,
 # 	col.col = "cos2",
  #	shape.col=16,
  #	labelsize=4,
  #	repel=T,
  #	gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07")) +
  #	theme_classic() +
  #	guides(colour = guide_colourbar(position = "inside")) +
  #	theme(legend.margin = margin(0, 0, 0, 0),
  #		legend.position.inside = c(0.01, 1),
  #		legend.justification.top = "left",
  #		legend.justification.left = "top",
  #		legend.justification.bottom = "left",
  #		legend.justification.inside = c(0, 1),
  #		legend.location = "plot")
  #print(plot_obj)
  #dev.off()
#}

#-----------------------------------
# Functions to filter according to treshold
#-----------------------------------


#---------------------------------
# Apply
#---------------------------------

# Compute CA
#AFC = CA(df[,-c(1,2)], graph=F)
AFC = CA(df, graph=F)

# Plot and measures for 2 dims with no contrib threshold
# source("plots_func.R")
#print("1")
#AFC_plot(AFC)
#print("2")
#AFC_plot_cos2(AFC)
#print("3")
#-----------------------------------
# Check accuracy/explanatory power
#-----------------------------------

#Plot degree of variance explanation per axis
bmp(filename=paste(rep_name, "screeplot.bmp", sep=""),
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
		file = paste(rep_name, "contrib_10_patterns.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Get cols (texts/subcorpora)
	col <- get_ca_col(AFC)

	#Get the 10 heaviest contributing cols
	contrib_10_cols <- head(col$contrib, 10)
	write.table(contrib_10_cols,
		file = paste(rep_name, "contrib_10_texts.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Plot it
	bmp(filename=paste(rep_name, "contrib_dim_1.bmp", sep=""),
		width=2048, height=2048, res=200)
	plot_obj <- fviz_contrib(AFC,
		choice ="col",
		axes = 1)
	print(plot_obj)
	dev.off()

	bmp(filename=paste(rep_name, "contrib_dim_2.bmp", sep=""),
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

bmp(filename=paste(rep_name, "txt_contrib10.bmp"),
    width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=10),col.var="contrib", 
    gradient.cols=c("#ffc2ca", "#ff0000"), shape.col=19, repel=T)
	print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "motif_contrib10.bmp"),
    width=2048, height=2048, res=200)
plot_obj <- fviz_ca_row(AFC, select.row=list(contrib=10),col.var="contrib", gradient.rows=c("#ffc2ca", "#ff0000"), shape.col=19, repel=T)
    print(plot_obj)
dev.off()
  
bmp(filename=paste(rep_name, "txt_contrib10_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=10),pointsize="contrib", shape.col=19, repel=T)
print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "txt_contrib20_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=20),pointsize="contrib", shape.col=19, repel=T)
print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "motif_contrib10_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_row(AFC, select.row=list(contrib=10),pointsize="contrib", shape.row=19, repel=T)
print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "motif_contrib20_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_row(AFC, select.row=list(contrib=20),pointsize="contrib", shape.col=19, repel=T)
print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "motif_contrib30_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_row(AFC, select.row=list(contrib=30),pointsize="contrib", shape.row=19, repel=T)
print(plot_obj)
dev.off()

bmp(filename=paste(rep_name, "text_contrib30_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=30),pointsize="contrib", shape.col=19, repel=T)
print(plot_obj)
dev.off()

#------hierarchical clustering------#
hclust = HCPC(AFC, nb.clust=-1, graph=F)

bmp(filename=paste(rep_name, "hclust_map_rows.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="map")
dev.off()

bmp(filename=paste(rep_name, "hclust_map_cols.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="map", cluster.ca="columns")
dev.off()

bmp(filename=paste(rep_name, "hclust_map_rows_light.bmp"), width=2048, height=2048, res=200)
plot(hclust, choice="map", ind.names = FALSE)
dev.off()

bmp(filename=paste(rep_name, "hclust_map_cols_light.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="map", cluster.ca="columns")
dev.off()

bmp(filename=paste(rep_name, "hclust_rows_chute.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust, choice="bar")
dev.off()

capture.output(hclust$desc.var, file=paste(rep_name, "hclust_desc_var.txt"))
capture.output(hclust$desc.ind, file=paste(rep_name, "hclust_desc_ind.txt"))


#----IMPORTANT ! création du rep "motifs_cluster" dans lequel le script interpret_association_motif.py vient chercher ses motifs----#

dir.create(glue("{rep_name}motifs_cluster"))

for (cluster in 1:hclust$call$t$nb.clust) {
	para = glue("{rep_name}motifs_cluster/{cluster}_para.csv")
	write.csv(hclust$desc.ind$para[cluster], file=para, row.names=TRUE)
	dist = glue("{rep_name}motifs_cluster/{cluster}_dist.csv")
	write.csv(hclust$desc.ind$dist[cluster], file=dist, row.names=TRUE)
}



#--force 2 clusters : optionnal--#
hclust_force2 = HCPC(AFC, nb.clust=2, graph=F)
bmp(filename=paste(rep_name, "hclust_force2_map.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_force2, choice="map")
dev.off()
bmp(filename=paste(rep_name, "hclust_force2_chute.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_force2, choice="bar")
dev.off()
capture.output(hclust_force2$desc.var, file=paste(rep_name, "hclust_force2_desc_var.txt"))
capture.output(hclust_force2$desc.ind, file=paste(rep_name, "hclust_force2_desc_ind.txt"))




 #ferme l'accolade ouverte ligne 26














