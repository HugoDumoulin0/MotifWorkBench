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

#cleaning
df <- df[rowSums(df) != 0, ]

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

bmp(filename=paste(rep_name, "txt_contrib30_size.bmp"), width=2048, height=2048, res=200)
plot_obj <- fviz_ca_col(AFC, select.col=list(contrib=30),pointsize="contrib", shape.col=19, repel=T)
print(plot_obj)
dev.off()

#------hierarchical clustering------#
hclust_row <- HCPC(AFC, nb.clust=-1, graph=F)
hclust_col <- HCPC(AFC, cluster.CA="columns", nb.clust=-1, graph=F)

#----------plots---------------------#

bmp(filename=paste(rep_name, "rows_hclust_map.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_row, choice="map")
dev.off()

bmp(filename=paste(rep_name, "cols_hclust_map.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_col, choice="map")
dev.off()

bmp(filename=paste(rep_name, "rows_hclust_map_light.bmp"), width=2048, height=2048, res=200)
plot(hclust_row, choice="map", ind.names = FALSE)
dev.off()

bmp(filename=paste(rep_name, "cols_hclust_map_light.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_col, choice="map", ind.names = FALSE)
dev.off()

bmp(filename=paste(rep_name, "rows_hclust_chute.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_row, choice="bar")
dev.off()

bmp(filename=paste(rep_name, "cols_hclust_chute.bmp"), width=2048, height=2048, res=200)
plot.HCPC(hclust_col, choice="bar")
dev.off()

capture.output(hclust_row$desc.var, file=paste(rep_name, "rows_hclust_desc_var.txt"))
capture.output(hclust_row$desc.ind, file=paste(rep_name, "rows_hclust_desc_ind.txt"))

capture.output(hclust_col$desc.var, file=paste(rep_name, "cols_hclust_desc_var.txt"))
capture.output(hclust_col$desc.ind, file=paste(rep_name, "cols_hclust_desc_ind.txt"))


#----IMPORTANT ! création du rep "motifs_cluster" dans lequel le script interpret_association_motif.py vient chercher ses motifs----#

dir.create(glue("{rep_name}motifs_cluster"))

for (cluster in 1:hclust_row$call$t$nb.clust) {
	para = glue("{rep_name}motifs_cluster/{cluster}_para.csv")
	write.csv(hclust_row$desc.ind$para[cluster], file=para, row.names=TRUE)
	dist = glue("{rep_name}motifs_cluster/{cluster}_dist.csv")
	write.csv(hclust_row$desc.ind$dist[cluster], file=dist, row.names=TRUE)
}

#--force 2 clusters : optionnal--#
#hclust_force2 = HCPC(AFC, nb.clust=2, graph=F)
#bmp(filename=paste(rep_name, "hclust_force2_map.bmp"), width=2048, height=2048, res=200)
#plot.HCPC(hclust_force2, choice="map")
#dev.off()
#bmp(filename=paste(rep_name, "hclust_force2_chute.bmp"), width=2048, height=2048, res=200)
#plot.HCPC(hclust_force2, choice="bar")
#dev.off()
#capture.output(hclust_force2$desc.var, file=paste(rep_name, "hclust_force2_desc_var.txt"))
#capture.output(hclust_force2$desc.ind, file=paste(rep_name, "hclust_force2_desc_ind.txt"))

#----plot de HCPC réduit----#

plot_CA_clusters<- function(data_type, individus_type, AFC, rep_name = "output", custom_colors = NULL) {
  # Extraire les parangons
  individus_full <- paste0("hclust_",data_type,"$desc.ind$", individus_type)
  individus <- eval(parse(text = individus_full))
  individus.names <- unlist(lapply(individus, names))
  
  # Coordonnées des parangons sur les deux premières dimensions
  coords_full <- paste0("AFC$", data_type, "$coord")
  coords=eval(parse(text = coords_full))
  coords.individus <- coords[individus.names, 1:2]
  
  # Déterminer à quel cluster appartient chaque parangon
  clusters <- sapply(individus.names, function(x) {
    which(sapply(individus, function(cl) x %in% names(cl)))
  })
  clusters <- factor(clusters)
  
  # Construire le data.frame
  df <- data.frame(
    Dim1 = coords.individus[,1],
    Dim2 = coords.individus[,2],
    Cluster = clusters,
    Nom = individus.names
  )
  
  # Construire le graphique
  p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
    geom_point(size = 3) +
    ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
    theme_minimal() +
    theme(
      panel.grid = element_blank(),
      axis.line = element_blank(),
      axis.ticks = element_blank(),
      axis.text = element_blank(),
      axis.title = element_text(color = "grey30")
    ) +
    labs(
      title = glue("Carte factorielle (CA) - individus {individus_type} uniquement"),
      x = "Dimension 1",
      y = "Dimension 2"
    )
  
  test_full = paste0("hclust_", data_type, "$call$t$nb.clust")
  test=eval(parse(text = test_full))
  # Palette manuelle (si 3 clusters uniquement ou définie via argument)
  if (!is.null(custom_colors)) {
    p <- p + scale_color_manual(values = custom_colors)
  } else if (test == 3) {
    p <- p + scale_color_manual(values = c("black", "red", "green"))
  }
  
  # Enregistrer le graphique
  filename <- paste0(rep_name, glue("{data_type}_hclust_{individus_type}.bmp"))
  ggsave(filename, plot = p, width = 8, height = 6, dpi = 300)
  
  return(p)
}


plot_CA_clusters("col", "para", AFC, rep_name, custom_colors = NULL) 
plot_CA_clusters("col", "dist", AFC, rep_name, custom_colors = NULL) 
plot_CA_clusters("row", "para", AFC, rep_name, custom_colors = NULL) 
plot_CA_clusters("row", "dist", AFC, rep_name, custom_colors = NULL) 







