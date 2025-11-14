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

default_folder <- "./Patterns_results/Specifs"
print(default_folder)
s)

args <- commandArgs(trailingOnly = TRUE)
file = args[1]
path = args[2]



base_name <- basename(file)
input_file <- file
df <- read.csv(input_file, sep="\t", row.names = 1, header=T, check.names = FALSE)
rep_name=path



#cleaning
df <- df[rowSums(df) != 0, ]

# Compute CA
AFC = CA(df, graph=F)

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

#----plots de HCPC----# Hugo Dumoulin 05-07/2025

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
    theme_classic() +
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


plot_v_test_clust_ind <- function(data_type, AFC, rep_name = "output", custom_colors = NULL) {
	#modifier nom en fonction de data_type
	type_array <- paste0("hclust_",data_type,"$desc.var")
	array_type <- eval(parse(text = type_array))
	
	#extraire pour chaque cluster les var où v.test > 0
	clust <- lapply(array_type, function(mat) {
  	# Sélectionner uniquement les lignes avec v.test > 0
  	vars <- rownames(mat)[mat[, "v.test"] > 0]
  	# Garder au plus 5 variables
  	head(vars, 5)
	})

	#clust_clean <- lapply(clust, function(vec) {
 	# gsub("\\.", " ", vec)
	#})
	clust_clean <- lapply(clust, function(vec) {
  	# Remplacer uniquement les points entre deux blocs {lemma_"..."} -> {lemma_"..."} {lemma_"..."}
 	 gsub("\\}\\.\\{", "} {", vec)
	})

	ind = unlist(clust_clean)
	
	if (data_type=="col"){
		AFC_type = "row"
	}
	
	if (data_type=="row"){
		AFC_type = "col"
	}
	
	#récupérer les coordonnées de ces ind
	coords_full <- paste0("AFC$", AFC_type, "$coord")
  	coords=eval(parse(text = coords_full))
  	coords.individus <- coords[ind, 1:2]

	
	clusters <- unlist(lapply(names(clust_clean), function(cluster_name) {
  	individus <- clust_clean[[cluster_name]]
  	setNames(rep(cluster_name, length(individus)), individus)
	}))
	clusters <- factor(clusters)

	
	 # Construire le data.frame
  df <- data.frame(
    Dim1 = coords.individus[,1],
    Dim2 = coords.individus[,2],
    Cluster = clusters,
    Nom = ind
  )
  
  # Construire le graphique
  p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
    geom_point(size = 3) +
    ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
    geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
    theme_classic() +
    theme(
      panel.grid = element_blank(),
      axis.line = element_blank(),
      axis.ticks = element_blank(),
      axis.text = element_blank(),
      axis.title = element_text(color = "grey30")
    ) +
    labs(
      title = "Variables associées à chaque cluster par v-test",
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
  filename <- paste0(rep_name, glue("{data_type}_hclust_v_test.bmp"))
  ggsave(filename, plot = p, width = 8, height = 6, dpi = 300)
  
  return(p)
	

}

plot_v_test_clust_ind("col", AFC, rep_name, custom_colors = NULL) 
plot_v_test_clust_ind("row", AFC, rep_name, custom_colors = NULL) 


