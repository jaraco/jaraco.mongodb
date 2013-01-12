// Globals: test environment
var rs1, rs2;
var srcConn, destConn, srcDb, destDb, srcColl, destColl;

/** Test suite runner. */
function runTests() {
    setUp();

    test_basicOperations();

    tearDown();
}

/** Initialize test environment. */
function setUp() {
    rs1 = new ReplSetTest({name: 'rs1',
                           nodes: [{nojournal: ''}],
                           startPort:31001});
    rs2 = new ReplSetTest({name: 'rs2',
                           nodes: [{nojournal: ''}],
                           startPort:31002});
    rs1.startSet({oplogSize: 1})
    rs2.startSet({oplogSize: 1})
    rs1.initiate();
    rs2.initiate();
    rs1.awaitSecondaryNodes();
    rs2.awaitSecondaryNodes();

    srcConn   = new Mongo(rs1.getURL());
    srcDb     = srcConn.getDB('test');
    src       = srcDb.basic01;

    destConn  = new Mongo(rs2.getURL());
    destDb    = destConn.getDB('test');
    dest      = destDb.basic01;
}

/** Clean up after the tests. */
function tearDown() {
    rs1.stopSet();
    rs2.stopSet();
}


/*
 * Check that oplog records can be applied from one replica set to another
 */
function test_basicOperations() {
    // Insert some data in source db
    src.insert({"answer": "unknown"});
    src.update({"answer": "unknown"}, {"$set": {"answer": 42}});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    runMongoProgram('mongooplog-alt',
                    '--from', rs1.getPrimary().host,
                    '--host', rs2.getPrimary().host);

    // Check that all operations got applied
    assert(dest.findOne());
    assert.eq(dest.findOne().answer, 42);
}


runTests();
