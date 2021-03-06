            ##
            # Author: Autogenerated on 2013-12-18 17:01:19
            # gitHash: 2581a0dfa12a51892283830529a5126ea49f0cb9
            # SEED: 2481425483200553751
            ##
            setwd(normalizePath(dirname(R.utils::commandArgs(asValues=TRUE)$"-f")))
            source('../findNSourceUtils.R')
            complexFilterTest_allyears2k_headers_38 <- function(conn) {
                Log.info("A munge-task R unit test on data <allyears2k_headers> testing the functional unit <['', '<=']> ")
                Log.info("Uploading allyears2k_headers")
                hex <- h2o.uploadFile(conn, locate("../../smalldata/airlines/allyears2k_headers.zip"), "rallyears2k_headers.hex")
            Log.info("Performing compound task ( ( hex[,c(\"Cancelled\")] <= 0.252596694009 ))  on dataset <allyears2k_headers>")
                     filterHex <- hex[( ( hex[,c("Cancelled")] <= 0.252596694009 )) ,]
            Log.info("Performing compound task ( ( hex[,c(\"Diverted\")] <= 0.952276526236 ))  on dataset allyears2k_headers, and also subsetting columns.")
                     filterHex <- hex[( ( hex[,c("Diverted")] <= 0.952276526236 )) , c("ActualElapsedTime","DepDelay","Diverted","DayOfWeek","Distance","TaxiIn","TaxiOut","CRSElapsedTime","ArrTime","CarrierDelay","CRSArrTime","DayofMonth","Year")]
                Log.info("Now do the same filter & subset, but select complement of columns.")
                     filterHex <- hex[( ( hex[,c("Diverted")] <= 0.952276526236 )) , c("ArrDelay","SecurityDelay","Month","DepTime","Origin","CancellationCode","FlightNum","LateAircraftDelay","WeatherDelay","Cancelled","TailNum","AirTime","IsArrDelayed","CRSDepTime","IsDepDelayed","Dest","UniqueCarrier","NASDelay")]
            testEnd()
            }
            doTest("compoundFilterTest_ on data allyears2k_headers unit= ['', '<=']", complexFilterTest_allyears2k_headers_38)
