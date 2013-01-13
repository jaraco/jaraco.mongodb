/** Test suite runner. */
function runTests() {
    var cases = [test_basicOperations,
                 test_excludeNamespaces,
                ];

    cases.forEach(function(test) {
        var env = setUp();
        print("============================");
        print("       " + test.name);
        print("============================");
        test(env.rs1, env.rs2);
        tearDown(env);
    });
}

/** Initialize test environment. */
function setUp() {
    var rs1 = new ReplSetTest({name: 'rs1',
                           nodes: [{nojournal: ''}],
                           startPort:31001});
    var rs2 = new ReplSetTest({name: 'rs2',
                           nodes: [{nojournal: ''}],
                           startPort:31002});

    rs1.startSet({oplogSize: 1})
    rs1.initiate();
    rs1.waitForMaster();

    rs2.startSet({oplogSize: 1})
    rs2.initiate();
    rs2.waitForMaster();

    return {rs1: rs1, rs2: rs2};
}

/** Clean up after the tests. */
function tearDown(env) {
    env.rs1.stopSet();
    env.rs2.stopSet();
}


/*
 * Check that oplog records can be applied from one replica set to another
 */
function test_basicOperations(rs1, rs2) {
    var src = rs1.getPrimary();
    var dst = rs2.getPrimary();
    var srcColl = src.getDB("test").coll;
    var dstColl = dst.getDB("test").coll;

    // Insert some data in source db
    srcColl.insert({"answer": "unknown"});
    srcColl.update({"answer": "unknown"}, {"$set": {"answer": 42}});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    runMongoProgram('mongooplog-alt',
                    '--from', src.host,
                    '--host', dst.host);

    // Check that all operations got applied
    assert(dstColl.findOne());
    assert.eq(dstColl.findOne().answer, 42);
}

function test_excludeNamespaces(rs1, rs2) {
    // Given operations on several different namespaces
    var srcDb1 = rs1.getPrimary().getDB('testdb');
    var srcDb2 = rs1.getPrimary().getDB('test_ignored_db');

    srcDb1.include_coll.insert({msg: "This namespace should be transfered"});
    srcDb1.exclude_coll.insert({msg: "This namespace should be ignored"});
    srcDb2.coll.insert({msg: "This whole db should be ignored"});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    // Ignore two namespaces: a collection and a whole database
    runMongoProgram('mongooplog-alt',
                    '--from', rs1.getPrimary().host,
                    '--host', rs2.getPrimary().host,
                    '--exclude', 'testdb.exclude_coll', 'test_ignored_db');

    // Changes in namespaces that are not in --exclude list should be delivered
    var destDb1 = rs2.getPrimary().getDB('testdb');
    var destDb2 = rs2.getPrimary().getDB('test_ignored_db');

    assert(destDb1.include_coll.count(), 1);

    // Changes in excluded namespaces should not be on dest server
    assert.eq(destDb1.exclude_coll.count(), 0);
    assert.eq(destDb2.coll.count(), 0);
}


runTests();
