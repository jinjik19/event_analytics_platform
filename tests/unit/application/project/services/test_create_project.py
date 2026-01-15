from unittest.mock import AsyncMock

from application.project.schemas.create_dto import CreateProjectDTO
from application.project.services.create import CreateProjectService
from domain.project.types import Plan


async def test_create_project_service(mock_uow, mock_logger, test_settings):
    mock_uow.project = AsyncMock()

    service = CreateProjectService(uow=mock_uow, logger=mock_logger, settings=test_settings)
    dto = CreateProjectDTO(name="Test Project", plan=Plan.FREE)

    result = await service(dto)

    assert result.name == "Test Project"
    mock_uow.project.add.assert_called_once()
    mock_uow.commit.assert_called_once()

    assert mock_logger.info.called
