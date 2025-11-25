"""
Example background tasks demonstrating how to use the logger helper
without request context.
"""

import asyncio
import logging
from typing import Optional

from .logger_helper import get_logger_with_trace, log_with_trace

# Get logger for this module
logger = logging.getLogger(__name__)


async def process_animal_data(trace_id: str, correlation_id: Optional[str] = None, animal_data: dict = None):
    """
    Example background task that processes animal data.
    This demonstrates how to use the logger helper without request context.

    Args:
        trace_id: The trace ID to use for logging
        correlation_id: The correlation ID if available
        animal_data: The data to process
    """
    # Get logger adapter with trace context
    task_logger = get_logger_with_trace(
        trace_id=trace_id,
        correlation_id=correlation_id,
        logger_name="background_task",
        task_name="process_animal_data",
        animal_id=animal_data.get("id") if animal_data else None,
    )

    # Log task start
    task_logger.info("Starting animal data processing")

    try:
        # Simulate some processing
        await asyncio.sleep(0.1)

        # Update context during processing
        task_logger.update_context(processing_step="validation")
        task_logger.info("Validating animal data")

        await asyncio.sleep(0.1)

        # Update context again
        task_logger.update_context(processing_step="saving")
        task_logger.info("Saving animal data to database")

        await asyncio.sleep(0.1)

        # Log completion
        task_logger.info("Animal data processing completed successfully")

        return {"status": "success", "processed_data": animal_data}

    except Exception as e:
        # Log error with trace context
        task_logger.exception(f"Failed to process animal data with error: {str(e)}")
        raise


async def send_notification(trace_id: str, correlation_id: Optional[str] = None, message: str = None):
    """
    Example background task for sending notifications.

    Args:
        trace_id: The trace ID to use for logging
        correlation_id: The correlation ID if available
        message: The notification message
    """
    # Get logger adapter with trace context
    task_logger = get_logger_with_trace(
        trace_id=trace_id,
        correlation_id=correlation_id,
        logger_name="background_task",
        task_name="send_notification",
    )

    # Log task start
    task_logger.info(f"Sending notification: {message}")

    try:
        # Simulate sending notification
        await asyncio.sleep(0.05)

        # Log success
        task_logger.info("Notification sent successfully")

        return {"status": "sent", "message": message}

    except Exception as e:
        # Log error with trace context
        task_logger.exception(f"Failed to send notification with error: {str(e)}")
        raise


def sync_background_task(trace_id: str, correlation_id: Optional[str] = None, data: dict = None):
    """
    Example synchronous background task.

    Args:
        trace_id: The trace ID to use for logging
        correlation_id: The correlation ID if available
        data: The data to process
    """
    # For sync tasks, we can use log_with_trace directly
    log_with_trace(
        logger=logger,
        level=logging.INFO,
        msg="Starting sync background task",
        trace_id=trace_id,
        correlation_id=correlation_id,
        extra={"task_name": "sync_background_task", "data_id": data.get("id") if data else None},
    )

    try:
        # Simulate some processing
        import time

        time.sleep(0.1)

        # Log progress
        log_with_trace(
            logger=logger,
            level=logging.INFO,
            msg="Sync task processing completed",
            trace_id=trace_id,
            correlation_id=correlation_id,
            extra={"task_name": "sync_background_task", "status": "completed"},
        )

        return {"status": "success", "processed_data": data}

    except Exception as e:
        # Log error
        log_with_trace(
            logger=logger,
            level=logging.ERROR,
            msg="Sync background task failed",
            trace_id=trace_id,
            correlation_id=correlation_id,
            extra={"task_name": "sync_background_task", "error": str(e)},
        )
        raise


# Example usage in views or services:
async def example_usage_in_view(request):
    """
    Example of how to use background tasks from a view.
    """
    # Use request.logger directly (just like request.trace_id)
    request.logger.info("Starting background tasks")

    # Start background tasks with the same trace_id and correlation_id
    tasks = [
        process_animal_data(
            trace_id=request.trace_id,
            correlation_id=getattr(request, "correlation_id", None),
            animal_data={"id": 1, "name": "Fluffy"},
        ),
        send_notification(
            trace_id=request.trace_id,
            correlation_id=getattr(request, "correlation_id", None),
            message="Animal processed successfully",
        ),
    ]

    # Wait for tasks to complete
    results = await asyncio.gather(*tasks)

    # Log completion
    request.logger.info("Background tasks completed")

    return results
