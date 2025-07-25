import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models

# Создаем тестовую БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Или :memory: для in-memory
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

# Подмена зависимостей
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Заменяем зависимость в приложении
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Вызывается один раз для создания схемы
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

# Тест создания задачи
def test_create_todo():
    response = client.post("/todos", json={"title": "Проверка", "description": "Описание"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Проверка"
    assert "id" in data

# Тест получения всех задач
def test_read_todos():
    response = client.get("/todos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Тест получения одной задачи
def test_read_single_todo():
    response = client.get("/todos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

# Тест обновления задачи
def test_update_todo():
    response = client.put("/todos/1", json={"title": "Обновлено", "description": "Новое описание"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Обновлено"

# Тест удаления задачи
def test_delete_todo():
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json() == {"ok": True}

# Тест ошибки при запросе несуществующей задачи
def test_not_found_todo():
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "ToDo not found"
