#-----------------------------------
# Functions to filter according to treshold
#-----------------------------------



#General plot
AFC_plot <- function(AFC){
  filename <- paste("../graphs/", var_name, "_AFC.bmp", sep = "")
  bmp(filename = filename, width = 2048, height = 2048, res = 200)
  plot_obj <- fviz_ca_col(AFC,
                          shape.col = 16,
                          labelsize = 4,
                          repel = TRUE,
                          col.col = "black") +
              theme_classic()
  print(plot_obj)
  dev.off()
}

#General plot with cos2 representing contribution
	#the value of the cos2 is between 0 and 1. A cos2 closed to 1 corresponds
	#to a column/row variables that are well represented on the factor map.
AFC_plot_cos2 <- function(AFC){
  filename <- paste("../graphs/", var_name, "_AFC_cos2.bmp", sep = "")
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
