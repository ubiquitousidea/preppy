# A simple keyword and regex based tweet classifier
# 
# Input -- a csv of tweets
# Output -- 3 csvs of tweets:
#    relevant
#    irrelevant
#    relevant_geotagged
#
# Relevance is determined by checking each tweet against a set of
# user (programmer) defined keyword regexes
#
# This will eventually be replaced by /preppy/preppy/binaryclassifier.py
# but it will work for now: FPR and FNR hover around 1% and 3%, respectively

infile <- commandArgs(trailingOnly = TRUE)

keywords = list(
  PrEP = list(
    pat = "PrEP",
    case_insens = FALSE),
  STI = list(
    pat = "\\bST[ID]{1}\\b",
    case_insens = TRUE),
  truvada = list(
    pat = "truvada",
    case_insens = TRUE),
  hiv = list(
    pat = "\\bhiv\\b",
    case_insens = TRUE),
  aids = list(
    pat = "\\baids\\b",
    case_insens = TRUE),
  hivaids = list(
    pat = "hivaids",
    case_insens = TRUE),
  hiv_aids = list(
    pat = "hiv/aids",
    case_insens = FALSE),
  gay = list(
    pat = "\\bgay",
    case_insens = TRUE),
  msm = list(
    pat = "\\bmsm\\b",
    case_insens = TRUE),
  sex = list(
    pat = "\\bsex\\b",
    case_insens = TRUE),
  trans = list(
    pat = "\\btrans\\b",
    case_insens = TRUE),
  transgender = list(
    pat = "transgender",
    case_insens = TRUE),
  bareback = list(
    pat = "bareback", 
    case_insens = TRUE),
  prevention = list(
    pat = "prevention", 
    case_insens = TRUE),
  medication = list(
    pat = "medication",
    case_insens = TRUE),
  prescription = list(
    pat = "prescription",
    case_insens = TRUE),
  gilead = list(
    pat = "\\bgilead\\b", 
    case_insens = TRUE),
  bethegen = list(
    pat = "bethegeneration",
    case_insens = TRUE),
  united = list(
    pat = "united healthcare", 
    case_insens = TRUE), 
  FDA = list(
    pat = "\\bFDA\\b",
    case_insens = TRUE),
  CDC = list(
    pat = "\\bCDC(gov)?\\b",
    case_insens = TRUE),
  US_FDA = list(
    pat = "US_FDA",
    case_insens = TRUE),
  insurance = list(
    pat = "insurance",
    case_insens = TRUE),
  drug = list(
    pat = "\\bdrug\\b",
    case_insens = TRUE),
  fag = list(
    pat = "\\bfags?\\b",
    case_insens = TRUE),
  queer = list(
    pat = "queer",
    case_insens = TRUE)
)

main <- function(keywords, infile) {
  prep <- read.csv(infile)
  
  # need another workaround: keep utf for watson
  prep$text <- stringi::stri_enc_toascii(prep$text)
  
  for (i in seq_along(keywords)) {
    word <- names(keywords)[i]
    wordpat <- keywords[[i]]$pat
    case_insens <- keywords[[i]]$case_insens
    result <- grepl(wordpat, prep$text, ignore.case = case_insens)
    prep[[word]] <- result
  }
  
  prep$keep <- apply(prep[15:ncol(prep)], 1, any)
  keep_frame <- prep[prep$keep, ]
  toss_frame <- prep[!prep$keep, ]
  geotagged <- keep_frame[keep_frame$latitude != 0]
  
  print(paste("Out of", nrow(prep), "tweets:", 
              nrow(keep_frame), "kept,", 
              nrow(toss_frame), "tossed"))
  print(paste(nrow(geotagged), "geotagged relevant tweets"))
  
  outtime <- format(Sys.time(), "%Y-%m-%d_%H.%M.%S")
  write.csv(keep_frame, paste0("kept_tweets_", outtime), row.names = FALSE)
  write.csv(toss_frame, paste0("tossed_tweets_", outtime), row.names = FALSE)
  write.csv(geotagged, paste0("relevant_geotagged_", outtime), row.names = FALSE)
}

main(keywords, infile)

