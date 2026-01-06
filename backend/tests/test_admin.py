def test_list_content_types_public(client):
    """Test that anyone can list content types"""
    response = client.get("/admin/content-types")

    assert response.status_code == 200
    data = response.json()
    assert "content_types" in data
    assert len(data["content_types"]) > 0

    # Check default types exist
    type_names = [ct["name"] for ct in data["content_types"]]
    assert "quran" in type_names
    assert "sahifa_sajjadiya" in type_names
    assert "nahj_balagha" in type_names


def test_list_content_types_with_inactive(client):
    """Test listing content types including inactive ones"""
    response = client.get("/admin/content-types?include_inactive=true")

    assert response.status_code == 200
    data = response.json()
    assert "content_types" in data


def test_create_content_type_without_auth(client):
    """Test creating content type without authentication fails"""
    response = client.post(
        "/admin/content-types",
        json={
            "name": "test_type",
            "display_name": "Test Type",
            "description": "A test content type",
            "default_portion_types": {"chapter": 10},
        },
    )

    assert response.status_code == 401  # Unauthorized (no token provided)


def test_create_content_type_non_admin(client, auth_headers):
    """Test creating content type as non-admin fails"""
    response = client.post(
        "/admin/content-types",
        headers=auth_headers,
        json={
            "name": "test_type",
            "display_name": "Test Type",
            "default_portion_types": {"chapter": 10},
        },
    )

    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_create_content_type_as_admin(client, admin_headers):
    """Test creating content type as admin"""
    response = client.post(
        "/admin/content-types",
        headers=admin_headers,
        json={
            "name": "tafsir_tabari",
            "display_name": "Tafsir al-Tabari",
            "description": "Classical Quranic commentary",
            "default_portion_types": {"volume": 24, "part": 30},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "tafsir_tabari"
    assert "id" in data
    assert data["message"] == "Content type created successfully"


def test_create_duplicate_content_type(client, admin_headers):
    """Test creating duplicate content type fails"""
    # Create first
    client.post(
        "/admin/content-types",
        headers=admin_headers,
        json={"name": "duplicate_type", "display_name": "Duplicate", "default_portion_types": {}},
    )

    # Try to create duplicate
    response = client.post(
        "/admin/content-types",
        headers=admin_headers,
        json={
            "name": "duplicate_type",
            "display_name": "Another Duplicate",
            "default_portion_types": {},
        },
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_update_content_type(client, admin_headers):
    """Test updating content type"""
    # Create content type
    create_response = client.post(
        "/admin/content-types",
        headers=admin_headers,
        json={
            "name": "update_test",
            "display_name": "Update Test",
            "default_portion_types": {"chapter": 10},
        },
    )
    content_type_id = create_response.json()["id"]

    # Update it
    response = client.patch(
        f"/admin/content-types/{content_type_id}",
        headers=admin_headers,
        json={
            "display_name": "Updated Name",
            "default_portion_types": {"chapter": 15, "section": 50},
        },
    )

    assert response.status_code == 200
    assert "updated successfully" in response.json()["message"]

    # Verify update
    list_response = client.get("/admin/content-types")
    types = list_response.json()["content_types"]
    updated_type = next((t for t in types if t["id"] == content_type_id), None)
    assert updated_type is not None
    assert updated_type["display_name"] == "Updated Name"
    assert updated_type["default_portion_types"]["chapter"] == 15


def test_toggle_content_type(client, admin_headers):
    """Test activating/deactivating content type"""
    # Create content type
    create_response = client.post(
        "/admin/content-types",
        headers=admin_headers,
        json={"name": "toggle_test", "display_name": "Toggle Test", "default_portion_types": {}},
    )
    content_type_id = create_response.json()["id"]

    # Deactivate
    response = client.post(f"/admin/content-types/{content_type_id}/toggle", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert not data["is_active"]
    assert "deactivated" in data["message"]

    # Activate again
    response = client.post(f"/admin/content-types/{content_type_id}/toggle", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"]
    assert "activated" in data["message"]


def test_update_nonexistent_content_type(client, admin_headers):
    """Test updating non-existent content type"""
    response = client.patch(
        "/admin/content-types/99999", headers=admin_headers, json={"display_name": "New Name"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
