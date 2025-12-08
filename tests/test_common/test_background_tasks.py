from unittest.mock import MagicMock, patch

import pytest

from common.background_tasks import process_animal_data, send_notification, sync_background_task


class TestBackgroundTasks:
    @pytest.mark.asyncio
    @patch("common.background_tasks.get_logger_with_trace")
    async def test_process_animal_data_success(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        await process_animal_data(trace_id="trace-123", animal_data={"id": 1})

        # Verify logs
        mock_logger.info.assert_any_call("[1] Starting animal data processing")
        mock_logger.info.assert_any_call("[2] Validating animal data")
        mock_logger.info.assert_any_call("[3] Saving animal data to database")
        mock_logger.info.assert_any_call("[4] Animal data processing completed successfully")

    @pytest.mark.asyncio
    @patch("common.background_tasks.get_logger_with_trace")
    async def test_process_animal_data_failure(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # Simulate sleep raising an exception to trigger error path
        with patch("asyncio.sleep", side_effect=ValueError("processing failed")):
            with pytest.raises(ValueError):
                await process_animal_data(trace_id="trace-123", animal_data={"id": 1})

        mock_logger.info.assert_any_call("[1] Starting animal data processing")
        mock_logger.exception.assert_any_call(
            "[E] Failed to process animal data with error: processing failed"
        )

    @pytest.mark.asyncio
    @patch("common.background_tasks.get_logger_with_trace")
    async def test_send_notification_success(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        await send_notification(trace_id="trace-123", message="Hello")

        mock_logger.info.assert_any_call("[1] Sending notification: Hello")
        mock_logger.info.assert_any_call("[2] Notification sent successfully")

    @pytest.mark.asyncio
    @patch("common.background_tasks.get_logger_with_trace")
    async def test_send_notification_failure(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with patch("asyncio.sleep", side_effect=ValueError("send failed")):
            with pytest.raises(ValueError):
                await send_notification(trace_id="trace-123", message="Hello")

        mock_logger.info.assert_any_call("[1] Sending notification: Hello")
        mock_logger.exception.assert_any_call("[E] Failed to send notification with error: send failed")

    @patch("common.background_tasks.get_logger_with_trace")
    def test_sync_background_task_success(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        sync_background_task(trace_id="trace-123", data={"id": 1})

        mock_logger.info.assert_any_call("[1] Starting sync background task")
        mock_logger.info.assert_any_call("[2] Sync task processing completed", extra={"status": "completed"})

    @patch("common.background_tasks.get_logger_with_trace")
    def test_sync_background_task_failure(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        with patch("time.sleep", side_effect=ValueError("sync failed")):
            with pytest.raises(ValueError):
                sync_background_task(trace_id="trace-123", data={"id": 1})

        mock_logger.info.assert_any_call("[1] Starting sync background task")
        mock_logger.error.assert_any_call("[E] Sync background task failed", extra={"error": "sync failed"})
