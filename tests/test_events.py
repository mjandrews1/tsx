"""Parser smoke without network."""
from acquire.usgs_quakes import events
def test_events_idempotent_keys():
    fc={"features":[{"id":"ak1","properties":{"time":1710000000000,"mag":1.2,"magType":"ml","place":"test","url":"u","title":"t"},"geometry":{"coordinates":[-120.0,36.0,5.0]}}]}
    rows=list(events(fc))
    assert len(rows)==1 and rows[0]["nat_key"]=="ak1" and rows[0]["value"]==1.2
if __name__ == "__main__":
    test_events_idempotent_keys()
    print("OK")
