library(jsonlite)

#variables crées dans R
chaine <- "Bonjour"
flag <- TRUE
int <- 42
liste_strings <- c("a", "b", "c")
liste_int <- c(10, 20, 30)

#puis transformées en JSON pour l'output que lira Python
result <- toJSON(list(
  message = message,
  flag = flag,
  age = age,
  liste_strings = liste_strings,
  liste_int = liste_int
), auto_unbox = TRUE)

cat(result)