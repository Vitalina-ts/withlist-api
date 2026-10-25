from uuid import uuid4


def test_get_wishlist_from_postgresql(api, client, postgres_session):
    from database import get_db
    from models import User, WishList

    session = postgres_session
    owner = User(
        email=f"{uuid4().hex}@example.com",
        full_name="CI Owner",
        hashed_password="unused-for-public-read",
    )
    session.add(owner)
    session.flush()
    wishlist = WishList(title="CI wishlist", description="PostgreSQL test", user_id=owner.id)
    session.add(wishlist)
    session.commit()
    wishlist_id, owner_id = wishlist.id, owner.id
    session.expunge_all()

    def get_test_db():
        yield session

    previous = api.app.dependency_overrides.copy()
    api.app.dependency_overrides[get_db] = get_test_db
    try:
        # This public endpoint reads PostgreSQL directly and has no Redis cache.
        response = client.get(f"/wishlists/{wishlist_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == wishlist_id
        assert body["user_id"] == owner_id
        assert body["title"] == "CI wishlist"
        assert body["description"] == "PostgreSQL test"
        assert body["owner_name"] == "CI Owner"
        assert body["items_count"] == 0
    finally:
        api.app.dependency_overrides.clear()
        api.app.dependency_overrides.update(previous)


def test_real_redis(api, client):
    assert api.redis_client.ping() is True
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["redis"] == "healthy"
