from unittest.mock import AsyncMock, MagicMock

from structlog import BoundLogger

from application.project.schemas.create_dto import CreateProjectDTO
from application.project.services.create import CreateProjectService
from domain.project.types import Plan
from infrastructure.config.settings import Settings


async def test_create_project_service():
    uow_mock = AsyncMock()
    uow_mock.project = AsyncMock()

    settings_mock = MagicMock(spec=Settings)
    settings_mock.app_env = "test"

    logger_mock = MagicMock(spec=BoundLogger)
    logger_mock.bind.return_value = logger_mock
    logger_mock.info = MagicMock()

    service = CreateProjectService(uow=uow_mock, logger=logger_mock, settings=settings_mock)
    dto = CreateProjectDTO(name="Test Project", plan=Plan.FREE)

    result = await service(dto)

    assert result.name == "Test Project"
    uow_mock.project.add.assert_called_once()
    uow_mock.commit.assert_called_once()

    assert logger_mock.info.called
