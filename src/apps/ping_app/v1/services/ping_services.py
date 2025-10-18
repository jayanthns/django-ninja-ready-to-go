import asyncio
import time
from datetime import timedelta
from typing import List

import aiohttp

from ..models import PingLog
from ..schemas import PingRequestSchema, PingResponseSchema, PingStatsSchema


class PingService:
    """Service for handling ping operations and health checks."""

    @staticmethod
    async def ping_endpoint(ping_request: PingRequestSchema) -> PingResponseSchema:
        """
        Ping an external endpoint and return response details.

        Args:
            ping_request: The ping request details

        Returns:
            PingResponseSchema: Response details including timing and status
        """
        start_time = time.time()
        response_headers = {}
        error_message = None
        status_code = 0
        success = False

        try:
            timeout = aiohttp.ClientTimeout(total=ping_request.timeout)
            headers = ping_request.headers or {}

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=ping_request.method, url=ping_request.endpoint, headers=headers
                ) as response:
                    status_code = response.status
                    response_headers = dict(response.headers)
                    success = 200 <= status_code < 400

        except asyncio.TimeoutError:
            error_message = f"Request timed out after {ping_request.timeout} seconds"
        except aiohttp.ClientError as e:
            error_message = f"Client error: {str(e)}"
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"

        response_time_ms = (time.time() - start_time) * 1000

        return PingResponseSchema(
            endpoint=ping_request.endpoint,
            method=ping_request.method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            response_headers=response_headers,
        )

    @staticmethod
    async def log_ping_result(ping_request: PingRequestSchema, ping_response: PingResponseSchema) -> PingLog:
        """
        Log ping result to database.

        Args:
            ping_request: The original ping request
            ping_response: The ping response

        Returns:
            PingLog: The created ping log entry
        """
        return await PingLog.objects.acreate(
            endpoint=ping_request.endpoint,
            method=ping_request.method,
            status_code=ping_response.status_code,
            response_time_ms=ping_response.response_time_ms,
            success=ping_response.success,
            error_message=ping_response.error_message,
            request_headers=ping_request.headers or {},
            response_headers=ping_response.response_headers,
        )

    @staticmethod
    async def get_ping_logs(limit: int = 100) -> List[PingLog]:
        """
        Get recent ping logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List[PingLog]: Recent ping logs
        """
        return [log async for log in PingLog.objects.all()[:limit]]

    @staticmethod
    async def get_ping_stats() -> PingStatsSchema:
        """
        Get ping statistics.

        Returns:
            PingStatsSchema: Ping statistics
        """
        # Get all ping logs
        all_pings = [ping async for ping in PingLog.objects.all()]

        if not all_pings:
            return PingStatsSchema(
                total_pings=0,
                successful_pings=0,
                failed_pings=0,
                average_response_time_ms=0.0,
                min_response_time_ms=0.0,
                max_response_time_ms=0.0,
                last_24h_pings=0,
                last_24h_success_rate=0.0,
            )

        # Calculate basic stats
        total_pings = len(all_pings)
        successful_pings = sum(1 for ping in all_pings if ping.success)
        failed_pings = total_pings - successful_pings

        response_times = [ping.response_time_ms for ping in all_pings]
        average_response_time_ms = sum(response_times) / len(response_times)
        min_response_time_ms = min(response_times)
        max_response_time_ms = max(response_times)

        # Calculate 24h stats
        from django.utils import timezone

        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        recent_pings = [ping for ping in all_pings if ping.created_at >= twenty_four_hours_ago]
        last_24h_pings = len(recent_pings)
        last_24h_successful = sum(1 for ping in recent_pings if ping.success)
        last_24h_success_rate = (last_24h_successful / last_24h_pings * 100) if last_24h_pings > 0 else 0.0

        return PingStatsSchema(
            total_pings=total_pings,
            successful_pings=successful_pings,
            failed_pings=failed_pings,
            average_response_time_ms=average_response_time_ms,
            min_response_time_ms=min_response_time_ms,
            max_response_time_ms=max_response_time_ms,
            last_24h_pings=last_24h_pings,
            last_24h_success_rate=last_24h_success_rate,
        )
