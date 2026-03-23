"""
Email notification utility.

Currently a stub — logs the notification instead of sending.
Wire up to SendGrid, AWS SES, or similar when ready.

Usage:
    from app.utils.email import send_results_email
    await send_results_email(to="user@example.com", job_id="abc-123", download_url="https://...")
"""
import logging

logger = logging.getLogger(__name__)


async def send_results_email(to: str, job_id: str, download_url: str) -> None:
    """
    Notify the user that their PDF results are ready.

    TODO: Replace with real email sending (SendGrid / AWS SES).
    """
    logger.info(
        "[EMAIL STUB] Results ready for job %s → sending to %s | download: %s",
        job_id,
        to,
        download_url,
    )
