library(data.table)

calc_specif_hyper <- function(x, F, t, T){
	library(textometry)
	#### Copyright © - 2012-2014 ENS de Lyon - https://textometrie.org (function specificities.distribution.plot) ###
	# x: observed number of A words
	# F: total number of A
	# t: size of motif
	# T: size of corpus
	
	# return : (px, mode, pfsum)
  
	# example: specificities.distribution.plot(11, 296, 1084, 61449)
	
	f=0:F
  
	mode.val=((F+1)*(t+1))/(T+2)
	
	pf=dhyper(f, F, T-F, t)
	pfsum=specificities.probabilities.vector(f, rep(F, F+1), rep(T, F+1), t)
  
	px <- pf[x+1]
	#### END Copyright © - 2012-2014 ENS de Lyon - https://textometrie.org ###
	
	mode.int <- as.integer(mode.val)
	#~ def pfsum = r.eval('res$pfsum'+"[$f+1]").asDouble()
	is.positive.spec = ifelse(x > abs(mode.int), TRUE, FALSE) # True if S+
	pfsumx <- pfsum[x+1]
	proba = abs(pfsumx)  # Compute actual probability (should be a positive number, even for negative specificities, where pfsum = -probability)
	specif <- ifelse(is.positive.spec, abs(log10(proba)), -1*abs(log10(proba)))
	specif <- ifelse(is.infinite(specif), sign(specif)*1000, specif)

	specif
}

calc_KLD <- function(f, F, t, T){
	O11 = f
	O12 = (F - f)
	O21 = (t - f)
	O22 = (T - F - t + f)
	E11 = ((F * t) / T)
	R1 = F
	R2 = (T - F)
	C1 = t
	C2 = (T - t)
	p.O11 = (O11 / R1)
	p.O12 = (O12 / R1)
	p.C1 = (C1 / T)
	p.C2 = (C2 / T)
	
	term.prob.O11 = ifelse(p.O11 > 0, p.O11 * log2((p.O11 / p.C1)), 0)
	term.prob.O12 = ifelse(p.O12 > 0, p.O12 * log2((p.O12 / p.C2)), 0)
	KLD.score = term.prob.O11 + term.prob.O12
	
	KLD.score
}


calc_specif <- function(df, scores=c("am.specif.hyper"))
{
	# Calcul de scores d'association
	DT <- data.table(df)
	DT[, `:=`(f=as.numeric(f), F=as.numeric(F), t=as.numeric(t), T=as.numeric(T))]
	DT[, `:=`(E11=((F*t)/T), mode.val=(((F+1)*(t+1))/(T+2)), am.specif.hyper=calc_specif_hyper(f, F, t, T)), by=list(fichier,motif)]
	if("am.KLD" %in% scores)
	{
		DT[, `:=`(am.KLD=calc_KLD(f, F, t, T)), by=list(fichier,motif)]
		DT[, `:=`(am.KLD=round(am.KLD,3)), by=list(fichier,motif)]
	}
	
	setkey(DT, fichier,motif)
	DT[, `:=`(f=as.integer(f), F=as.integer(F), t=as.integer(t), T=as.integer(T))]
	DT[, `:=`(E11=round(E11,3), mode.val=round(mode.val,3), am.specif.hyper=round(am.specif.hyper,3)), by=list(fichier,motif)]
	
	df.res <- as.data.frame(DT)
	
	df.res
}