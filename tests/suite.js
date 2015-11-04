/** Test suite runner. */
function runTests() {
    var cases = [
        test_basicOperations,
        test_excludeNamespaces,
        test_includeMatchingNamespaces,
        test_renameNamespaces,
        test_renameNamespacesIndexes,
        test_resumeFromSavedTimestamp,
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
    MongoRunner.dataPath = '/tmp/'
    var rs1 = new ReplSetTest({
        name: 'rs1',
        nodes: [{nojournal: ''}],
        startPort: 31001,
    });
    var rs2 = new ReplSetTest({
        name: 'rs2',
        nodes: [{nojournal: ''}],
        startPort: 31002,
    });

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
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', src.host,
        '--dest', dst.host
    );

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
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host,
        '--exclude', 'testdb.exclude_coll', 'test_ignored_db'
    );

    // Changes in namespaces that are not in --exclude list should be delivered
    var destDb1 = rs2.getPrimary().getDB('testdb');
    var destDb2 = rs2.getPrimary().getDB('test_ignored_db');

    assert(destDb1.include_coll.count(), 1);

    // Changes in excluded namespaces should not be on dest server
    assert.eq(destDb1.exclude_coll.count(), 0);
    assert.eq(destDb2.coll.count(), 0);
}

function test_includeMatchingNamespaces(rs1, rs2) {
    // Given operations on several different namespaces
    var srcDb1 = rs1.getPrimary().getDB('testdb');
    var srcDb2 = rs1.getPrimary().getDB('test_ignored_db');

    srcDb1.include_coll.insert({msg: "This namespace should be transfered"});
    srcDb1.other_coll.insert({msg: "This namespace should be ignored"});
    srcDb2.coll.insert({msg: "This whole db should be ignored"});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    // Process only one namespace (a collection)
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host,
        '--ns', 'testdb.include_coll'
    );

    // Only changes in namespaces specified in --ns should be delivered
    var destDb1 = rs2.getPrimary().getDB('testdb');
    var destDb2 = rs2.getPrimary().getDB('test_ignored_db');

    assert(destDb1.include_coll.count(), 1);

    // All other namespaces should be ignored
    assert.eq(destDb1.exclude_coll.count(), 0);
    assert.eq(destDb2.coll.count(), 0);
}

function test_renameNamespaces(rs1, rs2) {

    // Given operations on different namespaces
    var srcDb1 = rs1.getPrimary().getDB('renamedb');
    var srcDb2 = rs1.getPrimary().getDB('testdb');

    srcDb1.coll_1.insert({msg: "All collections in this db "});
    srcDb1.coll_2.insert({msg: "  should be moved to other db"});

    srcDb2.renameMe.insert({msg: "Only this collection must be renamed"});
    srcDb2.notMe.insert({msg: "...but not this"});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    // Rename one db and one collection during transfer
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host,
        '--rename', 'renamedb=newdb', 'testdb.renameMe=testdb.newMe'
    )

    // Namespaces (databases and collections) given in --rename argument
    // should be actually renamed on destination server
    var dest = rs2.getPrimary();
    assert(dest.getDB('newdb').coll_1.findOne());
    assert(dest.getDB('newdb').coll_2.findOne());
    assert(dest.getDB('testdb').newMe.findOne());

    // Old namespaces should not appear on destination server
    assert(dest.getDB('renamedb').coll_1.findOne() == null);
    assert(dest.getDB('renamedb').coll_2.findOne() == null);
    assert(dest.getDB('testdb').renameMe.findOne() == null);
}

function test_renameNamespacesIndexes(rs1, rs2) {

    // Given operations on different namespaces
    var srcDb1 = rs1.getPrimary().getDB('testdb');

    srcDb1.coll_1.ensureIndex({'msg': 1})
    srcDb1.coll_1.insert({msg: "This message is indexed"});

    // Invoke mongooplog-alt to transfer changes from rs1 to rs2
    // Rename one db and one collection during transfer
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host,
        '--rename', 'testdb.coll_1=testdb.coll_new'
    )

    // Namespaces in index operation
    // should be actually renamed on destination server
    var dest = rs2.getPrimary();
    assert(dest.getDB('testdb').coll_new.findOne());

    // The index should have been created on the new collection
    assert(dest.getDB('testdb').coll_new.getIndexes()[1]['name'] == 'msg_1');

    // Old namespaces should not appear on destination server
    assert(dest.getDB('testdb').coll_1.findOne() == null);
}

function test_resumeFromSavedTimestamp(rs1, rs2) {
    var srcDb  = rs1.getPrimary().getDB('testdb');
    var destDb = rs2.getPrimary().getDB('testdb');
    var destLocal = rs2.getPrimary().getDB('local');

    // 1. Do some operation on source db and replicate it to the dest db
    srcDb.test_coll.insert({msg: "Hello world!"});
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host
    );

    // 2. Notice oplog size on dest server
    var oplogSizeAfterStep1 = destLocal.oplog.rs.count();

    // 3. Do one more operation on source and replicate it one more time
    srcDb.test_coll.remove({msg: "Hello world!"});
    runMongoProgram(
        'python', '-m', 'jaraco.mongodb.oplog',
        '--source', rs1.getPrimary().host,
        '--dest', rs2.getPrimary().host
    );

    // 4. mongooplog-alt should process only the last one operation.
    //    Thus, oplog size must increase by 1
    var oplogSizeAfterStep2 = destLocal.oplog.rs.count();
    assert.eq(oplogSizeAfterStep2 - oplogSizeAfterStep1, 1);
}

runTests();
