/*
 * Check that oplog records can be applied from one replica set to another
 */

// Start source and destination replica sets
var rs1 = new ReplSetTest({name: 'rs1',
                           nodes: [{nojournal: ''}],
                           startPort:31001});
var rs2 = new ReplSetTest({name: 'rs2',
                           nodes: [{nojournal: ''}],
                           startPort:31002});
rs1.startSet({oplogSize: 1})
rs2.startSet({oplogSize: 1})
rs1.initiate();
rs2.initiate();
rs1.awaitSecondaryNodes();
rs2.awaitSecondaryNodes();

var srcConn   = new Mongo(rs1.getURL());
var srcDb     = srcConn.getDB('test');
var src       = srcDb.basic01;

var destConn  = new Mongo(rs2.getURL());
var destDb    = destConn.getDB('test');
var dest      = destDb.basic01;

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

// Tear down
rs1.stopSet();
rs2.stopSet();
