import random
from dataclasses import dataclass
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import UUID4

from mealie.repos.repository_factory import AllRepositories
from mealie.schema.cookbook.cookbook import ReadCookBook, SaveCookBook
from tests import utils
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


class Routes:
    base = "/api/groups/cookbooks"

    def item(item_id: int) -> str:
        return f"{Routes.base}/{item_id}"


def get_page_data(group_id: UUID):
    name_and_slug = random_string(10)
    return {
        "name": name_and_slug,
        "slug": name_and_slug,
        "description": "",
        "position": 0,
        "categories": [],
        "group_id": str(group_id),
    }


@dataclass
class TestCookbook:
    id: UUID4
    slug: str
    name: str
    data: dict


@pytest.fixture(scope="function")
def cookbooks(database: AllRepositories, unique_user: TestUser) -> list[TestCookbook]:
    data: list[ReadCookBook] = []
    yield_data: list[TestCookbook] = []
    for _ in range(3):
        cb = database.cookbooks.create(SaveCookBook(**get_page_data(unique_user.group_id)))
        data.append(cb)
        yield_data.append(TestCookbook(id=cb.id, slug=cb.slug, name=cb.name, data=cb.dict()))

    yield yield_data

    for cb in yield_data:
        try:
            database.cookbooks.delete(cb.id)
        except Exception:
            pass


def test_create_cookbook(api_client: TestClient, unique_user: TestUser):
    page_data = get_page_data(unique_user.group_id)
    response = api_client.post(Routes.base, json=page_data, headers=unique_user.token)
    assert response.status_code == 201


def test_read_cookbook(api_client: TestClient, unique_user: TestUser, cookbooks: list[TestCookbook]):
    sample = random.choice(cookbooks)
    response = api_client.get(Routes.item(sample.id), headers=unique_user.token)
    assert response.status_code == 200

    page_data = response.json()

    assert page_data["id"] == str(sample.id)
    assert page_data["slug"] == sample.slug
    assert page_data["name"] == sample.name
    assert page_data["groupId"] == str(unique_user.group_id)


def test_update_cookbook(api_client: TestClient, unique_user: TestUser, cookbooks: list[TestCookbook]):
    cookbook = random.choice(cookbooks)

    update_data = get_page_data(unique_user.group_id)

    update_data["name"] = random_string(10)

    response = api_client.put(Routes.item(cookbook.id), json=update_data, headers=unique_user.token)
    assert response.status_code == 200

    response = api_client.get(Routes.item(cookbook.id), headers=unique_user.token)
    assert response.status_code == 200

    page_data = response.json()
    assert page_data["name"] == update_data["name"]
    assert page_data["slug"] == update_data["name"]


def test_update_cookbooks_many(api_client: TestClient, unique_user: TestUser, cookbooks: list[TestCookbook]):
    pages = [x.data for x in cookbooks]

    reverse_order = sorted(pages, key=lambda x: x["position"], reverse=True)
    for x, page in enumerate(reverse_order):
        page["position"] = x
        page["group_id"] = str(unique_user.group_id)

    response = api_client.put(Routes.base, json=utils.jsonify(reverse_order), headers=unique_user.token)
    assert response.status_code == 200

    response = api_client.get(Routes.base, headers=unique_user.token)
    assert response.status_code == 200

    known_ids = [x.id for x in cookbooks]

    server_ids = [x["id"] for x in response.json()]

    for know in known_ids:  # Hacky check, because other tests don't cleanup after themselves :(
        assert str(know) in server_ids


def test_delete_cookbook(api_client: TestClient, unique_user: TestUser, cookbooks: list[TestCookbook]):
    sample = random.choice(cookbooks)
    response = api_client.delete(Routes.item(sample.id), headers=unique_user.token)

    assert response.status_code == 200

    response = api_client.get(Routes.item(sample.slug), headers=unique_user.token)
    assert response.status_code == 404
