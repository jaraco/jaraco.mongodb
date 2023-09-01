from jaraco.mongodb import fields


def test_insert_with_dots(mongodb_instance):
    db = mongodb_instance.get_connection().test_db
    field = fields.encode("foo.bar")
    db.things.insert_one({field: "value"})
    doc = db.things.find_one({field: "value"})
    doc = {fields.decode(key): value for key, value in doc.items()}
    assert doc['foo.bar'] == 'value'
