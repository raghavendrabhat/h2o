import unittest, random, sys, time, math
sys.path.extend(['.','..','py'])
import h2o, h2o_cmd, h2o_hosts, h2o_import as h2i, h2o_exec as h2e, h2o_util

print "Create csv with lots of same data (98% 0?), so gz will have high compression ratio"
print "Cat a bunch of them together, to get an effective large blow up inside h2o"
print "Can also copy the files to test multi-file gz parse...that will behave differently"
print "Behavior may be different depending on whether small ints are used, reals or used, or enums are used"
print "Remember the enum translation table has to be passed around between nodes, and updated atomically"

print "response variable is the modulo sum of all features, for a given base"
print "\nThen do RF"

BASE = 2
def write_syn_dataset(csvPathname, rowCount, colCount, SEED):
    # 8 random generators, 1 per column
    r1 = random.Random(SEED)
    dsf = open(csvPathname, "w+")

    for i in range(rowCount):
        rowData = []
        rowSum = 0
        for j in range(colCount):
            if BASE==2:
                # 50/50
                # r = h2o_util.choice_with_probability([(0, .5), (1, .5)])
                # 98/2
                r = h2o_util.choice_with_probability([(0, .98), (1, .2)])
            else:
                raise Exception("Unsupported BASE: " + BASE)

            rowSum += r


            rowData.append(r)

        responseVar = rowSum % BASE
        # make r a many-digit real, so gzip compresses even more better!
        rowData.append('%#034.32e' % responseVar)
        rowDataCsv = ",".join(map(str,rowData))
        dsf.write(rowDataCsv + "\n")

    dsf.close()

def make_datasetgz_and_parse(SYNDATASETS_DIR, csvFilename, hex_key, rowCount, colCount, FILEREPL, SEEDPERFILE, timeoutSecs):
    csvPathname = SYNDATASETS_DIR + '/' + csvFilename
    print "Creating random", csvPathname
    write_syn_dataset(csvPathname, rowCount, colCount, SEEDPERFILE)

    csvFilenamegz = csvFilename + ".gz"
    csvPathnamegz = SYNDATASETS_DIR + '/' + csvFilenamegz
    h2o_util.file_gzip(csvPathname, csvPathnamegz)

    csvFilenameReplgz = csvFilename + "_" + str(FILEREPL) + "x.gz"
    csvPathnameReplgz = SYNDATASETS_DIR + '/' + csvFilenameReplgz
    print "Replicating", csvFilenamegz, "into", csvFilenameReplgz

    start = time.time()
    h2o_util.file_cat(csvPathnamegz, csvPathnamegz , csvPathnameReplgz)
    # no header? should we add a header? would have to be a separate gz?
    totalRows = 2 * rowCount
    for i in range(FILEREPL-2):
        h2o_util.file_append(csvPathnamegz, csvPathnameReplgz)
        totalRows += rowCount
    print "Replication took:", time.time() - start, "seconds"

    start = time.time()
    print "Parse start:", csvPathnameReplgz
    doSummary = False
    parseResult = h2i.import_parse(path=csvPathnameReplgz, schema='put', hex_key=hex_key, 
        timeoutSecs=timeoutSecs, pollTimeoutSecs=120, doSummary=doSummary)
    if doSummary:
        algo = "Parse and Summary:"
    else:
        algo = "Parse:"
    print algo , parseResult['destination_key'], "took", time.time() - start, "seconds"

    print "Inspecting.."
    start = time.time()
    inspect = h2o_cmd.runInspect(None, parseResult['destination_key'], timeoutSecs=timeoutSecs)
    print "Inspect:", parseResult['destination_key'], "took", time.time() - start, "seconds"
    h2o_cmd.infoFromInspect(inspect, csvPathname)
    print "\n" + csvPathname, \
        "    numRows:", "{:,}".format(inspect['numRows']), \
        "    numCols:", "{:,}".format(inspect['numCols'])

    # there is an extra response variable
    if inspect['numCols'] != (colCount + 1):
        raise Exception("parse created result with the wrong number of cols %s %s" % (inspect['numCols'], colCount))
    if inspect['numRows'] != totalRows:
        raise Exception("parse created result with the wrong number of rows (header shouldn't count) %s %s" % \
        (inspect['numRows'], rowCount))

    # hack it in! for test purposees only
    parseResult['numRows'] = inspect['numRows']
    parseResult['numCols'] = inspect['numCols']
    parseResult['byteSize'] = inspect['byteSize']
    return parseResult

class Basic(unittest.TestCase):
    def tearDown(self):
        h2o.check_sandbox_for_errors()

    @classmethod
    def setUpClass(cls):
        global SEED, localhost, tryHeap
        tryHeap = 14
        SEED = h2o.setup_random_seed()
        localhost = h2o.decide_if_localhost()
        if (localhost):
            h2o.build_cloud(1, java_heap_GB=tryHeap, enable_benchmark_log=True)
        else:
            h2o_hosts.build_cloud_with_hosts(enable_benchmark_log=True)

    @classmethod
    def tearDownClass(cls):
        h2o.tear_down_cloud()

    def test_rf_syn_gz_cat(self):
        h2o.beta_features = True
        SYNDATASETS_DIR = h2o.make_syn_dir()
        tryList = [
            # summary fails with 100000 cols
            # (10, 50, 2, 'cA', 600),
            (10, 50, 5000, 'cA', 600),
            (50, 50, 5000, 'cB', 600),
            (100, 50, 5000, 'cC', 600),
            (500, 50, 5000, 'cD', 600),
            (1000, 50, 5000, 'cE', 600),
            (5000, 50, 5000, 'cF', 600),
            # at 6000, it gets connection reset on the parse on ec2
            # (6000, 50, 5000, 'cG', 600),
            # (7000, 50, 5000, 'cH', 600),
            ]

        ### h2b.browseTheCloud()

        paramDict = {
            'ntrees': 10,
            'destination_key': 'model_keyA',
            'max_depth': 10,
            'nbins': 100,
            'sample_rate': 0.80,
            }


        trial = 0
        for (FILEREPL, rowCount, colCount, hex_key, timeoutSecs) in tryList:
            trial += 1

            SEEDPERFILE = random.randint(0, sys.maxint)
            csvFilename = 'syn_' + str(SEEDPERFILE) + "_" + str(rowCount) + 'x' + str(colCount) + '.csv'
            csvPathname = SYNDATASETS_DIR + '/' + csvFilename
            parseResult = make_datasetgz_and_parse(SYNDATASETS_DIR, csvFilename, hex_key, rowCount, colCount, FILEREPL, SEEDPERFILE, timeoutSecs)

            paramDict['response'] = 'C' + str(colCount)
            paramDict['mtries'] = 2
            paramDict['seed'] = random.randint(0, sys.maxint)
            kwargs = paramDict.copy()

            start = time.time()
            rfView = h2o_cmd.runRF(parseResult=parseResult, timeoutSecs=timeoutSecs, **kwargs)
            elapsed = time.time() - start
            print "RF end on ", parseResult['destination_key'], 'took', elapsed, 'seconds.', \
                "%d pct. of timeout" % ((elapsed/timeoutSecs) * 100)

            (classification_error, classErrorPctList, totalScores) = h2o_rf.simpleCheckRFView(rfv=rfView)

            algo = "RF " 
            l = '{:d} jvms, {:d}GB heap, {:s} {:s} {:6.2f} secs. trees: {:d} Error: {:6.2f} \
                numRows: {:d} numCols: {:d} value_size_bytes: {:d}'.format(
                len(h2o.nodes), tryHeap, algo, parseResult['destination_key'], elapsed, kwargs['ntrees'], \
                classification_error, parseResult['numRows'], parseResult['numCols'], parseResult['byteSize'])
            print l
            h2o.cloudPerfH2O.message(l)

            print "Trial #", trial, "completed"


if __name__ == '__main__':
    h2o.unit_main()