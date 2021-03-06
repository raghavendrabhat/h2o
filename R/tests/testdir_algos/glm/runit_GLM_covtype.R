setwd(normalizePath(dirname(R.utils::commandArgs(asValues=TRUE)$"-f")))
source('../../findNSourceUtils.R')

test.GLM.covtype <- function(conn) {
  Log.info("Importing covtype.20k.data...\n")
  
  covtype.hex = h2o.uploadFile.VA(conn, locate("smalldata/covtype/covtype.20k.data"))
  covtype.sum = summary(covtype.hex)
  print(covtype.sum)
  
  myY = 55
  myX = setdiff(1:54, c(21,29))   # Cols 21 and 29 are constant, so must be explicitly ignored
  myX = myX[which(myX != myY)];
  
  # L2: alpha = 0, lambda = 0
  start = Sys.time()
  covtype.h2o1 = h2o.glm(y = myY, x = myX, data = covtype.hex, family = "binomial", nfolds = 2, alpha = 0, lambda = 0)
  end = Sys.time()
  Log.info(cat("GLM (L2) on", covtype.hex@key, "took", as.numeric(end-start), "seconds\n"))
  print(covtype.h2o1)
  
  # Elastic: alpha = 0.5, lambda = 1e-4
  start = Sys.time()
  covtype.h2o2 = h2o.glm(y = myY, x = myX, data = covtype.hex, family = "binomial", nfolds = 2, alpha = 0.5, lambda = 1e-4)
  end = Sys.time()
  Log.info(cat("GLM (Elastic) on", covtype.hex@key, "took", as.numeric(end-start), "seconds\n"))
  print(covtype.h2o2)
  
  # L1: alpha = 1, lambda = 1e-4
  start = Sys.time()
  covtype.h2o3 = h2o.glm(y = myY, x = myX, data = covtype.hex, family = "binomial", nfolds = 2, alpha = 1, lambda = 1e-4)
  end = Sys.time()
  Log.info(cat("GLM (L1) on", covtype.hex@key, "took", as.numeric(end-start), "seconds\n"))
  print(covtype.h2o3)
  
  testEnd()
}

doTest("Test GLM on covtype(20k) dataset", test.GLM.covtype)

