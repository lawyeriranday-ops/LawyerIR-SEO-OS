def test_user_crud(client):
    create = client.post(
        "/api/v1/users",
        json={
            "email": "user@lawyerir.com",
            "username": "seo_user",
            "password": "password123",
        },
    )
    assert create.status_code == 201
    user = create.json()
    assert "password" not in user
    assert user["email"] == "user@lawyerir.com"

    get = client.get(f"/api/v1/users/{user['id']}")
    assert get.status_code == 200

    update = client.patch(
        f"/api/v1/users/{user['id']}",
        json={"username": "seo_admin"},
    )
    assert update.status_code == 200
    assert update.json()["username"] == "seo_admin"

    duplicate = client.post(
        "/api/v1/users",
        json={
            "email": "user@lawyerir.com",
            "username": "another",
            "password": "password123",
        },
    )
    assert duplicate.status_code == 409

    delete = client.delete(f"/api/v1/users/{user['id']}")
    assert delete.status_code == 204


def test_user_password_not_in_response(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "hidden@lawyerir.com",
            "username": "hidden_user",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "password" not in body
    assert "hashed_password" not in body
