def test_list_active_doctors(client, make_doctor):
    """Covers line 19: return doctor_repo.list_active(session)."""
    doc1, doc2 = make_doctor(), make_doctor()
    r = client.get("/doctors")
    assert r.status_code == 200
    
    body = r.json()
    assert isinstance(body, list)
    
    returned_ids = [d["id"] for d in body]
    assert str(doc1.id) in returned_ids
    assert str(doc2.id) in returned_ids
